"""Custom exception hierarchy for DataPrepToolkit.

All toolkit-specific exceptions inherit from :class:`DataPrepError`,
making it easy for callers to catch every toolkit error with a single
``except`` clause while still allowing granular handling.

Example::

    from datapreptoolkit.exceptions import DataPrepError, LoadError

    try:
        toolkit.load("missing.csv")
    except LoadError as exc:
        print(f"Could not load file: {exc}")
    except DataPrepError:
        print("Something else went wrong inside the toolkit.")
"""

from __future__ import annotations

from pathlib import Path


class DataPrepError(Exception):
    """Base exception for every error raised by DataPrepToolkit.

    Attributes:
        message: Human-readable description of the error.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


# ---------------------------------------------------------------------------
# Loading errors
# ---------------------------------------------------------------------------


class LoadError(DataPrepError):
    """Raised when a dataset cannot be loaded from disk or memory."""

    def __init__(self, message: str, source: str | Path | None = None) -> None:
        self.source = source
        detail = f" [source={source}]" if source else ""
        super().__init__(f"{message}{detail}")


class FileFormatError(LoadError):
    """Raised when the file extension is not supported (not ``.csv``)."""

    def __init__(self, path: str | Path) -> None:
        super().__init__(
            f"Unsupported file format. Expected .csv, got: {path}",
            source=path,
        )


class EmptyDatasetError(LoadError):
    """Raised when the loaded dataset contains zero rows or zero columns."""

    def __init__(self, source: str | Path | None = None) -> None:
        super().__init__("Dataset is empty (zero rows or zero columns).", source=source)


# ---------------------------------------------------------------------------
# Cleaning errors
# ---------------------------------------------------------------------------


class CleaningError(DataPrepError):
    """Raised when a data-cleaning operation fails."""


class InvalidColumnError(CleaningError):
    """Raised when a referenced column does not exist in the DataFrame."""

    def __init__(self, column: str, available: list[str] | None = None) -> None:
        self.column = column
        self.available = available or []
        hint = ""
        if self.available:
            close = [c for c in self.available if c.lower() == column.lower()]
            if close:
                hint = f"  Did you mean '{close[0]}'?"
        super().__init__(f"Column '{column}' not found in DataFrame.{hint}")


class IncompatibleDataError(CleaningError):
    """Raised when data fails an expected constraint (e.g. negative prices)."""


# ---------------------------------------------------------------------------
# Validation errors
# ---------------------------------------------------------------------------


class ValidationError(DataPrepError):
    """Raised when data validation checks fail."""


class QualityThresholdError(ValidationError):
    """Raised when the data-quality score falls below a caller-set threshold."""

    def __init__(self, score: float, threshold: float) -> None:
        self.score = score
        self.threshold = threshold
        super().__init__(
            f"Data quality score {score:.2%} is below threshold {threshold:.2%}."
        )


# ---------------------------------------------------------------------------
# Reporting errors
# ---------------------------------------------------------------------------


class ReportError(DataPrepError):
    """Raised when report generation fails."""


# ---------------------------------------------------------------------------
# Configuration errors
# ---------------------------------------------------------------------------


class ConfigError(DataPrepError):
    """Raised when an invalid configuration is provided."""
