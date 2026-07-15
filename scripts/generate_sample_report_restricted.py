"""Generate the sample artifact when optional Plotly packages are unavailable."""

from __future__ import annotations

import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path

import matplotlib.pyplot as plt

from src.analyzer import DataAnalyzer
from src.anomaly import IqrAnomalyDetector
from src.cleaner import DataCleaner
from src.insight import InsightService, TemplateInsightProvider, build_insight_payload
from src.loader import CsvLoader
from src.models import ReportModel
from src.report import HtmlReportGenerator


ROOT = Path(__file__).resolve().parent.parent


def image_html(figure) -> str:
    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(figure)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f'<img alt="chart" style="width:100%;height:auto" src="data:image/png;base64,{encoded}">'


def build_charts(analysis) -> dict[str, str]:
    plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
    plt.rcParams["axes.unicode_minus"] = False

    daily_figure, daily_axis = plt.subplots(figsize=(9, 3.4))
    daily_axis.plot(
        [row["date"] for row in analysis.daily_sales],
        [row["sales"] for row in analysis.daily_sales],
        marker="o",
        color="#167d76",
        linewidth=2.2,
    )
    daily_axis.set_title("Daily Sales Trend")
    daily_axis.set_ylabel("Sales (CNY)")
    daily_axis.tick_params(axis="x", rotation=35)
    daily_axis.grid(axis="y", alpha=0.22)

    products = list(reversed(analysis.top_products))
    product_figure, product_axis = plt.subplots(figsize=(6, 3.8))
    product_axis.barh(
        [row["product"] for row in products],
        [row["sales"] for row in products],
        color="#e0953e",
    )
    product_axis.set_title("Top Products by Sales")
    product_axis.set_xlabel("Sales (CNY)")

    regions = analysis.sales_by_region
    region_figure, region_axis = plt.subplots(figsize=(6, 3.8))
    region_axis.bar(
        [row["region"] for row in regions],
        [row["sales"] for row in regions],
        color="#167d76",
    )
    region_axis.set_title("Sales by Region")
    region_axis.set_ylabel("Sales (CNY)")

    return {
        "daily_sales": image_html(daily_figure),
        "top_products": image_html(product_figure),
        "region_sales": image_html(region_figure),
    }


def main() -> None:
    source = ROOT / "data" / "sample_orders.csv"
    with source.open("rb") as file_obj:
        raw = CsvLoader().load(file_obj, filename=source.name)
    cleaning = DataCleaner().clean(raw)
    analysis = DataAnalyzer().analyze(cleaning.clean_df)
    iqr = IqrAnomalyDetector().detect(cleaning.clean_df)

    anomalies = list(iqr.records)
    for frame, column in (
        (cleaning.rejected_df, "rejection_reasons"),
        (cleaning.partial_df, "quality_issues"),
    ):
        for row in frame.to_dict("records"):
            anomalies.append(
                {
                    "order_id": row.get("order_id"),
                    "source_row": row.get("source_row"),
                    "sales_amount": float(row.get("sales_amount", 0) or 0),
                    "anomaly_reason": ", ".join(row.get(column, [])),
                    "anomaly_type": "rule",
                }
            )
    analysis.overview.anomaly_count = len(anomalies)
    insight = InsightService(TemplateInsightProvider()).generate(
        build_insight_payload(analysis, anomalies)
    )
    report = ReportModel(
        quality=cleaning.quality_report,
        analysis=analysis,
        anomalies=anomalies,
        insight=insight.text,
        insight_is_fallback=True,
        insight_provider="template",
        generated_at=datetime.now(),
    )
    html = HtmlReportGenerator(ROOT / "templates" / "report.html").generate(
        report,
        build_charts(analysis),
    )
    (ROOT / "outputs" / "sample_report.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    main()
