"""Tests for validator module."""

from __future__ import annotations

import numpy as np
import pandas as pd

from datapreptoolkit import (
    ValidationResult,
    ValidationRule,
    ValidationViolation,
    validate_dataset,
)


class TestValidateDataset:
    """Tests for validate_dataset function."""

    def test_returns_validation_result(self, sample_df: pd.DataFrame) -> None:
        """Should return ValidationResult."""
        rules = [ValidationRule(column="id", rule_type="not_null")]
        result = validate_dataset(sample_df, rules)
        assert isinstance(result, ValidationResult)

    def test_no_rules(self, sample_df: pd.DataFrame) -> None:
        """Should handle empty rules list."""
        result = validate_dataset(sample_df, [])
        assert result.total_rules == 0
        assert result.is_valid is True

    def test_passing_rules(self, minimal_df: pd.DataFrame) -> None:
        """Should pass when rules are satisfied."""
        rules = [ValidationRule(column="a", rule_type="not_null")]
        result = validate_dataset(minimal_df, rules)
        assert result.is_valid is True
        assert result.failed_rules == 0

    def test_failing_rules(self, sample_df: pd.DataFrame) -> None:
        """Should fail when rules are violated."""
        rules = [ValidationRule(column="age", rule_type="not_null")]
        result = validate_dataset(sample_df, rules)
        assert result.is_valid is False
        assert result.failed_rules > 0


class TestRangeValidation:
    """Tests for range validation rules."""

    def test_valid_range(self, sample_df: pd.DataFrame) -> None:
        """Should pass when values are within range."""
        rules = [
            ValidationRule(
                column="age", rule_type="range",
                min_value=0, max_value=150,
            ),
        ]
        result = validate_dataset(sample_df, rules)
        assert result.is_valid is True

    def test_invalid_range(self) -> None:
        """Should fail when values are outside range."""
        df = pd.DataFrame({"age": [10, 20, 200, 30]})
        rules = [
            ValidationRule(
                column="age", rule_type="range",
                min_value=0, max_value=150,
            ),
        ]
        result = validate_dataset(df, rules)
        assert result.is_valid is False
        assert result.violations[0].violation_count == 1

    def test_range_with_nans(self) -> None:
        """Should not count NaN as violations."""
        df = pd.DataFrame({"age": [10.0, 20.0, np.nan, 30.0]})
        rules = [
            ValidationRule(
                column="age", rule_type="range",
                min_value=0, max_value=150,
            ),
        ]
        result = validate_dataset(df, rules)
        assert result.is_valid is True


class TestRegexValidation:
    """Tests for regex validation rules."""

    def test_valid_regex(self) -> None:
        """Should pass when values match pattern."""
        df = pd.DataFrame({"email": ["test@example.com", "user@domain.org"]})
        rules = [
            ValidationRule(
                column="email", rule_type="regex",
                pattern=r"^[\w.-]+@[\w.-]+\.\w+$",
            ),
        ]
        result = validate_dataset(df, rules)
        assert result.is_valid is True

    def test_invalid_regex(self) -> None:
        """Should fail when values don't match pattern."""
        df = pd.DataFrame({"email": ["test@example.com", "invalid-email"]})
        rules = [
            ValidationRule(
                column="email", rule_type="regex",
                pattern=r"^[\w.-]+@[\w.-]+\.\w+$",
            ),
        ]
        result = validate_dataset(df, rules)
        assert result.is_valid is False


class TestNotNullValidation:
    """Tests for not_null validation rules."""

    def test_not_null_passing(self, minimal_df: pd.DataFrame) -> None:
        """Should pass when no nulls."""
        rules = [ValidationRule(column="a", rule_type="not_null")]
        result = validate_dataset(minimal_df, rules)
        assert result.is_valid is True

    def test_not_null_failing(self, sample_df: pd.DataFrame) -> None:
        """Should fail when nulls present."""
        rules = [ValidationRule(column="age", rule_type="not_null")]
        result = validate_dataset(sample_df, rules)
        assert result.is_valid is False


class TestNoDuplicatesValidation:
    """Tests for no_duplicates validation rules."""

    def test_no_duplicates(self, minimal_df: pd.DataFrame) -> None:
        """Should pass when no duplicates."""
        rules = [ValidationRule(column="a", rule_type="no_duplicates")]
        result = validate_dataset(minimal_df, rules)
        assert result.is_valid is True

    def test_has_duplicates(self, duplicate_df: pd.DataFrame) -> None:
        """Should fail when duplicates present."""
        rules = [ValidationRule(column="id", rule_type="no_duplicates")]
        result = validate_dataset(duplicate_df, rules)
        assert result.is_valid is False
        assert result.violations[0].violation_count > 0


class TestRequiredValidation:
    """Tests for required column validation."""

    def test_required_exists(self, sample_df: pd.DataFrame) -> None:
        """Should pass when column exists."""
        rules = [ValidationRule(column="id", rule_type="required")]
        result = validate_dataset(sample_df, rules)
        assert result.is_valid is True

    def test_required_missing(self, sample_df: pd.DataFrame) -> None:
        """Should fail when column missing."""
        rules = [ValidationRule(column="nonexistent", rule_type="required")]
        result = validate_dataset(sample_df, rules)
        assert result.is_valid is False


class TestInSetValidation:
    """Tests for in_set validation rules."""

    def test_valid_set(self) -> None:
        """Should pass when values are in set."""
        df = pd.DataFrame({"status": ["active", "inactive", "active"]})
        rules = [
            ValidationRule(
                column="status", rule_type="in_set",
                allowed_values={"active", "inactive"},
            ),
        ]
        result = validate_dataset(df, rules)
        assert result.is_valid is True

    def test_invalid_set(self) -> None:
        """Should fail when values not in set."""
        df = pd.DataFrame({"status": ["active", "pending", "active"]})
        rules = [
            ValidationRule(
                column="status", rule_type="in_set",
                allowed_values={"active", "inactive"},
            ),
        ]
        result = validate_dataset(df, rules)
        assert result.is_valid is False


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_result_fields(self, sample_df: pd.DataFrame) -> None:
        """ValidationResult should have required fields."""
        rules = [ValidationRule(column="id", rule_type="not_null")]
        result = validate_dataset(sample_df, rules)
        assert hasattr(result, "total_rules")
        assert hasattr(result, "passed_rules")
        assert hasattr(result, "failed_rules")
        assert hasattr(result, "is_valid")
        assert hasattr(result, "violations")
        assert hasattr(result, "columns_checked")


class TestValidationViolation:
    """Tests for ValidationViolation dataclass."""

    def test_violation_fields(self) -> None:
        """ValidationViolation should have required fields."""
        violation = ValidationViolation(
            column="test",
            rule_type="range",
            violation_count=5,
            violation_pct=10.0,
            sample_violations=[1, 2, 3],
            description="Test violation",
        )
        assert violation.column == "test"
        assert violation.rule_type == "range"
        assert violation.violation_count == 5
        assert violation.violation_pct == 10.0
        assert len(violation.sample_violations) == 3
