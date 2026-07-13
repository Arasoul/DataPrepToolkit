"""Analytical functions for missing values, numeric/categorical columns,
and feature summaries.

Every function in this module is **read-only** — the input DataFrame is
never modified.  All results are returned as typed dataclasses so callers
can use them programmatically or pass them to the reporter.

Example::

    from datapreptoolkit.analyzer import (
        analyze_missing_values,
        analyze_numeric_columns,
    )

    missing = analyze_missing_values(df)
    numeric = analyze_numeric_columns(df)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from datapreptoolkit.config import ToolkitConfig

logger = logging.getLogger("datapreptoolkit")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnMissingInfo:
    """Missing-value statistics for a single column.

    Attributes:
        column: Column name.
        null_count: Number of null values.
        null_pct: Percentage of nulls (0–100).
        non_null_count: Number of non-null values.
        has_missing: Convenience flag.
    """

    column: str
    null_count: int
    null_pct: float
    non_null_count: int
    has_missing: bool


@dataclass(frozen=True)
class MissingValueAnalysis:
    """Complete missing-value analysis for a DataFrame.

    Attributes:
        total_cells: Total number of cells.
        total_missing: Total null cells.
        overall_missing_pct: Global missing percentage.
        columns: Per-column :class:`ColumnMissingInfo` (only for columns
            that actually have missing values).
        completely_empty_columns: Columns that are 100 % null.
        complete_columns: Columns with zero nulls.
        recommended_actions: Suggested treatment per column —
            ``"drop_column"`` (>60 %), ``"impute_median"`` (numeric),
            ``"impute_mode"`` (categorical), or ``"drop_rows"``.
    """

    total_cells: int
    total_missing: int
    overall_missing_pct: float
    columns: dict[str, ColumnMissingInfo] = field(default_factory=dict)
    completely_empty_columns: list[str] = field(default_factory=list)
    complete_columns: list[str] = field(default_factory=list)
    recommended_actions: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class NumericColumnStats:
    """Descriptive statistics for one numeric column.

    Attributes:
        column: Column name.
        count: Non-null count.
        mean, median, std, min, max: Standard statistics.
        q25, q75: 25th and 75th percentiles.
        iqr: Inter-quartile range.
        skewness: Distribution skewness.
        kurtosis: Distribution excess kurtosis.
        zero_count: Number of zero values.
        negative_count: Number of negative values.
        outlier_count_iqr: Outliers detected via 1.5 × IQR.
        outlier_pct_iqr: Percentage of IQR outliers.
    """

    column: str
    count: int
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float
    iqr: float
    skewness: float
    kurtosis: float
    zero_count: int
    negative_count: int
    outlier_count_iqr: int
    outlier_pct_iqr: float


@dataclass(frozen=True)
class NumericAnalysis:
    """Aggregate numeric analysis for the entire DataFrame.

    Attributes:
        columns: Per-column statistics.
        highly_skewed: Column names with |skewness| > 1.
        columns_with_outliers: Column names with at least one IQR outlier.
    """

    columns: dict[str, NumericColumnStats] = field(default_factory=dict)
    highly_skewed: list[str] = field(default_factory=list)
    columns_with_outliers: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CategoricalColumnStats:
    """Statistics for one categorical column.

    Attributes:
        column: Column name.
        count: Non-null count.
        unique_count: Distinct values.
        mode: Most frequent value.
        mode_freq: Frequency of the mode.
        top_values: Up to 10 ``(value, count)`` pairs sorted by frequency.
        cardinality_ratio: ``unique / count``.
    """

    column: str
    count: int
    unique_count: int
    mode: Any
    mode_freq: int
    top_values: tuple[tuple[Any, int], ...] = field(default_factory=tuple)
    cardinality_ratio: float = 0.0


@dataclass(frozen=True)
class CategoricalAnalysis:
    """Aggregate categorical analysis for the entire DataFrame.

    Attributes:
        columns: Per-column statistics.
        high_cardinality_columns: Columns whose cardinality ratio
            exceeds the configured threshold.
    """

    columns: dict[str, CategoricalColumnStats] = field(default_factory=dict)
    high_cardinality_columns: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class FeatureSummary:
    """Compact summary for a single feature (column).

    Attributes:
        column: Column name.
        dtype: Pandas dtype string.
        semantic_type: ``"numeric"``, ``"categorical"``, ``"datetime"``,
            ``"boolean"``, or ``"other"``.
        non_null: Non-null count.
        null_count: Null count.
        null_pct: Null percentage.
        unique_count: Unique value count.
        unique_ratio: Unique / total rows.
        summary: A type-specific dict of key statistics.
    """

    column: str
    dtype: str
    semantic_type: str
    non_null: int
    null_count: int
    null_pct: float
    unique_count: int
    unique_ratio: float
    summary: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Public API: Missing Value Analysis
# ---------------------------------------------------------------------------

def analyze_missing_values(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> MissingValueAnalysis:
    """Analyse missing values across the entire DataFrame.

    The function never modifies *df*.

    Args:
        df: The DataFrame to analyse.
        config: Toolkit configuration.  Controls the drop-column
            threshold (>60 %) for recommendation logic.

    Returns:
        A :class:`MissingValueAnalysis` with per-column details and
        recommended actions.
    """
    n_rows, n_cols = df.shape
    total_cells = n_rows * n_cols
    total_missing = int(df.isnull().sum().sum())

    col_infos: dict[str, ColumnMissingInfo] = {}
    empty_cols: list[str] = []
    complete_cols: list[str] = []
    recommended: dict[str, str] = {}

    for col in df.columns:
        nc = int(df[col].isnull().sum())
        pct = round(nc / n_rows * 100, 2) if n_rows > 0 else 0.0
        info = ColumnMissingInfo(
            column=col,
            null_count=nc,
            null_pct=pct,
            non_null_count=n_rows - nc,
            has_missing=nc > 0,
        )
        col_infos[col] = info

        if pct == 100.0:
            empty_cols.append(col)
            recommended[col] = "drop_column"
        elif pct == 0.0:
            complete_cols.append(col)
        elif pct > 60.0:
            recommended[col] = "drop_column"
        elif pd.api.types.is_numeric_dtype(df[col]):
            recommended[col] = "impute_median"
        else:
            recommended[col] = "impute_mode"

    result = MissingValueAnalysis(
        total_cells=total_cells,
        total_missing=total_missing,
        overall_missing_pct=(
            round(total_missing / total_cells * 100, 2)
            if total_cells else 0.0
        ),
        columns=col_infos,
        completely_empty_columns=empty_cols,
        complete_columns=complete_cols,
        recommended_actions=recommended,
    )

    logger.info(
        "Missing values: %d / %d cells (%.2f%%)",
        total_missing,
        total_cells,
        result.overall_missing_pct,
    )
    return result


# ---------------------------------------------------------------------------
# Public API: Numeric Analysis
# ---------------------------------------------------------------------------

def analyze_numeric_columns(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> NumericAnalysis:
    """Compute descriptive statistics for every numeric column.

    The function never modifies *df*.

    Args:
        df: The DataFrame to analyse.
        config: Toolkit configuration (currently unused but reserved
            for future threshold tuning).

    Returns:
        A :class:`NumericAnalysis` with per-column statistics and
        lists of skewed / outlier columns.
    """
    cfg = config or ToolkitConfig()
    num_cols = df.select_dtypes(include="number").columns.tolist()

    col_stats: dict[str, NumericColumnStats] = {}
    skewed: list[str] = []
    with_outliers: list[str] = []

    for col in num_cols:
        s = df[col].dropna()
        if s.empty:
            continue

        count = int(s.count())
        mean = float(s.mean())
        median = float(s.median())
        std = float(s.std()) if count > 1 else 0.0
        mn = float(s.min())
        mx = float(s.max())
        q25 = float(s.quantile(0.25))
        q75 = float(s.quantile(0.75))
        iqr_val = q75 - q25
        skew = float(s.skew())  # type: ignore[arg-type]
        kurt = float(s.kurtosis())  # type: ignore[arg-type]
        zeros = int((s == 0).sum())
        negatives = int((s < 0).sum())

        lower = q25 - cfg.iqr_multiplier * iqr_val
        upper = q75 + cfg.iqr_multiplier * iqr_val
        outliers = int(((s < lower) | (s > upper)).sum())
        outlier_pct = round(outliers / count * 100, 2) if count else 0.0

        cs = NumericColumnStats(
            column=col,
            count=count,
            mean=round(mean, 4),
            median=round(median, 4),
            std=round(std, 4),
            min=round(mn, 4),
            max=round(mx, 4),
            q25=round(q25, 4),
            q75=round(q75, 4),
            iqr=round(iqr_val, 4),
            skewness=round(skew, 4),
            kurtosis=round(kurt, 4),
            zero_count=zeros,
            negative_count=negatives,
            outlier_count_iqr=outliers,
            outlier_pct_iqr=outlier_pct,
        )
        col_stats[col] = cs

        if abs(skew) > 1.0:
            skewed.append(col)
        if outliers > 0:
            with_outliers.append(col)

    result = NumericAnalysis(
        columns=col_stats,
        highly_skewed=skewed,
        columns_with_outliers=with_outliers,
    )

    logger.info(
        "Numeric analysis: %d columns, %d skewed, %d with outliers",
        len(col_stats),
        len(skewed),
        len(with_outliers),
    )
    return result


# ---------------------------------------------------------------------------
# Public API: Categorical Analysis
# ---------------------------------------------------------------------------

def analyze_categorical_columns(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> CategoricalAnalysis:
    """Compute frequency statistics for every categorical column.

    The function never modifies *df*.

    Args:
        df: The DataFrame to analyse.
        config: Toolkit configuration.  Controls the high-cardinality
            threshold.

    Returns:
        A :class:`CategoricalAnalysis` with per-column statistics.
    """
    cfg = config or ToolkitConfig()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    col_stats: dict[str, CategoricalColumnStats] = {}
    high_card: list[str] = []

    for col in cat_cols:
        s = df[col].dropna()
        count = int(s.count())
        unique = int(s.nunique())
        mode_val = s.mode().iloc[0] if not s.mode().empty else None
        mode_freq = int(s.value_counts().iloc[0]) if not s.value_counts().empty else 0
        top = tuple(
            (val, int(cnt))
            for val, cnt in s.value_counts().head(10).items()
        )
        ratio = unique / count if count else 0.0

        cs = CategoricalColumnStats(
            column=col,
            count=count,
            unique_count=unique,
            mode=mode_val,
            mode_freq=mode_freq,
            top_values=top,
            cardinality_ratio=round(ratio, 4),
        )
        col_stats[col] = cs

        if ratio >= cfg.high_cardinality_threshold and unique > 1:
            high_card.append(col)

    result = CategoricalAnalysis(
        columns=col_stats,
        high_cardinality_columns=high_card,
    )

    logger.info(
        "Categorical analysis: %d columns, %d high-cardinality",
        len(col_stats),
        len(high_card),
    )
    return result


# ---------------------------------------------------------------------------
# Public API: Feature Summaries
# ---------------------------------------------------------------------------

def generate_feature_summaries(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> list[FeatureSummary]:
    """Generate a compact per-column summary for the entire DataFrame.

    The summary adapts to the column's semantic type: numeric columns
    get mean/median/std, categorical columns get mode/cardinality, etc.

    The function never modifies *df*.

    Args:
        df: The DataFrame to summarise.
        config: Toolkit configuration.

    Returns:
        An ordered list of :class:`FeatureSummary` objects.
    """
    n_rows = df.shape[0]
    summaries: list[FeatureSummary] = []

    for col in df.columns:
        series = df[col]
        nc = int(series.isnull().sum())
        non_null = n_rows - nc
        null_pct = round(nc / n_rows * 100, 2) if n_rows else 0.0
        unique = int(series.nunique())
        ratio = round(unique / n_rows, 4) if n_rows else 0.0

        # Semantic type
        if pd.api.types.is_bool_dtype(series):
            sem = "boolean"
        elif pd.api.types.is_numeric_dtype(series):
            sem = "numeric"
        elif pd.api.types.is_datetime64_any_dtype(series):
            sem = "datetime"
        elif pd.api.types.is_object_dtype(series) \
                or isinstance(series.dtype, pd.CategoricalDtype):
            sem = "categorical"
        else:
            sem = "other"

        # Type-specific summary dict
        s_data = series.dropna()
        detail: dict[str, Any] = {}

        if sem == "numeric" and not s_data.empty:
            detail = {
                "mean": round(float(s_data.mean()), 4),
                "median": round(float(s_data.median()), 4),
                "std": round(float(s_data.std()), 4) if len(s_data) > 1 else 0.0,
                "min": round(float(s_data.min()), 4),
                "max": round(float(s_data.max()), 4),
            }
        elif sem == "categorical" and not s_data.empty:
            detail = {
                "mode": s_data.mode().iloc[0] if not s_data.mode().empty else None,
                "unique_count": unique,
                "top_5": [
                    {"value": v, "count": int(c)}
                    for v, c in s_data.value_counts().head(5).items()
                ],
            }
        elif sem == "datetime" and not s_data.empty:
            detail = {
                "min": str(s_data.min()),
                "max": str(s_data.max()),
            }
        elif sem == "bool":
            detail = {
                "true_count": int(s_data.sum()) if s_data.dtype != object else 0,
                "false_count": int((~s_data).sum()) if s_data.dtype != object else 0,
            }

        summaries.append(
            FeatureSummary(
                column=col,
                dtype=str(series.dtype),
                semantic_type=sem,
                non_null=non_null,
                null_count=nc,
                null_pct=null_pct,
                unique_count=unique,
                unique_ratio=ratio,
                summary=detail,
            )
        )

    logger.info("Generated feature summaries for %d columns", len(summaries))
    return summaries
