from pathlib import Path

import pytest

from src.analyzer import DataAnalyzer
from src.cleaner import DataCleaner
from src.loader import CsvLoader


FIXTURES = Path(__file__).parent / "fixtures"


def _analyze(name: str, top_n: int = 10):
    with (FIXTURES / name).open("rb") as file_obj:
        cleaned = DataCleaner().clean(CsvLoader().load(file_obj, filename=name))
    return DataAnalyzer(top_n=top_n).analyze(cleaned.clean_df)


def test_core_metrics_follow_documented_scope() -> None:
    result = _analyze("clean_orders.csv")
    assert result.overview.valid_orders == 6
    assert result.overview.total_sales == pytest.approx(1780.0)
    assert result.overview.average_order_value == pytest.approx(445.0)
    assert result.overview.total_quantity == 6
    assert result.overview.refunded_orders == 1
    assert result.overview.refund_rate == pytest.approx(1 / 6)


def test_top_n_and_pivot_are_ordered() -> None:
    result = _analyze("clean_orders.csv", top_n=2)
    assert [row["product"] for row in result.top_products] == ["显示器", "键盘"]
    assert len(result.top_products) == 2
    assert result.region_category_matrix


def test_zero_completed_orders_returns_zero_average() -> None:
    result = _analyze("all_refunded.csv")
    assert result.overview.total_sales == 0
    assert result.overview.average_order_value == 0
    assert result.overview.refund_rate == 1
