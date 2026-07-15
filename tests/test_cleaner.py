from pathlib import Path

from src.cleaner import DataCleaner
from src.loader import CsvLoader


FIXTURES = Path(__file__).parent / "fixtures"


def _clean(name: str):
    with (FIXTURES / name).open("rb") as file_obj:
        return DataCleaner().clean(CsvLoader().load(file_obj, filename=name))


def test_clean_data_remains_valid() -> None:
    result = _clean("clean_orders.csv")
    assert result.quality_report.raw_rows == 6
    assert result.quality_report.valid_rows == 6
    assert result.quality_report.partial_rows == 0
    assert result.quality_report.rejected_rows == 0


def test_dirty_data_is_classified_and_traceable() -> None:
    result = _clean("dirty_orders.csv")
    assert result.quality_report.raw_rows == 10
    assert result.quality_report.valid_rows == 1
    assert result.quality_report.partial_rows == 1
    assert result.quality_report.rejected_rows == 8
    assert result.quality_report.duplicate_rows == 1
    assert result.clean_df.loc[result.clean_df["order_id"] == "D001", "region"].iloc[0] == "未知地区"
    assert result.clean_df.loc[result.clean_df["order_id"] == "D001", "discount"].iloc[0] == 0
    assert "invalid_date" in result.partial_df.iloc[0]["quality_issues"]
    assert result.rejected_df["rejection_reasons"].str.len().gt(0).all()


def test_cleaner_does_not_mutate_input() -> None:
    with (FIXTURES / "clean_orders.csv").open("rb") as file_obj:
        raw = CsvLoader().load(file_obj, filename="clean_orders.csv")
    original = raw.copy(deep=True)
    DataCleaner().clean(raw)
    assert raw.equals(original)


def test_fractional_quantity_is_rejected_instead_of_truncated() -> None:
    result = _clean("decimal_quantity.csv")
    assert result.clean_df.empty
    assert result.quality_report.rejected_rows == 1
    assert "non_integer_quantity" in result.rejected_df.iloc[0]["rejection_reasons"]
