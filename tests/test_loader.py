"""Tests for loader module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from datapreptoolkit import (
    ColumnProfile,
    DatasetProfile,
    ToolkitConfig,
    load_csv,
    load_dataframe,
    profile_dataset,
)
from datapreptoolkit.exceptions import FileFormatError, LoadError


class TestLoadCSV:
    """Tests for load_csv function."""

    def test_load_csv_success(self, test_csv_path: Path) -> None:
        """Should load CSV successfully."""
        df = load_csv(test_csv_path)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert list(df.columns) == ["col1", "col2"]

    def test_load_csv_with_encoding(self, test_csv_path: Path) -> None:
        """Should load CSV with explicit encoding."""
        df = load_csv(test_csv_path, encoding="utf-8")
        assert len(df) == 3

    def test_load_csv_nonexistent_file(self) -> None:
        """Should raise FileNotFoundError for nonexistent file."""
        with pytest.raises(FileNotFoundError):
            load_csv("nonexistent.csv")

    def test_load_csv_wrong_format(self, tmp_path: Path) -> None:
        """Should raise FileFormatError for non-CSV file."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a csv")
        with pytest.raises(FileFormatError):
            load_csv(txt_file)

    def test_load_csv_empty(self, tmp_path: Path) -> None:
        """Should raise LoadError for empty CSV."""
        empty_csv = tmp_path / "empty.csv"
        empty_csv.write_text("")
        with pytest.raises(LoadError):
            load_csv(empty_csv)


class TestLoadDataframe:
    """Tests for load_dataframe function."""

    def test_load_dataframe_success(self, minimal_df: pd.DataFrame) -> None:
        """Should load DataFrame successfully."""
        result = load_dataframe(minimal_df)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 5

    def test_load_dataframe_returns_copy(self, minimal_df: pd.DataFrame) -> None:
        """Should return a copy, not the original."""
        result = load_dataframe(minimal_df)
        result.iloc[0, 0] = 999
        assert minimal_df.iloc[0, 0] != 999


class TestProfileDataset:
    """Tests for profile_dataset function."""

    def test_profile_returns_dataset_profile(self, sample_df: pd.DataFrame) -> None:
        """Should return a DatasetProfile."""
        profile = profile_dataset(sample_df)
        assert isinstance(profile, DatasetProfile)

    def test_profile_shape(self, sample_df: pd.DataFrame) -> None:
        """Profile shape should match DataFrame shape."""
        profile = profile_dataset(sample_df)
        assert profile.shape == sample_df.shape

    def test_profile_memory(self, sample_df: pd.DataFrame) -> None:
        """Profile should have memory info."""
        profile = profile_dataset(sample_df)
        assert profile.memory_bytes > 0
        assert profile.memory_human != ""

    def test_profile_column_types(self, sample_df: pd.DataFrame) -> None:
        """Profile should identify column types correctly."""
        profile = profile_dataset(sample_df)
        assert "id" in profile.numeric_columns or "id" in profile.categorical_columns
        assert "salary" in profile.numeric_columns

    def test_profile_missing_columns(self, sample_df: pd.DataFrame) -> None:
        """Profile should identify columns with missing values."""
        profile = profile_dataset(sample_df)
        assert len(profile.missing_columns) > 0

    def test_profile_quality_score(self, sample_df: pd.DataFrame) -> None:
        """Quality score should be between 0 and 100."""
        profile = profile_dataset(sample_df)
        assert 0 <= profile.overall_quality_score <= 100

    def test_profile_column_profiles(self, sample_df: pd.DataFrame) -> None:
        """Profile should have ColumnProfile for each column."""
        profile = profile_dataset(sample_df)
        assert len(profile.columns) == len(sample_df.columns)
        for col in sample_df.columns:
            assert col in profile.columns
            assert isinstance(profile.columns[col], ColumnProfile)

    def test_profile_with_empty_df(self, empty_df: pd.DataFrame) -> None:
        """Should handle empty DataFrame."""
        profile = profile_dataset(empty_df)
        assert profile.shape == (0, 0)

    def test_profile_with_config(
        self,
        sample_df: pd.DataFrame,
        default_config: ToolkitConfig,
    ) -> None:
        """Should accept config parameter."""
        profile = profile_dataset(sample_df, config=default_config)
        assert isinstance(profile, DatasetProfile)


class TestColumnProfile:
    """Tests for ColumnProfile dataclass."""

    def test_column_profile_fields(self, sample_df: pd.DataFrame) -> None:
        """ColumnProfile should have all required fields."""
        profile = profile_dataset(sample_df)
        col_profile = profile.columns["age"]

        assert col_profile.name == "age"
        assert col_profile.dtype != ""
        assert col_profile.non_null >= 0
        assert col_profile.null_count >= 0
        assert 0 <= col_profile.null_pct <= 100
        assert col_profile.unique_count >= 0
        assert 0 <= col_profile.unique_ratio <= 1
