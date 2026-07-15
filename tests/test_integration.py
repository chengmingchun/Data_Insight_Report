from pathlib import Path

from src.insight import TemplateInsightProvider
from src.orchestrator import AnalysisOptions, AnalysisOrchestrator


FIXTURES = Path(__file__).parent / "fixtures"


def test_dirty_csv_runs_end_to_end_without_external_service() -> None:
    with (FIXTURES / "dirty_orders.csv").open("rb") as file_obj:
        result = AnalysisOrchestrator(insight_provider=TemplateInsightProvider()).run(
            file_obj,
            filename="dirty_orders.csv",
            options=AnalysisOptions(top_n=5),
        )
    assert result.report.quality.raw_rows == 10
    assert result.report.analysis.overview.valid_orders == 2
    assert result.report.analysis.overview.total_sales == 500
    assert result.report.insight
    assert "<html" in result.html.lower()
    assert len(result.figures) == 3
    assert len(result.rejected_df) == 8


def test_repeated_analysis_is_deterministic() -> None:
    orchestrator = AnalysisOrchestrator(insight_provider=TemplateInsightProvider())
    content = (FIXTURES / "clean_orders.csv").read_bytes()
    from io import BytesIO

    first = orchestrator.run(BytesIO(content), filename="clean_orders.csv")
    second = orchestrator.run(BytesIO(content), filename="clean_orders.csv")
    assert first.report.analysis == second.report.analysis
    assert first.report.quality == second.report.quality
