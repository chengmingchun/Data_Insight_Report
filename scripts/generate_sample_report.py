"""Generate the committed sample report using the offline fallback."""

from pathlib import Path

from src.insight import TemplateInsightProvider
from src.orchestrator import AnalysisOrchestrator


ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    source = ROOT / "data" / "sample_orders.csv"
    html_target = ROOT / "outputs" / "sample_report.html"
    pdf_target = ROOT / "outputs" / "sample_report.pdf"
    with source.open("rb") as file_obj:
        result = AnalysisOrchestrator(TemplateInsightProvider()).run(
            file_obj,
            filename=source.name,
        )
    html_target.write_text(result.html, encoding="utf-8")
    pdf_target.write_bytes(result.pdf)


if __name__ == "__main__":
    main()
