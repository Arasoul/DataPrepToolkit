"""Tests for cleaner module."""

from __future__ import annotations

import numpy as np
import pandas as pd

from datapreptoolkit import (
    CleaningResult,
    InvalidValueRule,
    ToolkitConfig,
    clean_dataset,
    detect_invalid_values,
    handle_missing_values,
    parse_datetimes,
    remove_duplicates,
)


class TestHandleMissingValues:
    """Tests for handle_missing_values function."""

    def test_returns_cleaned_df(self, sample_df: pd.DataFrame) -> None:
        """Should return cleaned DataFrame and CleaningResult."""
        result_df, result = handle_missing_values(sample_df)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(result, CleaningResult)

    def test_median_imputation(self, sample_df: pd.DataFrame) -> None:
        """Should impute numeric columns with median."""
        result_df, _ = handle_missing_values(sample_df, strategy="median")
        assert result_df.isnull().sum().sum() < sample_df.isnull().sum().sum()

    def test_mean_imputation(self, sample_df: pd.DataFrame) -> None:
        """Should impute numeric columns with mean."""
        result_df, _ = handle_missing_values(sample_df, strategy="mean")
        assert result_df.isnull().sum().sum() < sample_df.isnull().sum().sum()

    def test_mode_imputation(self, sample_df: pd.DataFrame) -> None:
        """Should impute categorical columns with mode."""
        result_df, _ = handle_missing_values(sample_df, strategy="mode")
        assert result_df.isnull().sum().sum() < sample_df.isnull().sum().sum()

    def test_drop_rows(self, sample_df: pd.DataFrame) -> None:
        """Should drop rows with missing values."""
        result_df, _ = handle_missing_values(sample_df, strategy="drop_rows")
        assert len(result_df) < len(sample_df)

    def test_drop_columns(self, sample_df: pd.DataFrame) -> None:
        """Should drop columns with too many missing values."""
        df = sample_df.copy()
        df["almost_null"] = np.nan
        result_df, _ = handle_missing_values(df, strategy="drop_column")
        assert "almost_null" not in result_df.columns

    def test_does_not_modify_original(self, sample_df: pd.DataFrame) -> None:
        """Original DataFrame should not be modified."""
        original_null_count = sample_df.isnull().sum().sum()
        handle_missing_values(sample_df)
        assert sample_df.isnull().sum().sum() == original_null_count


class TestParseDatetimes:
    """Tests for parse_datetimes function."""

    def test_returns_datetime_columns(self, sample_df: pd.DataFrame) -> None:
        """Should parse datetime columns."""
        result_df, result = parse_datetimes(sample_df)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(result, CleaningResult)

    def test_parses_join_date(self, sample_df: pd.DataFrame) -> None:
        """Should parse join_date column to datetime."""
        result_df, _ = parse_datetimes(sample_df, columns=["join_date"])
        assert pd.api.types.is_datetime64_any_dtype(result_df["join_date"])


class TestRemoveDuplicates:
    """Tests for remove_duplicates function."""

    def test_returns_deduplicated_df(self, duplicate_df: pd.DataFrame) -> None:
        """Should return deduplicated DataFrame."""
        result_df, result = remove_duplicates(duplicate_df)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(result, CleaningResult)
        assert len(result_df) < len(duplicate_df)

    def test_no_duplicates(self, minimal_df: pd.DataFrame) -> None:
        """Should handle DataFrame with no duplicates."""
        result_df, result = remove_duplicates(minimal_df)
        assert len(result_df) == len(minimal_df)

    def test_subset_duplicates(self) -> None:
        """Should detect duplicates based on subset."""
        df = pd.DataFrame(
            {
                "id": [1, 1, 2],
                "value": ["a", "b", "c"],
            }
        )
        result_df, _ = remove_duplicates(df, subset=["id"])
        assert len(result_df) == 2


class TestDetectInvalidValues:
    """Tests for detect_invalid_values function."""

    def test_returns_tuple(self, sample_df: pd.DataFrame) -> None:
        """Should return tuple of (invalid_indices_dict, CleaningResult)."""
        invalid_dict, result = detect_invalid_values(sample_df)
        assert isinstance(invalid_dict, dict)
        assert isinstance(result, CleaningResult)

    def test_with_custom_rules(self, sample_df: pd.DataFrame) -> None:
        """Should accept custom rules."""
        rules = [
            InvalidValueRule(
                column="age",
                condition=lambda s: (s < 0) | (s > 150),
                description="Age must be between 0 and 150",
            ),
        ]
        invalid_dict, result = detect_invalid_values(sample_df, rules=rules)
        assert isinstance(invalid_dict, dict)
        assert isinstance(result, CleaningResult)


class TestCleanDataset:
    """Tests for clean_dataset function."""

    def test_returns_cleaned_df(self, sample_df: pd.DataFrame) -> None:
        """Should return cleaned DataFrame and CleaningResult."""
        result_df, result = clean_dataset(sample_df)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(result, CleaningResult)

    def test_removes_duplicates(self, duplicate_df: pd.DataFrame) -> None:
        """Should remove duplicates when configured."""
        config = ToolkitConfig(remove_duplicates=True)
        result_df, _ = clean_dataset(duplicate_df, config=config)
        assert len(result_df) < len(duplicate_df)

    def test_handles_missing_values(self, sample_df: pd.DataFrame) -> None:
        """Should handle missing values."""
        result_df, _ = clean_dataset(sample_df)
        assert result_df.isnull().sum().sum() <= sample_df.isnull().sum().sum()


class TestCleaningResult:
    """Tests for CleaningResult dataclass."""

    def test_cleaning_result_fields(self) -> None:
        """CleaningResult should have required fields."""
        result = CleaningResult()
        assert result.rows_before == 0
        assert result.rows_after == 0
        assert result.cols_before == 0
        assert result.cols_after == 0
        assert isinstance(result.columns_dropped, list)
        assert isinstance(result.imputations, list)
        assert isinstance(result.messages, list)
