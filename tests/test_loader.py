from io import BytesIO
from pathlib import Path

import pytest

from src.exceptions import (
    CsvParseError,
    EmptyFileError,
    FileTooLargeError,
    MissingRequiredColumnsError,
    UnsupportedFileError,
)
from src.loader import CsvLoader


FIXTURES = Path(__file__).parent / "fixtures"


def test_loads_utf8_and_normalizes_columns() -> None:
    loader = CsvLoader()
    with (FIXTURES / "clean_orders.csv").open("rb") as file_obj:
        frame = loader.load(file_obj, filename="clean_orders.csv")
    assert len(frame) == 6
    assert "order_id" in frame.columns


def test_loads_utf8_bom() -> None:
    body = (FIXTURES / "clean_orders.csv").read_bytes()
    frame = CsvLoader().load(BytesIO(b"\xef\xbb\xbf" + body), filename="bom.csv")
    assert frame.iloc[0]["order_id"] == "C001"


def test_rejects_empty_file() -> None:
    with pytest.raises(EmptyFileError):
        CsvLoader().load(BytesIO(b""), filename="empty.csv")


def test_rejects_missing_required_columns() -> None:
    with (FIXTURES / "missing_columns.csv").open("rb") as file_obj:
        with pytest.raises(MissingRequiredColumnsError) as error:
            CsvLoader().load(file_obj, filename="missing_columns.csv")
    assert "unit_price" in str(error.value)


def test_rejects_non_csv_extension() -> None:
    with pytest.raises(UnsupportedFileError):
        CsvLoader().load(BytesIO(b"a,b\n1,2"), filename="orders.txt")


def test_rejects_non_utf8_bytes() -> None:
    with pytest.raises(CsvParseError):
        CsvLoader().load(BytesIO(b"\xff\xfe\x00\x00"), filename="orders.csv")


def test_rejects_file_over_limit() -> None:
    with pytest.raises(FileTooLargeError):
        CsvLoader(max_upload_mb=1).load(BytesIO(b"x" * (1024 * 1024 + 1)), filename="large.csv")
