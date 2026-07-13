"""Data loading and dataset profiling.

Provides functions to load data from CSV files or existing DataFrames,
and to generate a comprehensive :class:`DatasetProfile` that captures
shape, types, missing values, duplicates, cardinality, and potential
column roles (IDs, targets, leakage).

Example::

    from datapreptoolkit.loader import load_csv, profile_dataset

    df = load_csv("data/sales.csv")
    profile = profile_dataset(df)
    print(profile.shape)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from datapreptoolkit.config import ToolkitConfig
from datapreptoolkit.exceptions import (
    EmptyDatasetError,
    FileFormatError,
    LoadError,
)
from datapreptoolkit.utils import (
    copy_dataframe,
    format_bytes,
)

logger = logging.getLogger("datapreptoolkit")


# ---------------------------------------------------------------------------
# Dataclass: ColumnProfile
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnProfile:
    """Profile for a single column.

    Attributes:
        name: Column name.
        dtype: Pandas dtype string.
        non_null: Count of non-null values.
        null_count: Count of null values.
        null_pct: Percentage of null values (0–100).
        unique_count: Number of distinct values.
        unique_ratio: Unique values divided by total rows (0–1).
        is_constant: Whether ≥99 % of values are identical.
        is_high_cardinality: Whether the unique ratio exceeds the threshold.
        is_potential_id: Whether the column looks like an identifier.
        sample_values: Up to 5 sample non-null values.
    """

    name: str
    dtype: str
    non_null: int
    null_count: int
    null_pct: float
    unique_count: int
    unique_ratio: float
    is_constant: bool
    is_high_cardinality: bool
    is_potential_id: bool
    sample_values: tuple[Any, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Dataclass: DatasetProfile
# ---------------------------------------------------------------------------

@dataclass
class DatasetProfile:
    """Comprehensive profile of a dataset.

    Attributes:
        shape: ``(rows, columns)`` tuple.
        memory_bytes: Total memory usage in bytes.
        memory_human: Human-readable memory string.
        columns: Ordered mapping of column name → :class:`ColumnProfile`.
        numeric_columns: Column names with a numeric dtype.
        categorical_columns: Column names with object or categorical dtype.
        datetime_columns: Column names with a datetime dtype.
        boolean_columns: Column names with a boolean dtype.
        other_columns: Column names with any other dtype.
        constant_columns: Columns flagged as constant.
        high_cardinality_columns: Columns with very high unique ratio.
        potential_id_columns: Columns that look like identifiers.
        potential_leakage_columns: Columns whose name or behavior suggests
            data leakage (e.g. post-event fields).
        missing_columns: Columns that contain at least one null value.
        duplicate_rows: Number of completely duplicate rows.
        duplicate_ratio: Fraction of duplicate rows (0-1).
        total_missing: Total number of missing cells across the dataset.
        total_cells: Total number of cells (rows x columns).
        overall_quality_score: A 0-100 quality score (100 = perfect).
    """

    shape: tuple[int, int]
    memory_bytes: int
    memory_human: str
    columns: dict[str, ColumnProfile] = field(default_factory=dict)
    numeric_columns: list[str] = field(default_factory=list)
    categorical_columns: list[str] = field(default_factory=list)
    datetime_columns: list[str] = field(default_factory=list)
    boolean_columns: list[str] = field(default_factory=list)
    other_columns: list[str] = field(default_factory=list)
    constant_columns: list[str] = field(default_factory=list)
    high_cardinality_columns: list[str] = field(default_factory=list)
    potential_id_columns: list[str] = field(default_factory=list)
    potential_leakage_columns: list[str] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)
    duplicate_rows: int = 0
    duplicate_ratio: float = 0.0
    total_missing: int = 0
    total_cells: int = 0
    overall_quality_score: float = 0.0


# ---------------------------------------------------------------------------
# Public API: Loading
# ---------------------------------------------------------------------------

def load_csv(
    filepath: str | Path,
    encoding: str = "utf-8",
    config: ToolkitConfig | None = None,
    **pd_kwargs: Any,
) -> pd.DataFrame:
    """Load a CSV file into a DataFrame.

    The function validates the path and file extension before delegating
    to ``pandas.read_csv``.  If the file is empty (zero rows) an
    :class:`EmptyDatasetError` is raised.

    Args:
        filepath: Path to the ``.csv`` file.
        encoding: File encoding.  Default ``"utf-8"``.
        config: Optional toolkit config (reserved for future use).
        **pd_kwargs: Extra keyword arguments forwarded to ``pd.read_csv``.

    Returns:
        A ``pandas.DataFrame`` containing the loaded data.

    Raises:
        FileNotFoundError: If *filepath* does not exist.
        FileFormatError: If *filepath* is not a ``.csv`` file.
        LoadError: If reading fails for any other reason.
        EmptyDatasetError: If the file contains zero rows.
    """
    path = Path(filepath)

    # -- Existence check --
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # -- Extension check --
    if path.suffix.lower() != ".csv":
        raise FileFormatError(path)

    # -- Read --
    logger.info("Loading CSV: %s", path)
    try:
        df = pd.read_csv(path, encoding=encoding, **pd_kwargs)
    except UnicodeDecodeError as exc:
        raise LoadError(
            f"Encoding error — try a different encoding. Last error: {exc}",
            source=path,
        ) from exc
    except pd.errors.ParserError as exc:
        raise LoadError(f"CSV parse error: {exc}", source=path) from exc
    except Exception as exc:
        raise LoadError(f"Unexpected error loading CSV: {exc}", source=path) from exc

    # -- Empty check --
    if df.empty or df.shape[1] == 0:
        raise EmptyDatasetError(source=path)

    logger.info(
        "Loaded %d rows × %d columns from %s",
        df.shape[0],
        df.shape[1],
        path.name,
    )
    return pd.DataFrame(df)


def load_dataframe(
    df: pd.DataFrame,
    deep: bool = True,
    config: ToolkitConfig | None = None,
) -> pd.DataFrame:
    """Validate and optionally copy an existing DataFrame.

    Args:
        df: The DataFrame to load.
        deep: If ``True`` (default), return a deep copy so the caller's
            original is never mutated.
        config: Optional toolkit config (reserved for future use).

    Returns:
        A validated (and optionally copied) DataFrame.

    Raises:
        TypeError: If *df* is not a ``pandas.DataFrame``.
        EmptyDatasetError: If *df* has zero rows or zero columns.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(
            f"Expected a pandas DataFrame, got {type(df).__name__}"
        )

    if df.empty or df.shape[1] == 0:
        raise EmptyDatasetError()

    logger.info("Loading DataFrame: %d rows × %d columns", *df.shape)
    return copy_dataframe(df, deep=deep)


