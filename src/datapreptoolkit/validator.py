"""Data validation module for checking data quality rules.

Provides functions and dataclasses for validating DataFrames against
custom rules such as value ranges, regex patterns, required columns,
and duplicate primary keys.

Example::

    from datapreptoolkit.validator import validate_dataset, ValidationRule

    rules = [
        ValidationRule(
            column="age", rule_type="range",
            min_value=0, max_value=150,
        ),
        ValidationRule(
            column="email", rule_type="regex",
            pattern=r"^[\\w.-]+@[\\w.-]+\\.\\w+$",
        ),
        ValidationRule(column="id", rule_type="no_duplicates"),
    ]
    result = validate_dataset(df, rules)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from datapreptoolkit.config import ToolkitConfig

logger = logging.getLogger("datapreptoolkit")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationRule:
    """A single validation rule for a column.

    Attributes:
        column: Column name to validate.
        rule_type: Type of validation — ``"range"``, ``"regex"``,
            ``"not_null"``, ``"no_duplicates"``, ``"required"``,
            ``"unique"``, ``"in_set"``.
        min_value: Minimum value for range checks (inclusive).
        max_value: Maximum value for range checks (inclusive).
        pattern: Regex pattern for regex checks.
        allowed_values: Set of allowed values for in_set checks.
        description: Human-readable description of the rule.
    """

    column: str
    rule_type: str
    min_value: float | None = None
    max_value: float | None = None
    pattern: str | None = None
    allowed_values: set[Any] | None = None
    description: str = ""


@dataclass(frozen=True)
class ValidationViolation:
    """A single validation failure.

    Attributes:
        column: Column name that failed.
        rule_type: Type of rule that was violated.
        violation_count: Number of rows that violated the rule.
        violation_pct: Percentage of rows that violated (0-100).
        sample_violations: Up to 5 example violating values.
        description: Human-readable description.
    """

    column: str
    rule_type: str
    violation_count: int
    violation_pct: float
    sample_violations: list[Any] = field(default_factory=list)
    description: str = ""


@dataclass(frozen=True)
class ValidationResult:
    """Complete validation result for a DataFrame.

    Attributes:
        total_rules: Number of rules checked.
        passed_rules: Number of rules that passed.
        failed_rules: Number of rules that failed.
        is_valid: Overall validation status (True if all rules pass).
        violations: List of :class:`ValidationViolation` objects.
        columns_checked: List of column names that were validated.
    """

    total_rules: int
    passed_rules: int
    failed_rules: int
    is_valid: bool
    violations: list[ValidationViolation] = field(default_factory=list)
    columns_checked: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal validation functions
# ---------------------------------------------------------------------------

def _validate_range(
    df: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationViolation | None:
    """Validate that column values fall within [min_value, max_value]."""
    if rule.column not in df.columns:
        return ValidationViolation(
            column=rule.column,
            rule_type="range",
            violation_count=len(df),
            violation_pct=100.0,
            description=f"Column '{rule.column}' not found in DataFrame.",
        )

    series = df[rule.column].dropna()
    if not pd.api.types.is_numeric_dtype(series):
        return ValidationViolation(
            column=rule.column,
            rule_type="range",
            violation_count=len(df),
            violation_pct=100.0,
            description=f"Column '{rule.column}' is not numeric for range check.",
        )

    violations = pd.Series([False] * len(df), index=df.index)
    if rule.min_value is not None:
        violations = violations | (df[rule.column] < rule.min_value)
    if rule.max_value is not None:
        violations = violations | (df[rule.column] > rule.max_value)

    # Don't count NaN as violations
    violations = violations & df[rule.column].notna()

    count = int(violations.sum())
    if count == 0:
        return None

    pct = round(count / len(df) * 100, 2)
    samples = df.loc[violations, rule.column].head(5).tolist()

    return ValidationViolation(
        column=rule.column,
        rule_type="range",
        violation_count=count,
        violation_pct=pct,
        sample_violations=samples,
        description=(
            rule.description
            or f"Values outside range "
               f"[{rule.min_value}, {rule.max_value}]."
        ),
    )


def _validate_regex(
    df: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationViolation | None:
    """Validate that string column values match a regex pattern."""
    if rule.column not in df.columns:
        return ValidationViolation(
            column=rule.column,
            rule_type="regex",
            violation_count=len(df),
            violation_pct=100.0,
            description=f"Column '{rule.column}' not found in DataFrame.",
        )

    if not rule.pattern:
        return ValidationViolation(
            column=rule.column,
            rule_type="regex",
            violation_count=0,
            violation_pct=0.0,
            description="No regex pattern provided.",
        )

    series = df[rule.column].dropna().astype(str)
    pattern = re.compile(rule.pattern)
    violations = ~series.str.match(pattern)

    count = int(violations.sum())
    if count == 0:
        return None

    pct = round(count / len(df) * 100, 2)
    samples = series[violations].head(5).tolist()

    return ValidationViolation(
        column=rule.column,
        rule_type="regex",
        violation_count=count,
        violation_pct=pct,
        sample_violations=samples,
        description=(
            rule.description
            or f"Values not matching pattern '{rule.pattern}'."
        ),
    )


def _validate_not_null(
    df: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationViolation | None:
    """Validate that column has no null values."""
    if rule.column not in df.columns:
        return ValidationViolation(
            column=rule.column,
            rule_type="not_null",
            violation_count=len(df),
            violation_pct=100.0,
            description=f"Column '{rule.column}' not found in DataFrame.",
        )

    null_count = int(df[rule.column].isnull().sum())
    if null_count == 0:
        return None

    pct = round(null_count / len(df) * 100, 2)
    return ValidationViolation(
        column=rule.column,
        rule_type="not_null",
        violation_count=null_count,
        violation_pct=pct,
        description=rule.description or f"Column has {null_count} null values.",
    )


def _validate_no_duplicates(
    df: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationViolation | None:
    """Validate that column has no duplicate values."""
    if rule.column not in df.columns:
        return ValidationViolation(
            column=rule.column,
            rule_type="no_duplicates",
            violation_count=len(df),
            violation_pct=100.0,
            description=f"Column '{rule.column}' not found in DataFrame.",
        )

    duplicates = df[rule.column].duplicated(keep="first")
    count = int(duplicates.sum())
    if count == 0:
        return None

    pct = round(count / len(df) * 100, 2)
    samples = df.loc[duplicates, rule.column].head(5).tolist()

    return ValidationViolation(
        column=rule.column,
        rule_type="no_duplicates",
        violation_count=count,
        violation_pct=pct,
        sample_violations=samples,
        description=rule.description or f"Column has {count} duplicate values.",
    )


def _validate_unique(
    df: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationViolation | None:
    """Validate that column has all unique values (alias for no_duplicates)."""
    return _validate_no_duplicates(df, rule)


def _validate_required(
    df: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationViolation | None:
    """Validate that a column exists in the DataFrame."""
    if rule.column in df.columns:
        return None

    return ValidationViolation(
        column=rule.column,
        rule_type="required",
        violation_count=1,
        violation_pct=100.0,
        description=rule.description or f"Required column '{rule.column}' is missing.",
    )


def _validate_in_set(
    df: pd.DataFrame,
    rule: ValidationRule,
) -> ValidationViolation | None:
    """Validate that column values are within an allowed set."""
    if rule.column not in df.columns:
        return ValidationViolation(
            column=rule.column,
            rule_type="in_set",
            violation_count=len(df),
            violation_pct=100.0,
            description=f"Column '{rule.column}' not found in DataFrame.",
        )

    if not rule.allowed_values:
        return ValidationViolation(
            column=rule.column,
            rule_type="in_set",
            violation_count=0,
            violation_pct=0.0,
            description="No allowed values provided.",
        )

    series = df[rule.column].dropna()
    violations = ~series.isin(rule.allowed_values)

    count = int(violations.sum())
    if count == 0:
        return None

    pct = round(count / len(df) * 100, 2)
    samples = series[violations].head(5).tolist()

    return ValidationViolation(
        column=rule.column,
        rule_type="in_set",
        violation_count=count,
        violation_pct=pct,
        sample_violations=samples,
        description=rule.description or "Values not in allowed set.",
    )


# ---------------------------------------------------------------------------
# Validation dispatch
# ---------------------------------------------------------------------------

_VALIDATORS = {
    "range": _validate_range,
    "regex": _validate_regex,
    "not_null": _validate_not_null,
    "no_duplicates": _validate_no_duplicates,
    "unique": _validate_unique,
    "required": _validate_required,
    "in_set": _validate_in_set,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def validate_dataset(
    df: pd.DataFrame,
    rules: list[ValidationRule],
    config: ToolkitConfig | None = None,
) -> ValidationResult:
    """Validate a DataFrame against a list of rules.

    The function never modifies *df*.

    Args:
        df: The DataFrame to validate.
        rules: List of :class:`ValidationRule` objects.
        config: Toolkit configuration (reserved for future use).

    Returns:
        A :class:`ValidationResult` summarising all violations.
    """
    violations: list[ValidationViolation] = []
    columns_checked: list[str] = []

    for rule in rules:
        validator = _VALIDATORS.get(rule.rule_type)
        if validator is None:
            logger.warning(
                "Unknown rule_type '%s' for column '%s'",
                rule.rule_type,
                rule.column,
            )
            continue

        if rule.column not in columns_checked:
            columns_checked.append(rule.column)

        violation = validator(df, rule)
        if violation is not None:
            violations.append(violation)

    total = len(rules)
    failed = len(violations)
    result = ValidationResult(
        total_rules=total,
        passed_rules=total - failed,
        failed_rules=failed,
        is_valid=(failed == 0),
        violations=violations,
        columns_checked=columns_checked,
    )

    logger.info(
        "Validation: %d/%d rules passed, %d violations",
        total - failed,
        total,
        failed,
    )
    return result
