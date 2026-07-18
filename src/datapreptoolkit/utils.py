"""Shared utility helpers for DataPrepToolkit.

Every function here is **stateless** and **pure** — they take inputs,
return outputs, and have no side effects beyond optional logging.
Other modules import from here to stay DRY.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from datapreptoolkit.exceptions import InvalidColumnError

if TYPE_CHECKING:
    pass

logger = logging.getLogger("datapreptoolkit")


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


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------


def format_bytes(size_bytes: float) -> str:
    """Convert a byte count into a human-readable string.

    Examples::

        >>> format_bytes(1536)
        '1.50 KB'
        >>> format_bytes(2_097_152)
        '2.00 MB'

    Args:
        size_bytes: Number of bytes.

    Returns:
        A formatted string such as ``"1.50 KB"``.
    """
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(size_bytes) < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024  # type: ignore[assignment]
    return f"{size_bytes:.2f} PB"


def memory_usage_mb(df: pd.DataFrame) -> float:
    """Return the total memory usage of *df* in megabytes.

    Args:
        df: The DataFrame to measure.

    Returns:
        Approximate memory usage in MB.
    """
    return float(df.memory_usage(deep=True).sum() / (1024**2))


# ---------------------------------------------------------------------------
# Column classification helpers
# ---------------------------------------------------------------------------


def identify_column_types(df: pd.DataFrame) -> dict[str, list[str]]:
    """Classify columns by their semantic type.

    Args:
        df: The DataFrame to classify.

    Returns:
        A dict with keys ``"numeric"``, ``"categorical"``, ``"datetime"``,
        ``"boolean"``, and ``"other"``, each mapping to a list of column names.
    """
    result: dict[str, list[str]] = {
        "numeric": [],
        "categorical": [],
        "datetime": [],
        "boolean": [],
        "other": [],
    }
    for col in df.columns:
        dtype = df[col].dtype
        if pd.api.types.is_bool_dtype(dtype):
            result["boolean"].append(col)
        elif pd.api.types.is_numeric_dtype(dtype):
            result["numeric"].append(col)
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            result["datetime"].append(col)
        elif pd.api.types.is_object_dtype(dtype) or isinstance(
            dtype, (pd.CategoricalDtype, pd.StringDtype)
        ):
            result["categorical"].append(col)
        else:
            result["other"].append(col)
    return result


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
            pd.to_datetime(df[col], errors="coerce")
            # If >50% became NaT, it's probably not a datetime column
            nat_ratio = pd.to_datetime(df[col], errors="coerce").isnull().sum() / len(
                df[col]
            )
            if nat_ratio > 0.5:
                continue
            parsed.append(col)
        except (ValueError, TypeError, OverflowError):
            continue
    return parsed
