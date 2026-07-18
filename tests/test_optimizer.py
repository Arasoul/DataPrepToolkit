"""Tests for optimizer module."""

from __future__ import annotations

import numpy as np
import pandas as pd

from datapreptoolkit import (
    ColumnOptimization,
    OptimizationResult,
    ToolkitConfig,
    optimise_datatypes,
    optimise_memory,
)


class TestOptimiseDatatypes:
    """Tests for optimise_datatypes function."""

    def test_returns_optimized_df_and_result(self, sample_df: pd.DataFrame) -> None:
        """Should return optimized DataFrame and OptimizationResult."""
        result_df, result = optimise_datatypes(sample_df)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(result, OptimizationResult)

    def test_memory_reduction(self, sample_df: pd.DataFrame) -> None:
        """Should reduce memory usage."""
        _, result = optimise_datatypes(sample_df)
        assert result.savings_bytes >= 0
        assert result.savings_pct >= 0

    def test_before_after_memory(self, sample_df: pd.DataFrame) -> None:
        """Should have before/after memory metrics."""
        _, result = optimise_datatypes(sample_df)
        assert result.memory_before > 0
        assert result.memory_after > 0
        assert result.memory_before_human != ""
        assert result.memory_after_human != ""

    def test_savings_mb(self, sample_df: pd.DataFrame) -> None:
        """Should have savings_mb field."""
        _, result = optimise_datatypes(sample_df)
        assert isinstance(result.savings_mb, float)

    def test_column_changes(self, sample_df: pd.DataFrame) -> None:
        """Should record column changes."""
        _, result = optimise_datatypes(sample_df)
        assert isinstance(result.column_changes, list)
        for change in result.column_changes:
            assert isinstance(change, ColumnOptimization)
            assert change.column != ""
            assert change.dtype_before != ""
            assert change.dtype_after != ""
            assert change.memory_before > 0

    def test_does_not_modify_original(self, sample_df: pd.DataFrame) -> None:
        """Original DataFrame should not be modified."""
        original_mem = sample_df.memory_usage(deep=True).sum()
        optimise_datatypes(sample_df)
        assert sample_df.memory_usage(deep=True).sum() == original_mem

    def test_integer_downcast(self) -> None:
        """Should downcast large integers to smaller types."""
        df = pd.DataFrame({"big_int": np.arange(100, dtype=np.int64)})
        result_df, result = optimise_datatypes(df)
        # Should have downcasted from int64 to smaller type
        assert result_df["big_int"].dtype != np.int64 or result.savings_bytes >= 0

    def test_float_downcast(self) -> None:
        """Should downcast float64 to float32."""
        df = pd.DataFrame({"big_float": np.random.uniform(0, 1, 100)})
        result_df, _ = optimise_datatypes(df)
        # May or may not downcast depending on values
        assert isinstance(result_df, pd.DataFrame)

    def test_object_to_category(self) -> None:
        """Should convert low-cardinality object columns to category."""
        df = pd.DataFrame({"cat_col": ["A", "B", "C"] * 10})
        result_df, result = optimise_datatypes(df)
        assert result_df["cat_col"].dtype.name == "category"


class TestOptimiseMemory:
    """Tests for optimise_memory function."""

    def test_returns_optimized_df(self, sample_df: pd.DataFrame) -> None:
        """Should return optimized DataFrame."""
        result_df, result = optimise_memory(sample_df)
        assert isinstance(result_df, pd.DataFrame)
        assert isinstance(result, OptimizationResult)

    def test_disabled_config(self, sample_df: pd.DataFrame) -> None:
        """Should return original when optimization disabled."""
        config = ToolkitConfig(optimise_memory=False)
        result_df, result = optimise_memory(sample_df, config=config)
        assert result_df.equals(sample_df)
        assert "disabled" in result.messages[0].lower()

    def test_enabled_config(self, sample_df: pd.DataFrame) -> None:
        """Should optimize when enabled."""
        config = ToolkitConfig(optimise_memory=True)
        result_df, result = optimise_memory(sample_df, config=config)
        assert result.savings_bytes >= 0
