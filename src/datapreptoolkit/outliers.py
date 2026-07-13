"""Outlier detection using IQR and Z-score methods.

Every function is **read-only** — the input DataFrame is never modified.
Results are returned as typed dataclasses so callers can inspect outlier
indices, bounds, and counts programmatically.

Example::

    from datapreptoolkit.outliers import detect_outliers

    result = detect_outliers(df, method="iqr")
    print(result.total_outliers)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from datapreptoolkit.config import ToolkitConfig, ZScoreMethod

logger = logging.getLogger("datapreptoolkit")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnOutlierInfo:
    """Outlier statistics for a single numeric column.

    Attributes:
        column: Column name.
        method: Detection method used (``"iqr"`` or ``"zscore"``).
        total_values: Number of non-null values examined.
        outlier_count: Number of detected outliers.
        outlier_pct: Percentage of outliers (0–100).
        outlier_indices: Row indices of outlier rows.
        lower_bound: Lower threshold below which values are outliers.
        upper_bound: Upper threshold above which values are outliers.
        min_outlier: Minimum outlier value (or ``NaN`` if none).
        max_outlier: Maximum outlier value (or ``NaN`` if none).
    """

    column: str
    method: str
    total_values: int
    outlier_count: int
    outlier_pct: float
    outlier_indices: tuple[int, ...] = field(default_factory=tuple)
    lower_bound: float = 0.0
    upper_bound: float = 0.0
    min_outlier: float = float("nan")
    max_outlier: float = float("nan")


@dataclass
class OutlierDetection:
    """Aggregate outlier detection result for the entire DataFrame.

    Attributes:
        method: Detection method used.
        columns: Per-column :class:`ColumnOutlierInfo` (only numeric columns).
        columns_with_outliers: Column names that have at least one outlier.
        total_outliers: Sum of outlier counts across all columns.
        outlier_mask: A boolean DataFrame (same shape as the input) where
            ``True`` marks a cell that is an outlier in its column.
    """

    method: str
    columns: dict[str, ColumnOutlierInfo] = field(default_factory=dict)
    columns_with_outliers: list[str] = field(default_factory=list)
    total_outliers: int = 0
    outlier_mask: pd.DataFrame = field(default_factory=pd.DataFrame)


# ---------------------------------------------------------------------------
# IQR detection
# ---------------------------------------------------------------------------

def detect_outliers_iqr(
    df: pd.DataFrame,
    multiplier: float | None = None,
    config: ToolkitConfig | None = None,
) -> OutlierDetection:
    """Detect outliers using the Interquartile Range (IQR) method.

    A value is an outlier if it falls below ``Q1 - m*IQR`` or above
    ``Q3 + m*IQR`` where *m* is the *multiplier* (default 1.5).

    Args:
        df: The DataFrame to scan.
        multiplier: IQR multiplier override.  ``None`` uses
            ``config.iqr_multiplier``.
        config: Toolkit configuration.

    Returns:
        An :class:`OutlierDetection` with per-column details.
    """
    cfg = config or ToolkitConfig()
    m = multiplier if multiplier is not None else cfg.iqr_multiplier

    num_df = df.select_dtypes(include="number")
    col_infos: dict[str, ColumnOutlierInfo] = {}
    mask_parts: list[pd.DataFrame] = []
    flagged: list[str] = []
    total = 0

    for col in num_df.columns:
        series = num_df[col].dropna()
        if series.empty:
            continue

        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - m * iqr
        upper = q3 + m * iqr

        mask = (series < lower) | (series > upper)
        outlier_idx = tuple(series.index[mask].tolist())
        n_out = len(outlier_idx)
        pct = round(n_out / len(series) * 100, 2) if len(series) else 0.0

        info = ColumnOutlierInfo(
            column=col,
            method="iqr",
            total_values=len(series),
            outlier_count=n_out,
            outlier_pct=pct,
            outlier_indices=outlier_idx,
            lower_bound=round(lower, 4),
            upper_bound=round(upper, 4),
            min_outlier=float(series.loc[mask].min()) if n_out else float("nan"),
            max_outlier=float(series.loc[mask].max()) if n_out else float("nan"),
        )
        col_infos[col] = info
        total += n_out

        if n_out > 0:
            flagged.append(col)
            col_mask = pd.Series(False, index=df.index)
            col_mask.loc[mask.index[mask]] = True
            mask_parts.append(col_mask.to_frame(col))

    outlier_mask = pd.concat(mask_parts, axis=1) if mask_parts else pd.DataFrame()

    result = OutlierDetection(
        method="iqr",
        columns=col_infos,
        columns_with_outliers=flagged,
        total_outliers=total,
        outlier_mask=outlier_mask,
    )

    logger.info(
        "IQR outlier detection: %d columns scanned, %d total outliers",
        len(col_infos),
        total,
    )
    return result


# ---------------------------------------------------------------------------
# Z-score detection
# ---------------------------------------------------------------------------

def detect_outliers_zscore(
    df: pd.DataFrame,
    threshold: float | None = None,
    method: ZScoreMethod | None = None,
    config: ToolkitConfig | None = None,
) -> OutlierDetection:
    """Detect outliers using the Z-score method.

    Supports both the standard Z-score (mean-based) and the modified
    Z-score (median-based, more robust to outliers themselves).

    A value is an outlier if its absolute Z-score exceeds *threshold*
    (default 3.0).

    Args:
        df: The DataFrame to scan.
        threshold: Z-score threshold override.  ``None`` uses
            ``config.zscore_threshold``.
        method: ``ZScoreMethod.STANDARD`` or ``ZScoreMethod.MODIFIED``.
            ``None`` uses ``config.zscore_method``.
        config: Toolkit configuration.

    Returns:
        An :class:`OutlierDetection` with per-column details.
    """
    cfg = config or ToolkitConfig()
    t = threshold if threshold is not None else cfg.zscore_threshold
    m = method if method is not None else cfg.zscore_method

    num_df = df.select_dtypes(include="number")
    col_infos: dict[str, ColumnOutlierInfo] = {}
    mask_parts: list[pd.DataFrame] = []
    flagged: list[str] = []
    total = 0

    for col in num_df.columns:
        series = num_df[col].dropna()
        if series.empty:
            continue

        if m == ZScoreMethod.MODIFIED:
            med = float(series.median())
            mad = float(np.median(np.abs(series - med)))
            if mad == 0:
                z_scores = pd.Series(0.0, index=series.index)
            else:
                z_scores = 0.6745 * (series - med) / mad
        else:
            mean = float(series.mean())
            std = float(series.std())
            if std == 0:
                z_scores = pd.Series(0.0, index=series.index)
            else:
                z_scores = (series - mean) / std

        abs_z = z_scores.abs()
        mask = abs_z > t
        outlier_idx = tuple(series.index[mask].tolist())
        n_out = len(outlier_idx)
        pct = round(n_out / len(series) * 100, 2) if len(series) else 0.0

        # Bounds in original value space
        if m == ZScoreMethod.MODIFIED:
            if mad != 0:
                lower = med - (t / 0.6745) * mad
                upper = med + (t / 0.6745) * mad
            else:
                lower = upper = med
        else:
            mean_v = float(series.mean())
            std_v = float(series.std())
            lower = mean_v - t * std_v
            upper = mean_v + t * std_v

        info = ColumnOutlierInfo(
            column=col,
            method=f"zscore_{m.value}",
            total_values=len(series),
            outlier_count=n_out,
            outlier_pct=pct,
            outlier_indices=outlier_idx,
            lower_bound=round(lower, 4),
            upper_bound=round(upper, 4),
            min_outlier=float(series.loc[mask].min()) if n_out else float("nan"),
            max_outlier=float(series.loc[mask].max()) if n_out else float("nan"),
        )
        col_infos[col] = info
        total += n_out

        if n_out > 0:
            flagged.append(col)
            col_mask = pd.Series(False, index=df.index)
            col_mask.loc[mask.index[mask]] = True
            mask_parts.append(col_mask.to_frame(col))

    outlier_mask = pd.concat(mask_parts, axis=1) if mask_parts else pd.DataFrame()

    result = OutlierDetection(
        method=f"zscore_{m.value}",
        columns=col_infos,
        columns_with_outliers=flagged,
        total_outliers=total,
        outlier_mask=outlier_mask,
    )

    logger.info(
        "Z-score outlier detection (%s): %d columns scanned, %d total outliers",
        m.value,
        len(col_infos),
        total,
    )
    return result


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def detect_outliers(
    df: pd.DataFrame,
    method: str | None = None,
    config: ToolkitConfig | None = None,
) -> OutlierDetection:
    """Detect outliers using the method specified in *config*.

    This is the main entry point.  It delegates to
    :func:`detect_outliers_iqr` or :func:`detect_outliers_zscore`
    based on ``config.outlier_method`` (or the *method* override).

    Args:
        df: The DataFrame to scan.
        method: ``"iqr"`` or ``"zscore"``.  ``None`` uses config.
        config: Toolkit configuration.

    Returns:
        An :class:`OutlierDetection` result.
    """
    cfg = config or ToolkitConfig()
    m = method or cfg.outlier_method

    if m == "iqr":
        return detect_outliers_iqr(df, config=cfg)
    elif m == "zscore":
        return detect_outliers_zscore(df, config=cfg)
    else:
        raise ValueError(
            f"Unknown outlier method '{m}'. Choose 'iqr' or 'zscore'."
        )
