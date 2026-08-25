"""Internal utils — delegates shared functions to automation_core.

DPT-specific helpers are defined locally.
"""

from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

import pandas as pd
from automation_core.utils import format_bytes, identify_column_types

logger = logging.getLogger("datapreptoolkit")

__all__ = [
    "identify_column_types",
    "format_bytes",
    "setup_logging",
    "copy_dataframe",
    "validate_columns",
    "ensure_directory",
    "memory_usage_mb",
    "find_datetime_columns",
]


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------


def setup_logging(level: str = "INFO") -> None:
    """Configure the package-level logger.

    Args:
        level: A Python log-level name (``"DEBUG"``, ``"INFO"``, etc.).
    """
    numeric = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.setLevel(numeric)
    if not logger.handlers:
        logger.addHandler(handler)


# ---------------------------------------------------------------------------
# DataFrame helpers
# ---------------------------------------------------------------------------


def copy_dataframe(df: pd.DataFrame, deep: bool = True) -> pd.DataFrame:
    """Return a copy of *df* so originals are never mutated.

    Args:
        df: The source DataFrame.
        deep: If ``True`` (default), perform a deep copy.

    Returns:
        A (optionally deep) copy of the input DataFrame.
    """
    logger.debug("Copying DataFrame (deep=%s, shape=%s)", deep, df.shape)
    return df.copy(deep=deep)


def validate_columns(df: pd.DataFrame, columns: list[str]) -> None:
    """Raise :class:`InvalidColumnError` if any *columns* are missing.

    Args:
        df: The DataFrame to check against.
        columns: Column names that must exist.

    Raises:
        InvalidColumnError: If any of the requested columns are absent.
    """
    from datapreptoolkit._internal.exceptions import InvalidColumnError

    missing = [c for c in columns if c not in df.columns]
    if missing:
        logger.error("Missing columns: %s", missing)
        raise InvalidColumnError(missing[0], available=list(df.columns))


def ensure_directory(path: Path) -> Path:
    """Create *path* (and parents) if it does not already exist.

    Args:
        path: Directory to create.

    Returns:
        The same ``Path`` for chaining.
    """
    path.mkdir(parents=True, exist_ok=True)
    logger.debug("Ensured directory exists: %s", path)
    return path


def memory_usage_mb(df: pd.DataFrame) -> float:
    """Return the total memory usage of *df* in megabytes.

    Args:
        df: The DataFrame to measure.

    Returns:
        Approximate memory usage in MB.
    """
    return float(df.memory_usage(deep=True).sum() / (1024**2))


def find_datetime_columns(
    df: pd.DataFrame,
    candidates: list[str] | None = None,
) -> list[str]:
    """Detect columns that look like datetimes.

    Args:
        df: The DataFrame to inspect.
        candidates: Restrict detection to these columns.  ``None`` means
            check every ``object`` column.

    Returns:
        A list of column names that were successfully parsed as datetimes.
    """
    search = candidates or [
        c
        for c in df.columns
        if pd.api.types.is_object_dtype(df[c])
        or isinstance(df[c].dtype, pd.StringDtype)
    ]
    parsed: list[str] = []
    for col in search:
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", category=UserWarning)
                parsed_s = pd.to_datetime(df[col], errors="coerce")
            nat_ratio = (
                parsed_s.isnull().sum() / len(df[col])
                if len(df[col]) > 0
                else 0.0
            )
            if nat_ratio > 0.5:
                continue
            parsed.append(col)
        except (ValueError, TypeError, OverflowError):
            continue
    return parsed
