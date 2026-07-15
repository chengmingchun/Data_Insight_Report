"""Application facade that coordinates the fixed analysis workflow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Any

import pandas as pd
import plotly.graph_objects as go

from src.analyzer import DataAnalyzer
from src.anomaly import IqrAnomalyDetector
from src.charts import ChartBuilder
from src.cleaner import DataCleaner
from src.insight import InsightProvider, InsightService, TemplateInsightProvider, build_insight_payload
from src.loader import CsvLoader
from src.models import ReportModel
from src.report import HtmlReportGenerator, PdfReportGenerator


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class AnalysisOptions:
    top_n: int = 10
    max_upload_mb: int = 20


@dataclass
class PipelineResult:
    report: ReportModel
    figures: dict[str, go.Figure]
    html: str
    pdf: bytes
    clean_df: pd.DataFrame
    partial_df: pd.DataFrame
    rejected_df: pd.DataFrame
    anomaly_df: pd.DataFrame


class AnalysisOrchestrator:
    def __init__(self, insight_provider: InsightProvider | None = None) -> None:
        self.insight_provider = insight_provider or TemplateInsightProvider()

    def run(
        self,
        file_obj: BinaryIO,
        *,
        filename: str,
        options: AnalysisOptions | None = None,
    ) -> PipelineResult:
        options = options or AnalysisOptions()
        raw = CsvLoader(max_upload_mb=options.max_upload_mb).load(file_obj, filename=filename)
        cleaning = DataCleaner().clean(raw)
        analysis = DataAnalyzer(top_n=options.top_n).analyze(cleaning.clean_df)
        iqr = IqrAnomalyDetector().detect(cleaning.clean_df)
        anomalies = self._rule_anomalies(cleaning.rejected_df, cleaning.partial_df) + iqr.records
        analysis.overview.anomaly_count = len(anomalies)

        payload = build_insight_payload(analysis, anomalies)
        insight = InsightService(self.insight_provider).generate(payload)
        report = ReportModel(
            quality=cleaning.quality_report,
            analysis=analysis,
            anomalies=anomalies,
            insight=insight.text,
            insight_is_fallback=insight.is_fallback,
            insight_provider=insight.provider,
            generated_at=datetime.now(),
        )
        figures = ChartBuilder().build_all(analysis)
        chart_html: dict[str, str] = {}
        for index, (name, figure) in enumerate(figures.items()):
            chart_html[name] = figure.to_html(
                full_html=False,
                include_plotlyjs=True if index == 0 else False,
                config={"displaylogo": False, "responsive": True},
            )
        html = HtmlReportGenerator(ROOT / "templates" / "report.html").generate(report, chart_html)
        pdf = PdfReportGenerator().generate(report)
        return PipelineResult(
            report=report,
            figures=figures,
            html=html,
            pdf=pdf,
            clean_df=cleaning.clean_df,
            partial_df=cleaning.partial_df,
            rejected_df=cleaning.rejected_df,
            anomaly_df=pd.DataFrame(anomalies),
        )

    @staticmethod
    def _rule_anomalies(rejected: pd.DataFrame, partial: pd.DataFrame) -> list[dict[str, Any]]:
        records: list[dict[str, Any]] = []
        for frame, reason_column in (
            (rejected, "rejection_reasons"),
            (partial, "quality_issues"),
        ):
            for row in frame.to_dict("records"):
                records.append(
                    {
                        "order_id": row.get("order_id"),
                        "source_row": row.get("source_row"),
                        "sales_amount": float(row.get("sales_amount", 0) or 0),
                        "anomaly_reason": ", ".join(row.get(reason_column, [])),
                        "anomaly_type": "rule",
                    }
                )
        return records
