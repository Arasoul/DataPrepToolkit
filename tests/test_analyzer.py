"""Tests for analyzer module."""

from __future__ import annotations

import pandas as pd

from datapreptoolkit import (
    CategoricalAnalysis,
    CategoricalColumnStats,
    ColumnMissingInfo,
    FeatureSummary,
    MissingValueAnalysis,
    NumericAnalysis,
    NumericColumnStats,
    analyze_categorical_columns,
    analyze_missing_values,
    analyze_numeric_columns,
    generate_feature_summaries,
)


class TestAnalyzeMissingValues:
    """Tests for analyze_missing_values function."""

    def test_returns_missing_value_analysis(self, sample_df: pd.DataFrame) -> None:
        """Should return MissingValueAnalysis."""
        result = analyze_missing_values(sample_df)
        assert isinstance(result, MissingValueAnalysis)

    def test_total_cells(self, sample_df: pd.DataFrame) -> None:
        """Total cells should equal rows * cols."""
        result = analyze_missing_values(sample_df)
        assert result.total_cells == sample_df.shape[0] * sample_df.shape[1]

    def test_total_missing(self, sample_df: pd.DataFrame) -> None:
        """Total missing should match DataFrame."""
        result = analyze_missing_values(sample_df)
        expected = int(sample_df.isnull().sum().sum())
        assert result.total_missing == expected

    def test_overall_missing_pct(self, sample_df: pd.DataFrame) -> None:
        """Missing percentage should be calculated correctly."""
        result = analyze_missing_values(sample_df)
        expected_pct = round(result.total_missing / result.total_cells * 100, 2)
        assert result.overall_missing_pct == expected_pct

    def test_columns_with_missing(self, sample_df: pd.DataFrame) -> None:
        """Should identify columns with missing values."""
        result = analyze_missing_values(sample_df)
        cols_with_missing = [
            col for col, info in result.columns.items() if info.has_missing
        ]
        assert len(cols_with_missing) > 0

    def test_recommended_actions(self, sample_df: pd.DataFrame) -> None:
        """Should provide recommended actions."""
        result = analyze_missing_values(sample_df)
        assert len(result.recommended_actions) > 0

    def test_no_missing_values(self, minimal_df: pd.DataFrame) -> None:
        """Should handle DataFrame with no missing values."""
        result = analyze_missing_values(minimal_df)
        assert result.total_missing == 0
        assert result.overall_missing_pct == 0.0

    def test_column_missing_info(self, sample_df: pd.DataFrame) -> None:
        """ColumnMissingInfo should have correct attributes."""
        result = analyze_missing_values(sample_df)
        for col, info in result.columns.items():
            assert isinstance(info, ColumnMissingInfo)
            assert info.column == col
            assert info.null_count + info.non_null_count == sample_df.shape[0]


class TestAnalyzeNumericColumns:
    """Tests for analyze_numeric_columns function."""

    def test_returns_numeric_analysis(self, sample_df: pd.DataFrame) -> None:
        """Should return NumericAnalysis."""
        result = analyze_numeric_columns(sample_df)
        assert isinstance(result, NumericAnalysis)

    def test_identifies_numeric_columns(self, sample_df: pd.DataFrame) -> None:
        """Should identify numeric columns."""
        result = analyze_numeric_columns(sample_df)
        assert "age" in result.columns or "salary" in result.columns

    def test_numeric_stats(self, sample_df: pd.DataFrame) -> None:
        """NumericColumnStats should have valid statistics."""
        result = analyze_numeric_columns(sample_df)
        for col, stats in result.columns.items():
            assert isinstance(stats, NumericColumnStats)
            assert stats.column == col
            assert stats.count > 0
            assert stats.min <= stats.max
            assert stats.q25 <= stats.q75

    def test_highly_skewed(self, sample_df: pd.DataFrame) -> None:
        """Should identify highly skewed columns."""
        result = analyze_numeric_columns(sample_df)
        assert isinstance(result.highly_skewed, list)

    def test_columns_with_outliers(self, sample_df: pd.DataFrame) -> None:
        """Should identify columns with outliers."""
        result = analyze_numeric_columns(sample_df)
        assert isinstance(result.columns_with_outliers, list)


class TestAnalyzeCategoricalColumns:
    """Tests for analyze_categorical_columns function."""

    def test_returns_categorical_analysis(self, sample_df: pd.DataFrame) -> None:
        """Should return CategoricalAnalysis."""
        result = analyze_categorical_columns(sample_df)
        assert isinstance(result, CategoricalAnalysis)

    def test_identifies_categorical_columns(self, sample_df: pd.DataFrame) -> None:
        """Should identify categorical columns."""
        result = analyze_categorical_columns(sample_df)
        assert "department" in result.columns or "name" in result.columns

    def test_categorical_stats(self, sample_df: pd.DataFrame) -> None:
        """CategoricalColumnStats should have valid statistics."""
        result = analyze_categorical_columns(sample_df)
        for col, stats in result.columns.items():
            assert isinstance(stats, CategoricalColumnStats)
            assert stats.column == col
            assert stats.count > 0
            assert stats.unique_count > 0

    def test_high_cardinality(self, high_cardinality_df: pd.DataFrame) -> None:
        """Should identify high cardinality columns."""
        result = analyze_categorical_columns(high_cardinality_df)
        assert len(result.high_cardinality_columns) > 0


class TestGenerateFeatureSummaries:
    """Tests for generate_feature_summaries function."""

    def test_returns_feature_summaries(self, sample_df: pd.DataFrame) -> None:
        """Should return list of FeatureSummary."""
        result = generate_feature_summaries(sample_df)
        assert isinstance(result, list)
        assert all(isinstance(fs, FeatureSummary) for fs in result)

    def test_summary_count(self, sample_df: pd.DataFrame) -> None:
        """Should have summary for each column."""
        result = generate_feature_summaries(sample_df)
        assert len(result) == len(sample_df.columns)

    def test_summary_fields(self, sample_df: pd.DataFrame) -> None:
        """FeatureSummary should have required fields."""
        result = generate_feature_summaries(sample_df)
        for fs in result:
            assert fs.column != ""
            assert fs.dtype != ""
            assert fs.semantic_type in [
                "numeric",
                "categorical",
                "datetime",
                "boolean",
                "other",
            ]
            assert 0 <= fs.null_pct <= 100

    def test_numeric_summary(self, sample_df: pd.DataFrame) -> None:
        """Numeric columns should have mean/median/std."""
        result = generate_feature_summaries(sample_df)
        numeric_summaries = [fs for fs in result if fs.semantic_type == "numeric"]
        for fs in numeric_summaries:
            assert "mean" in fs.summary
            assert "median" in fs.summary
            assert "std" in fs.summary

    def test_categorical_summary(self, sample_df: pd.DataFrame) -> None:
        """Categorical columns should have mode/unique_count."""
        result = generate_feature_summaries(sample_df)
        cat_summaries = [fs for fs in result if fs.semantic_type == "categorical"]
        for fs in cat_summaries:
            assert "mode" in fs.summary
            assert "unique_count" in fs.summary
