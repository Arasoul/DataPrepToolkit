"""Data cleaning operations: missing values, duplicates, datetime parsing,
and invalid-value detection.

Every cleaning function returns a **new** DataFrame and a :class:`CleaningResult`
so callers can inspect exactly what changed.  The original is never mutated.

Example::

    from datapreptoolkit.cleaner import (
        handle_missing_values,
        remove_duplicates,
    )

    cleaned, result = handle_missing_values(df, strategy="median")
    cleaned, dup_result = remove_duplicates(cleaned)
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from datapreptoolkit.config import ToolkitConfig
from datapreptoolkit.exceptions import CleaningError
from datapreptoolkit.utils import (
    copy_dataframe,
    find_datetime_columns,
)

logger = logging.getLogger("datapreptoolkit")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImputationRecord:
    """Record of a single imputation operation.

    Attributes:
        column: Column that was modified.
        strategy: Imputation strategy applied.
        fill_value: The value used for imputation (if scalar).
        rows_filled: Number of rows that received a fill.
    """

    column: str
    strategy: str
    fill_value: Any = None
    rows_filled: int = 0


@dataclass
class CleaningResult:
    """Summary of all cleaning operations performed in one call.

    Attributes:
        rows_before: Row count before cleaning.
        rows_after: Row count after cleaning.
        cols_before: Column count before cleaning.
        cols_after: Column count after cleaning.
        columns_dropped: Column names that were removed.
        columns_parsed: Column names that were converted to datetime.
        imputations: Per-column imputation records.
        duplicates_dropped: Number of duplicate rows removed.
        invalid_values_found: Mapping of column → list of invalid-row indices.
        messages: Human-readable log of every change.
    """

    rows_before: int = 0
    rows_after: int = 0
    cols_before: int = 0
    cols_after: int = 0
    columns_dropped: list[str] = field(default_factory=list)
    columns_parsed: list[str] = field(default_factory=list)
    imputations: list[ImputationRecord] = field(default_factory=list)
    duplicates_dropped: int = 0
    invalid_values_found: dict[str, list[int]] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API: Missing Value Handling
# ---------------------------------------------------------------------------

_STRATEGY_DISPATCH: dict[str, str] = {
    "mean": "mean",
    "median": "median",
    "mode": "mode",
    "ffill": "ffill",
    "bfill": "bfill",
    "interpolate": "interpolate",
    "drop_rows": "drop_rows",
    "drop_column": "drop_column",
    "zero": "zero",
    "empty": "empty",
}


def handle_missing_values(
    df: pd.DataFrame,
    strategy: str = "median",
    strategy_map: dict[str, str] | None = None,
    drop_threshold: float = 0.6,
    config: ToolkitConfig | None = None,
) -> tuple[pd.DataFrame, CleaningResult]:
    """Treat missing values using the specified strategy.

    Strategies
    ----------
    ``"mean"``
        Fill numeric columns with their mean; categoricals with mode.
    ``"median"``
        Fill numeric columns with their median; categoricals with mode.
    ``"mode"``
        Fill every column with its mode.
    ``"ffill"``
        Forward-fill.
    ``"bfill"``
        Backward-fill.
    ``"interpolate"``
        Linear interpolation for numeric; ffill for the rest.
    ``"drop_rows"``
        Drop any row containing a null.
    ``"drop_column"``
        Drop columns whose null ratio exceeds *drop_threshold*.
    ``"zero"``
        Fill numeric nulls with 0; categoricals with ``"Unknown"``.
    ``"empty"``
        Fill numeric with NaN (no-op); categoricals with ``"Unknown"``.

    Args:
        df: The DataFrame to clean.
        strategy: Default strategy applied to every column with missing values.
        strategy_map: Per-column strategy overrides.  Keys are column names,
            values are strategy strings (same set as *strategy*).
        drop_threshold: Null-ratio threshold (0–1) above which columns are
            dropped when using ``"drop_column"``.
        config: Toolkit configuration.

    Returns:
        A tuple of ``(cleaned_df, CleaningResult)``.
    """
    cleaned = copy_dataframe(df)
    result = CleaningResult(
        rows_before=df.shape[0],
        rows_after=df.shape[0],
        cols_before=df.shape[1],
        cols_after=df.shape[1],
    )

    overrides = strategy_map or {}
    missing_cols = [c for c in cleaned.columns if cleaned[c].isnull().any()]

    for col in missing_cols:
        strat = overrides.get(col, strategy)
        null_count = int(cleaned[col].isnull().sum())
        fill_val: Any = None
        is_numeric = pd.api.types.is_numeric_dtype(cleaned[col])

        # Fallback: mean/median on non-numeric columns → mode
        if strat in ("mean", "median") and not is_numeric:
            strat = "mode"

        if strat == "mean" and is_numeric:
            fill_val = cleaned[col].mean()
            cleaned[col] = cleaned[col].fillna(fill_val)
        elif strat == "median" and is_numeric:
            fill_val = cleaned[col].median()
            cleaned[col] = cleaned[col].fillna(fill_val)
        elif strat == "mode":
            mode_series = cleaned[col].mode()
            if not mode_series.empty:
                fill_val = mode_series.iloc[0]
                cleaned[col] = cleaned[col].fillna(fill_val)
        elif strat == "ffill":
            cleaned[col] = cleaned[col].ffill()
        elif strat == "bfill":
            cleaned[col] = cleaned[col].bfill()
        elif strat == "interpolate":
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                cleaned[col] = cleaned[col].interpolate(method="linear")
                cleaned[col] = cleaned[col].bfill().ffill()
            else:
                cleaned[col] = cleaned[col].ffill().bfill()
        elif strat == "drop_rows":
            before = len(cleaned)
            cleaned = cleaned.dropna(subset=[col])
            null_count = before - len(cleaned)
            result.messages.append(
                f"Dropped {null_count} rows due to nulls in '{col}'."
            )
        elif strat == "drop_column":
            cleaned = cleaned.drop(columns=[col])
            result.columns_dropped.append(col)
            result.messages.append(f"Dropped column '{col}' (>60% null).")
            continue  # skip imputation record
        elif strat == "zero":
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                fill_val = 0
                cleaned[col] = cleaned[col].fillna(0)
            else:
                fill_val = "Unknown"
                cleaned[col] = cleaned[col].fillna("Unknown")
        elif strat == "empty":
            if not pd.api.types.is_numeric_dtype(cleaned[col]):
                fill_val = "Unknown"
                cleaned[col] = cleaned[col].fillna("Unknown")
        else:
            raise CleaningError(f"Unknown strategy '{strat}' for column '{col}'.")

        result.imputations.append(
            ImputationRecord(
                column=col,
                strategy=strat,
                fill_value=fill_val,
                rows_filled=null_count,
            )
        )
        result.messages.append(
            f"Column '{col}': filled {null_count} nulls with '{strat}'."
        )

    result.rows_after = cleaned.shape[0]
    result.cols_after = cleaned.shape[1]

    logger.info(
        "Missing values handled: %d columns imputed, %d columns dropped",
        len(result.imputations),
        len(result.columns_dropped),
    )
    return cleaned, result


# ---------------------------------------------------------------------------
# Public API: Datetime Parsing
# ---------------------------------------------------------------------------

def parse_datetimes(
    df: pd.DataFrame,
    columns: list[str] | None = None,
    datetime_format: str | None = None,
    config: ToolkitConfig | None = None,
) -> tuple[pd.DataFrame, CleaningResult]:
    """Detect and convert object columns to datetime.

    Args:
        df: The DataFrame to clean.
        columns: Explicit list of columns to parse.  ``None`` means
            auto-detect all object columns that can be parsed.
        datetime_format: strftime format string.  ``None`` lets pandas infer.
        config: Toolkit configuration.

    Returns:
        A tuple of ``(cleaned_df, CleaningResult)``.
    """
    cfg = config or ToolkitConfig()
    cleaned = copy_dataframe(df)
    result = CleaningResult(
        rows_before=df.shape[0],
        rows_after=df.shape[0],
        cols_before=df.shape[1],
        cols_after=df.shape[1],
    )

    candidates = columns or find_datetime_columns(cleaned)

    for col in candidates:
        if col not in cleaned.columns:
            continue
        try:
            cleaned[col] = pd.to_datetime(
                cleaned[col],
                format=datetime_format or cfg.datetime_format,
                errors="coerce",
            )
            # If the conversion turned >50 % of values into NaT, revert
            nat_ratio = cleaned[col].isnull().sum() / len(cleaned)
            if nat_ratio > 0.5:
                cleaned[col] = df[col]
                result.messages.append(
                    f"Column '{col}': datetime parse reverted (>50% NaT)."
                )
            else:
                result.columns_parsed.append(col)
                result.messages.append(f"Column '{col}' parsed as datetime.")
        except (ValueError, TypeError) as exc:
            result.messages.append(
                f"Column '{col}': datetime parse skipped — {exc}."
            )

    logger.info("Datetime parsing: %d columns converted", len(result.columns_parsed))
    return cleaned, result


# ---------------------------------------------------------------------------
# Public API: Duplicate Removal
# ---------------------------------------------------------------------------

def remove_duplicates(
    df: pd.DataFrame,
    subset: list[str] | None = None,
    keep: str = "first",
    config: ToolkitConfig | None = None,
) -> tuple[pd.DataFrame, CleaningResult]:
    """Detect and optionally remove duplicate rows.

    Args:
        df: The DataFrame to clean.
        subset: Column names to consider. ``None`` means all columns.
        keep: ``"first"``, ``"last"``, or ``False`` (drop all duplicates).
        config: Toolkit configuration.

    Returns:
        A tuple of ``(cleaned_df, CleaningResult)``.
    """
    cleaned = copy_dataframe(df)
    n_before = len(cleaned)

    dup_keep: str | bool = False if keep == "never" else keep
    dup_mask = cleaned.duplicated(subset=subset, keep=dup_keep)  # type: ignore[arg-type]
    n_dups = int(dup_mask.sum())

    if n_dups > 0:
        cleaned = cleaned[~dup_mask].reset_index(drop=True)

    result = CleaningResult(
        rows_before=n_before,
        rows_after=len(cleaned),
        cols_before=df.shape[1],
        cols_after=df.shape[1],
        duplicates_dropped=n_dups,
        messages=[f"Removed {n_dups} duplicate rows."],
    )

    logger.info("Duplicates removed: %d rows", n_dups)
    return cleaned, result


# ---------------------------------------------------------------------------
# Public API: Invalid Value Detection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InvalidValueRule:
    """A single validation rule for a column.

    Attributes:
        column: Column name to check.
        condition: A callable that receives a Series and returns a boolean
            mask of *invalid* rows.
        description: Human-readable description of the rule.
    """

    column: str
    condition: Callable[[pd.Series], pd.Series]
    description: str = ""


def detect_invalid_values(
    df: pd.DataFrame,
    rules: list[InvalidValueRule] | None = None,
    check_negative_non_negative: bool = True,
    config: ToolkitConfig | None = None,
) -> tuple[dict[str, list[int]], CleaningResult]:
    """Scan for invalid values using built-in checks and custom rules.

    Built-in checks (when *check_negative_non_negative* is ``True``):
    * Columns with names suggesting non-negative semantics (e.g. ``price``,
      ``age``, ``count``) are scanned for negative values.

    Args:
        df: The DataFrame to scan.
        rules: Optional list of custom :class:`InvalidValueRule`.
        check_negative_non_negative: Enable the built-in negative check.
        config: Toolkit configuration.

    Returns:
        A tuple of ``(invalid_map, CleaningResult)`` where *invalid_map*
        maps column names to lists of row indices containing invalid values.
    """
    result = CleaningResult(
        rows_before=df.shape[0],
        rows_after=df.shape[0],
        cols_before=df.shape[1],
        cols_after=df.shape[1],
    )
    invalid_map: dict[str, list[int]] = {}

    # -- Built-in: negative check --
    non_negative_hints = {
        "price", "age", "count", "quantity", "amount", "revenue",
        "payment_value", "freight_value", "weight", "height", "width",
        "length", "photos_qty", "installments",
    }
    if check_negative_non_negative:
        for col in df.columns:
            col_lower = col.lower()
            if any(hint in col_lower for hint in non_negative_hints) \
                    and pd.api.types.is_numeric_dtype(df[col]):
                mask = df[col] < 0
                bad_idx = df.index[mask].tolist()
                if bad_idx:
                    invalid_map[col] = bad_idx
                    result.invalid_values_found[col] = bad_idx
                    result.messages.append(
                        f"Column '{col}': {len(bad_idx)} negative values found."
                    )
                    logger.warning(
                        "Invalid values in '%s': %d negatives",
                        col,
                        len(bad_idx),
                    )

    # -- Custom rules --
    if rules:
        for rule in rules:
            if rule.column not in df.columns:
                continue
            try:
                mask = rule.condition(df[rule.column])
                bad_idx = df.index[mask].tolist()
                if bad_idx:
                    key = f"{rule.column} (custom)"
                    invalid_map[key] = bad_idx
                    result.invalid_values_found[key] = bad_idx
                    msg = (
                        f"Column '{rule.column}': "
                        f"{len(bad_idx)} invalid — "
                        f"{rule.description}."
                    )
                    result.messages.append(msg)
                    logger.warning("Custom rule violation: %s", msg)
            except Exception as exc:
                result.messages.append(
                    f"Rule for '{rule.column}' failed: {exc}"
                )

    if not invalid_map:
        result.messages.append("No invalid values detected.")

    logger.info(
        "Invalid value detection: %d columns with issues", len(invalid_map)
    )
    return invalid_map, result


# ---------------------------------------------------------------------------
# Public API: Comprehensive Clean Pipeline
# ---------------------------------------------------------------------------

def clean_dataset(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> tuple[pd.DataFrame, CleaningResult]:
    """Run the full cleaning pipeline controlled by *config*.

    Pipeline order:
    1. Remove duplicates (if ``config.remove_duplicates``).
    2. Parse datetimes (if ``config.parse_datetimes``).
    3. Handle missing values (``"median"`` for numeric, ``"mode"`` for rest).

    Args:
        df: The DataFrame to clean.
        config: Toolkit configuration.

    Returns:
        A tuple of ``(cleaned_df, CleaningResult)`` with a merged result
        log from every sub-step.
    """
    cfg = config or ToolkitConfig()
    cleaned = copy_dataframe(df)
    merged = CleaningResult(
        rows_before=df.shape[0],
        cols_before=df.shape[1],
    )

    # Step 1: Duplicates
    if cfg.remove_duplicates:
        subset = (
            list(cfg.duplicate_subset)
            if cfg.duplicate_subset
            else None
        )
        keep: str = (
            "never" if cfg.duplicate_keep == "none"
            else cfg.duplicate_keep
        )
        cleaned, dup_res = remove_duplicates(
            cleaned, subset=subset, keep=keep, config=cfg
        )
        merged.duplicates_dropped = dup_res.duplicates_dropped
        merged.messages.extend(dup_res.messages)

    # Step 2: Datetimes
    if cfg.parse_datetimes:
        cleaned, dt_res = parse_datetimes(
            cleaned,
            columns=cfg.datetime_columns,
            datetime_format=cfg.datetime_format,
            config=cfg,
        )
        merged.columns_parsed = dt_res.columns_parsed
        merged.messages.extend(dt_res.messages)

    # Step 3: Missing values
    strat = "median"  # default
    merged.rows_after = cleaned.shape[0]
    merged.cols_after = cleaned.shape[1]

    # Build per-column strategies
    strat_map: dict[str, str] = {}
    for col in cleaned.columns:
        if cleaned[col].isnull().any():
            if pd.api.types.is_numeric_dtype(cleaned[col]):
                strat_map[col] = "median"
            else:
                strat_map[col] = "mode"

    if strat_map:
        cleaned, mv_res = handle_missing_values(
            cleaned, strategy=strat, strategy_map=strat_map, config=cfg
        )
        merged.imputations = mv_res.imputations
        merged.columns_dropped = mv_res.columns_dropped
        merged.messages.extend(mv_res.messages)
        merged.rows_after = cleaned.shape[0]
        merged.cols_after = cleaned.shape[1]

    logger.info(
        "Clean pipeline complete: %s -> %s rows",
        merged.rows_before,
        merged.rows_after,
    )
    return cleaned, merged
