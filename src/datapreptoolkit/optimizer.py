"""Datatype and memory optimisation.

Provides functions that down-cast numeric types and convert low-cardinality
object columns to ``category`` dtype, reducing the DataFrame's memory
footprint without losing information.

Every function returns a **new** DataFrame and an :class:`OptimizationResult`
so callers can inspect exactly what changed.

Example::

    from datapreptoolkit.optimizer import optimise_memory

    optimised, result = optimise_memory(df)
    print(result.savings_human)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from datapreptoolkit.config import ToolkitConfig
from datapreptoolkit.utils import copy_dataframe, format_bytes

logger = logging.getLogger("datapreptoolkit")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ColumnOptimization:
    """Record of a single column's type change.

    Attributes:
        column: Column name.
        dtype_before: Original dtype string.
        dtype_after: New dtype string.
        memory_before: Memory used by this column before (bytes).
        memory_after: Memory used by this column after (bytes).
    """

    column: str
    dtype_before: str
    dtype_after: str
    memory_before: int
    memory_after: int


@dataclass
class OptimizationResult:
    """Summary of all optimisation operations performed.

    Attributes:
        memory_before: Total memory before (bytes).
        memory_after: Total memory after (bytes).
        memory_before_human: Human-readable memory before.
        memory_after_human: Human-readable memory after.
        savings_bytes: Absolute saving in bytes.
        savings_mb: Savings in megabytes.
        savings_pct: Percentage reduction (0-100).
        savings_human: Human-readable savings string.
        column_changes: Per-column :class:`ColumnOptimization` records.
        messages: Human-readable log.
    """

    memory_before: int = 0
    memory_after: int = 0
    memory_before_human: str = "0 B"
    memory_after_human: str = "0 B"
    savings_bytes: int = 0
    savings_mb: float = 0.0
    savings_pct: float = 0.0
    savings_human: str = "0.00 B"
    column_changes: list[ColumnOptimization] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _downcast_integer(series: pd.Series) -> pd.Series:
    """Down-cast an integer Series to the smallest feasible int dtype.

    Tries ``int8``, ``int16``, ``int32`` in order.  If the range doesn't
    fit, the series is returned unchanged.

    Args:
        series: A Series with an integer dtype.

    Returns:
        The down-cast Series (or the original if no smaller dtype fits).
    """
    col_min = int(series.min())
    col_max = int(series.max())

    for dtype in (np.int8, np.int16, np.int32):
        info = np.iinfo(dtype)
        if info.min <= col_min and col_max <= info.max:
            return series.astype(dtype)

    return series


def _downcast_float(series: pd.Series) -> pd.Series:
    """Attempt to down-cast a float Series to ``float32``.

    If the precision loss is acceptable (no NaN/inf introduced), the
    smaller dtype is used.

    Args:
        series: A Series with a float dtype.

    Returns:
        The down-cast Series or the original.
    """
    try:
        converted = series.astype(np.float32)
        # Verify no meaningful precision loss
        if series.equals(converted) or converted.equals(series):
            return converted
    except (ValueError, OverflowError, TypeError):
        pass
    return series


def _optimise_numeric(series: pd.Series) -> tuple[pd.Series, str, str]:
    """Down-cast a single numeric Series.

    Returns:
        ``(new_series, dtype_before, dtype_after)``
    """
    dtype_before = str(series.dtype)

    if pd.api.types.is_integer_dtype(series):
        new = _downcast_integer(series)
    elif pd.api.types.is_float_dtype(series):
        new = _downcast_float(series)
    else:
        return series, dtype_before, dtype_before

    return new, dtype_before, str(new.dtype)


def _optimise_object_to_category(
    series: pd.Series,
    cardinality_threshold: float = 0.5,
) -> pd.Series:
    """Convert an object Series to ``category`` if cardinality is low.

    Args:
        series: The object-dtype Series.
        cardinality_threshold: Maximum unique-ratio (unique / length)
            to justify conversion.  Default 0.5.

    Returns:
        The converted Series or the original.
    """
    n = len(series)
    if n == 0:
        return series
    unique_ratio = series.nunique() / n
    if unique_ratio <= cardinality_threshold:
        return series.astype("category")
    return series


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def optimise_datatypes(
    df: pd.DataFrame,
    category_threshold: float = 0.5,
    config: ToolkitConfig | None = None,
) -> tuple[pd.DataFrame, OptimizationResult]:
    """Down-cast numerics and convert low-cardinality objects to category.

    This function **never modifies** the original DataFrame.

    Args:
        df: The DataFrame to optimise.
        category_threshold: Maximum unique-ratio for an object column to be
            converted to ``category``.  Default ``0.5``.
        config: Toolkit configuration.

    Returns:
        A tuple of ``(optimised_df, OptimizationResult)``.
    """
    cleaned = copy_dataframe(df)
    mem_before = int(cleaned.memory_usage(deep=True).sum())
    result = OptimizationResult(
        memory_before=mem_before,
        memory_before_human=format_bytes(mem_before),
    )

    for col in cleaned.columns:
        mem_col_before = int(cleaned[col].memory_usage(deep=True))
        series = cleaned[col]
        dtype_before = str(series.dtype)

        if pd.api.types.is_numeric_dtype(series):
            new_series, db, da = _optimise_numeric(series)
            if da != db:
                cleaned[col] = new_series
                mem_col_after = int(new_series.memory_usage(deep=True))
                result.column_changes.append(
                    ColumnOptimization(col, db, da, mem_col_before, mem_col_after)
                )
                result.messages.append(f"Column '{col}': {db} -> {da}")
        elif pd.api.types.is_object_dtype(series) or isinstance(
            series.dtype, pd.StringDtype
        ):
            new_series = _optimise_object_to_category(series, category_threshold)
            if str(new_series.dtype) != dtype_before:
                cleaned[col] = new_series
                mem_col_after = int(new_series.memory_usage(deep=True))
                result.column_changes.append(
                    ColumnOptimization(
                        col,
                        dtype_before,
                        str(new_series.dtype),
                        mem_col_before,
                        mem_col_after,
                    )
                )
                result.messages.append(f"Column '{col}': {dtype_before} -> category")

    mem_after = int(cleaned.memory_usage(deep=True).sum())
    result.memory_after = mem_after
    result.memory_after_human = format_bytes(mem_after)
    result.savings_bytes = mem_before - mem_after
    result.savings_mb = round(result.savings_bytes / (1024 * 1024), 2)
    result.savings_pct = (
        round(result.savings_bytes / mem_before * 100, 2) if mem_before else 0.0
    )
    result.savings_human = format_bytes(result.savings_bytes)

    logger.info(
        "Optimisation: %s -> %s (saved %s, %.1f%%)",
        format_bytes(mem_before),
        format_bytes(mem_after),
        result.savings_human,
        result.savings_pct,
    )
    return cleaned, result


def optimise_memory(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> tuple[pd.DataFrame, OptimizationResult]:
    """High-level memory optimisation controlled by *config*.

    Runs :func:`optimise_datatypes` if ``config.optimise_memory`` is True.
    Otherwise returns the original DataFrame unchanged.

    Args:
        df: The DataFrame to optimise.
        config: Toolkit configuration.

    Returns:
        A tuple of ``(df_or_optimised, OptimizationResult)``.
    """
    cfg = config or ToolkitConfig()

    if not cfg.optimise_memory:
        mem = int(df.memory_usage(deep=True).sum())
        result = OptimizationResult(
            memory_before=mem,
            memory_after=mem,
            memory_before_human=format_bytes(mem),
            memory_after_human=format_bytes(mem),
            messages=["Memory optimisation disabled in config."],
        )
        return df, result

    return optimise_datatypes(df, config=cfg)
