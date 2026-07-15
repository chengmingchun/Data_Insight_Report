from pathlib import Path

from src.analyzer import DataAnalyzer
from src.charts import ChartBuilder
from src.cleaner import DataCleaner
from src.loader import CsvLoader


FIXTURES = Path(__file__).parent / "fixtures"


def test_builds_three_named_figures() -> None:
    with (FIXTURES / "clean_orders.csv").open("rb") as file_obj:
        cleaned = DataCleaner().clean(CsvLoader().load(file_obj, filename="clean_orders.csv"))
    figures = ChartBuilder().build_all(DataAnalyzer().analyze(cleaned.clean_df))
    assert set(figures) == {"daily_sales", "top_products", "region_sales"}
    assert all(figure.layout.title.text for figure in figures.values())
