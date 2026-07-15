"""Domain exceptions surfaced to the UI without Python tracebacks."""


class DataReportError(Exception):
    """Base class for expected application errors."""


class EmptyFileError(DataReportError):
    """Raised when an uploaded CSV contains no bytes or rows."""


class UnsupportedFileError(DataReportError):
    """Raised when an upload is not an accepted CSV file."""


class FileTooLargeError(DataReportError):
    """Raised when an upload exceeds the configured size limit."""


class CsvParseError(DataReportError):
    """Raised when CSV bytes cannot be decoded or parsed."""


class MissingRequiredColumnsError(DataReportError):
    """Raised when required business columns are absent."""

    def __init__(self, columns: set[str]) -> None:
        self.columns = sorted(columns)
        super().__init__(f"缺少必需字段：{', '.join(self.columns)}")
