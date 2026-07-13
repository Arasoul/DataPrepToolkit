"""Tests for utils module."""

from __future__ import annotations

import pandas as pd
import pytest

from datapreptoolkit import (
    copy_dataframe,
    format_bytes,
    identify_column_types,
    memory_usage_mb,
    setup_logging,
    validate_columns,
)
from datapreptoolkit.exceptions import InvalidColumnError
from datapreptoolkit.utils import ensure_directory


class TestCopyDataframe:
    """Tests for copy_dataframe function."""

    def test_returns_copy(self, minimal_df: pd.DataFrame) -> None:
        """Should return a copy of the DataFrame."""
        copy = copy_dataframe(minimal_df)
        assert isinstance(copy, pd.DataFrame)
        assert copy.equals(minimal_df)

    def test_independent_copy(self, minimal_df: pd.DataFrame) -> None:
        """Modifications to copy should not affect original."""
        copy = copy_dataframe(minimal_df)
        copy.iloc[0, 0] = 999
        assert minimal_df.iloc[0, 0] != 999


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_bytes(self) -> None:
        """Should format bytes."""
        assert format_bytes(100) == "100.00 B"

    def test_kilobytes(self) -> None:
        """Should format kilobytes."""
        result = format_bytes(1024)
        assert "KB" in result

    def test_megabytes(self) -> None:
        """Should format megabytes."""
        result = format_bytes(1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self) -> None:
        """Should format gigabytes."""
        result = format_bytes(1024 * 1024 * 1024)
        assert "GB" in result

    def test_zero(self) -> None:
        """Should handle zero bytes."""
        assert format_bytes(0) == "0.00 B"


class TestIdentifyColumnTypes:
    """Tests for identify_column_types function."""

    def test_identifies_numeric(self, sample_df: pd.DataFrame) -> None:
        """Should identify numeric columns."""
        result = identify_column_types(sample_df)
        assert "age" in result["numeric"] or "salary" in result["numeric"]

    def test_identifies_categorical(self, sample_df: pd.DataFrame) -> None:
        """Should identify categorical columns."""
        result = identify_column_types(sample_df)
        cat_types = set(result["categorical"])
        assert "department" in cat_types or "name" in cat_types

    def test_identifies_datetime(self) -> None:
        """Should identify datetime columns (only if dtype is datetime64)."""
        df = pd.DataFrame({
            "date": pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03"]),
            "name": ["a", "b", "c"],
        })
        result = identify_column_types(df)
        assert "date" in result["datetime"]

    def test_identifies_boolean(self, sample_df: pd.DataFrame) -> None:
        """Should identify boolean columns."""
        result = identify_column_types(sample_df)
        assert "is_active" in result["boolean"]


class TestMemoryUsageMb:
    """Tests for memory_usage_mb function."""

    def test_returns_float(self, minimal_df: pd.DataFrame) -> None:
        """Should return float value."""
        result = memory_usage_mb(minimal_df)
        assert isinstance(result, float)
        assert result > 0


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging(self) -> None:
        """Should setup logging without errors."""
        setup_logging("INFO")
        setup_logging("DEBUG")
        setup_logging("WARNING")


class TestValidateColumns:
    """Tests for validate_columns function."""

    def test_valid_columns(self, sample_df: pd.DataFrame) -> None:
        """Should pass for valid columns."""
        validate_columns(sample_df, ["id", "name"])

    def test_invalid_column(self, sample_df: pd.DataFrame) -> None:
        """Should raise InvalidColumnError for invalid column."""
        with pytest.raises(InvalidColumnError):
            validate_columns(sample_df, ["nonexistent"])


class TestEnsureDirectory:
    """Tests for ensure_directory function."""

    def test_creates_directory(self, tmp_path) -> None:
        """Should create directory if it doesn't exist."""
        new_dir = tmp_path / "new_dir"
        ensure_directory(new_dir)
        assert new_dir.exists()

    def test_existing_directory(self, tmp_path) -> None:
        """Should not raise error for existing directory."""
        ensure_directory(tmp_path)
        assert tmp_path.exists()
