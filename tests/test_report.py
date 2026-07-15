from datetime import datetime
from pathlib import Path

from src.models import AnalysisResult, DataQualityReport, OverviewMetrics, ReportModel
from src.report import HtmlReportGenerator, PdfReportGenerator


def test_html_report_embeds_charts_and_chinese() -> None:
    report = ReportModel(
        quality=DataQualityReport(raw_rows=1, valid_rows=1),
        analysis=AnalysisResult(
            overview=OverviewMetrics(valid_orders=1, total_sales=100),
            sales_by_region=[{"region": "华东", "sales": 100, "orders": 1}],
        ),
        anomalies=[],
        insight="华东销售表现稳定。",
        insight_is_fallback=True,
        generated_at=datetime(2026, 7, 15, 12, 0, 0),
    )
    html = HtmlReportGenerator(Path("templates/report.html")).generate(
        report,
        {"daily_sales": "<div>plotly-test</div>"},
    )
    assert "AI 数据洞察报告" in html
    assert "华东销售表现稳定" in html
    assert "plotly-test" in html
    assert "洞察来源" not in html


def test_pdf_report_has_pdf_signature_and_report_content() -> None:
    report = ReportModel(
        quality=DataQualityReport(raw_rows=2, valid_rows=2),
        analysis=AnalysisResult(
            overview=OverviewMetrics(valid_orders=2, total_sales=300),
            daily_sales=[
                {"order_date": "2026-07-14", "sales": 100},
                {"order_date": "2026-07-15", "sales": 200},
            ],
            top_products=[
                {"product": "耳机", "sales": 200, "quantity": 2, "orders": 1},
                {"product": "鼠标", "sales": 100, "quantity": 1, "orders": 1},
            ],
            sales_by_region=[{"region": "华东", "sales": 300, "orders": 2}],
        ),
        anomalies=[],
        insight="华东销售表现稳定。",
        generated_at=datetime(2026, 7, 15, 12, 0, 0),
    )

    pdf = PdfReportGenerator().generate(report)

    assert pdf.startswith(b"%PDF-")
    assert len(pdf) > 1_000
