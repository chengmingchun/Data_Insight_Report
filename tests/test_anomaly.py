from pathlib import Path

from src.anomaly import IqrAnomalyDetector
from src.cleaner import DataCleaner
from src.loader import CsvLoader


FIXTURES = Path(__file__).parent / "fixtures"


def _clean(name: str):
    with (FIXTURES / name).open("rb") as file_obj:
        return DataCleaner().clean(CsvLoader().load(file_obj, filename=name)).clean_df


def test_iqr_detects_extreme_completed_order() -> None:
    result = IqrAnomalyDetector().detect(_clean("iqr_outlier.csv"))
    assert len(result.records) == 1
    assert result.records[0]["order_id"] == "I006"
    assert "IQR" in result.records[0]["anomaly_reason"]


def test_iqr_skips_insufficient_sample() -> None:
    result = IqrAnomalyDetector().detect(_clean("single_order.csv"))
    assert result.records == []
    assert result.lower_bound is None
    assert result.upper_bound is None
