"""CSV loading, size checks, decoding and schema validation."""

from __future__ import annotations

from io import BytesIO, StringIO
import logging
from typing import BinaryIO

import pandas as pd

from src.exceptions import (
    CsvParseError,
    EmptyFileError,
    FileTooLargeError,
    MissingRequiredColumnsError,
    UnsupportedFileError,
)


LOGGER = logging.getLogger(__name__)

REQUIRED_COLUMNS = {
    "order_id",
    "order_date",
    "product",
    "quantity",
    "unit_price",
    "status",
}
OPTIONAL_COLUMNS = {"region", "category", "discount"}


class CsvLoader:
    def __init__(self, max_upload_mb: int = 20) -> None:
        self.max_bytes = max_upload_mb * 1024 * 1024

    def load(self, file_obj: BinaryIO, filename: str | None = None) -> pd.DataFrame:
        if filename and not filename.lower().endswith(".csv"):
            raise UnsupportedFileError("仅支持 .csv 文件")

        raw = file_obj.read()
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        if not raw:
            raise EmptyFileError("CSV 文件为空")
        if len(raw) > self.max_bytes:
            raise FileTooLargeError(f"CSV 文件超过 {self.max_bytes // (1024 * 1024)} MB")

        try:
            text = raw.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise CsvParseError("CSV 必须使用 UTF-8 或 UTF-8-SIG 编码") from exc

        try:
            frame = pd.read_csv(StringIO(text), dtype=str, keep_default_na=True)
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
            raise CsvParseError("CSV 格式无法解析") from exc

        if frame.empty:
            raise EmptyFileError("CSV 没有数据记录")

        frame.columns = [str(column).strip().lower() for column in frame.columns]
        if len(set(frame.columns)) != len(frame.columns):
            raise CsvParseError("CSV 包含重复列名")

        missing = REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise MissingRequiredColumnsError(missing)

        for column in sorted(OPTIONAL_COLUMNS - set(frame.columns)):
            frame[column] = pd.NA

        LOGGER.info("Loaded CSV rows=%s columns=%s", len(frame), len(frame.columns))
        return frame

    def load_bytes(self, content: bytes, filename: str = "upload.csv") -> pd.DataFrame:
        return self.load(BytesIO(content), filename=filename)