# ---------------------------------------------------------------------------
# Public API: Profiling
# ---------------------------------------------------------------------------

def profile_dataset(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> DatasetProfile:
    """Generate a comprehensive profile of a DataFrame.

    This is a **read-only** operation — the input DataFrame is never
    modified.

    Args:
        df: The DataFrame to profile.
        config: Toolkit configuration.  Controls thresholds for
            constant columns, high-cardinality detection, ID detection,
            and target correlation.

    Returns:
        A :class:`DatasetProfile` containing every metric and flag
        requested in the project specification.
    """
    cfg = config or ToolkitConfig()
    n_rows, n_cols = df.shape
    logger.info("Profiling dataset: %d rows × %d columns", n_rows, n_cols)

    total_cells = n_rows * n_cols
    total_missing = int(df.isnull().sum().sum())
    duplicate_rows = int(df.duplicated().sum())

    # -- Per-column profiling --
    col_profiles: dict[str, ColumnProfile] = {}
    numeric_cols: list[str] = []
    categorical_cols: list[str] = []
    datetime_cols: list[str] = []
    boolean_cols: list[str] = []
    other_cols: list[str] = []
    missing_cols: list[str] = []
    constant_cols: list[str] = []
    high_card_cols: list[str] = []
    potential_id_cols: list[str] = []

    for col in df.columns:
        series = df[col]
        null_count = int(series.isnull().sum())
        non_null = int(n_rows - null_count)
        unique = series.nunique()
        unique_ratio = unique / n_rows if n_rows > 0 else 0.0
        null_pct = (null_count / n_rows * 100) if n_rows > 0 else 0.0

        is_constant = unique_ratio <= (1.0 - cfg.constant_threshold)
        is_high_card = (
            unique_ratio >= cfg.high_cardinality_threshold
            and unique > 1
        )
        is_potential_id = (
            unique_ratio >= cfg.id_column_threshold and unique > 1
        )

        if null_count > 0:
            missing_cols.append(col)
        if is_constant:
            constant_cols.append(col)
        if is_high_card:
            high_card_cols.append(col)
        if is_potential_id:
            potential_id_cols.append(col)

        # Semantic classification
        dtype_str = str(series.dtype)
        sample = tuple(
            v for v in series.dropna().head(5).tolist()
        )

        cp = ColumnProfile(
            name=col,
            dtype=dtype_str,
            non_null=non_null,
            null_count=null_count,
            null_pct=round(null_pct, 2),
            unique_count=unique,
            unique_ratio=round(unique_ratio, 4),
            is_constant=is_constant,
            is_high_cardinality=is_high_card,
            is_potential_id=is_potential_id,
            sample_values=sample,
        )
        col_profiles[col] = cp

        # Type bucket
        if pd.api.types.is_bool_dtype(series):
            boolean_cols.append(col)
        elif pd.api.types.is_numeric_dtype(series):
            numeric_cols.append(col)
        elif pd.api.types.is_datetime64_any_dtype(series):
            datetime_cols.append(col)
        elif pd.api.types.is_object_dtype(series) or isinstance(
            series.dtype, (pd.CategoricalDtype, pd.StringDtype)
        ):
            categorical_cols.append(col)
        else:
            other_cols.append(col)

    # -- Potential leakage columns (heuristic: name-based) --
    leakage_keywords = {
        "date_sale", "sale_date", "signup_date", "order_approved",
        "delivered", "delivery_date", "review_date", "answer_timestamp",
    }
    potential_leakage_cols: list[str] = []
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in leakage_keywords):
            potential_leakage_cols.append(col)

    # -- Quality score (using configurable weights) --
    weights = cfg.quality_weights
    score = 100.0
    if total_cells > 0:
        score -= (total_missing / total_cells) * weights["missing"]
    if n_rows > 0:
        score -= (duplicate_rows / n_rows) * weights["duplicate"]
    score -= len(constant_cols) * weights["constant"]
    score -= len(high_card_cols) * weights["high_cardinality"]
    score = max(0.0, min(100.0, score))

    mem_bytes = df.memory_usage(deep=True).sum()

    profile = DatasetProfile(
        shape=(n_rows, n_cols),
        memory_bytes=int(mem_bytes),
        memory_human=format_bytes(mem_bytes),
        columns=col_profiles,
        numeric_columns=numeric_cols,
        categorical_columns=categorical_cols,
        datetime_columns=datetime_cols,
        boolean_columns=boolean_cols,
        other_columns=other_cols,
        constant_columns=constant_cols,
        high_cardinality_columns=high_card_cols,
        potential_id_columns=potential_id_cols,
        potential_leakage_columns=potential_leakage_cols,
        missing_columns=missing_cols,
        duplicate_rows=duplicate_rows,
        duplicate_ratio=round(duplicate_rows / n_rows, 4) if n_rows > 0 else 0.0,
        total_missing=total_missing,
        total_cells=total_cells,
        overall_quality_score=round(score, 2),
    )

    logger.info("Quality score: %.2f / 100", profile.overall_quality_score)
    return profile
