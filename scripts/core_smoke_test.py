"""Dependency-light verification for restricted build environments.

The full acceptance command remains pytest. This script exercises the deterministic
core when optional UI/LLM packages cannot be installed.
"""

from datetime import datetime
from pathlib import Path

from src.analyzer import DataAnalyzer
from src.anomaly import IqrAnomalyDetector
from src.cleaner import DataCleaner
from src.insight import (
    DeepSeekInsightProvider,
    InsightService,
    TemplateInsightProvider,
    build_insight_payload,
)
from src.loader import CsvLoader
from src.models import ReportModel
from src.report import HtmlReportGenerator


ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"


def load_and_clean(name: str):
    with (FIXTURES / name).open("rb") as file_obj:
        return DataCleaner().clean(CsvLoader().load(file_obj, filename=name))


def main() -> None:
    clean = load_and_clean("clean_orders.csv")
    assert clean.quality_report.valid_rows == 6
    analysis = DataAnalyzer(top_n=2).analyze(clean.clean_df)
    assert analysis.overview.total_sales == 1780.0
    assert analysis.overview.average_order_value == 445.0
    assert [row["product"] for row in analysis.top_products] == ["显示器", "键盘"]

    dirty = load_and_clean("dirty_orders.csv")
    assert dirty.quality_report.valid_rows == 1
    assert dirty.quality_report.partial_rows == 1
    assert dirty.quality_report.rejected_rows == 8

    decimal_quantity = load_and_clean("decimal_quantity.csv")
    assert decimal_quantity.clean_df.empty
    assert "non_integer_quantity" in decimal_quantity.rejected_df.iloc[0]["rejection_reasons"]

    outlier = load_and_clean("iqr_outlier.csv")
    anomaly = IqrAnomalyDetector().detect(outlier.clean_df)
    assert [row["order_id"] for row in anomaly.records] == ["I006"]

    payload = build_insight_payload(analysis, anomaly.records)
    insight = InsightService(TemplateInsightProvider()).generate(payload)
    assert insight.is_fallback is True
    assert "1,780.00" in insight.text

    class FakeCompletions:
        def create(self, **kwargs):
            assert "order_id" not in kwargs["messages"][1]["content"]
            message = type("Message", (), {"content": "销售额为 1,780.00 元。"})()
            choice = type("Choice", (), {"message": message})()
            return type("Response", (), {"choices": [choice]})()

    fake_client = type(
        "Client",
        (),
        {"chat": type("Chat", (), {"completions": FakeCompletions()})()},
    )()
    deepseek = InsightService(
        DeepSeekInsightProvider(api_key="test-only", client=fake_client)
    ).generate(payload)
    assert deepseek.is_fallback is False
    assert deepseek.provider == "deepseek"

    class HallucinatingProvider:
        provider_name = "mock"

        def generate(self, _payload):
            return "销售额为 999999 元。"

    guarded = InsightService(HallucinatingProvider()).generate(payload)
    assert guarded.is_fallback is True
    assert "999999" not in guarded.text

    report = ReportModel(
        quality=clean.quality_report,
        analysis=analysis,
        anomalies=anomaly.records,
        insight=insight.text,
        insight_is_fallback=True,
        generated_at=datetime(2026, 7, 15, 12, 0, 0),
    )
    html = HtmlReportGenerator(ROOT / "templates" / "report.html").generate(
        report,
        {"daily_sales": "<div>chart</div>"},
    )
    assert "AI 数据洞察报告" in html
    assert "<div>chart</div>" in html

    print("core-smoke-ok")


if __name__ == "__main__":
    main()
