"""Tests for outliers module."""

from __future__ import annotations

import pandas as pd

from datapreptoolkit import (
    ColumnOutlierInfo,
    OutlierDetection,
    ToolkitConfig,
    ZScoreMethod,
    detect_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
)


class TestDetectOutliersIQR:
    """Tests for detect_outliers_iqr function."""

    def test_returns_outlier_detection(self, sample_df: pd.DataFrame) -> None:
        """Should return OutlierDetection."""
        result = detect_outliers_iqr(sample_df)
        assert isinstance(result, OutlierDetection)

    def test_outlier_mask(self, sample_df: pd.DataFrame) -> None:
        """Should return boolean outlier mask as DataFrame."""
        result = detect_outliers_iqr(sample_df)
        assert isinstance(result.outlier_mask, pd.DataFrame)

    def test_columns_with_outliers(self, sample_df: pd.DataFrame) -> None:
        """Should identify columns with outliers."""
        result = detect_outliers_iqr(sample_df)
        assert isinstance(result.columns_with_outliers, list)

    def test_column_outlier_info(self, sample_df: pd.DataFrame) -> None:
        """ColumnOutlierInfo should have valid fields."""
        result = detect_outliers_iqr(sample_df)
        for col, info in result.columns.items():
            assert isinstance(info, ColumnOutlierInfo)
            assert info.column == col
            assert info.outlier_count >= 0
            assert info.outlier_pct >= 0
            assert info.lower_bound <= info.upper_bound


class TestDetectOutliersZScore:
    """Tests for detect_outliers_zscore function."""

    def test_returns_outlier_detection(self, sample_df: pd.DataFrame) -> None:
        """Should return OutlierDetection."""
        result = detect_outliers_zscore(sample_df)
        assert isinstance(result, OutlierDetection)

    def test_standard_method(self, sample_df: pd.DataFrame) -> None:
        """Should work with standard z-score method."""
        result = detect_outliers_zscore(sample_df, method=ZScoreMethod.STANDARD)
        assert isinstance(result, OutlierDetection)

    def test_modified_method(self, sample_df: pd.DataFrame) -> None:
        """Should work with modified z-score method."""
        result = detect_outliers_zscore(sample_df, method=ZScoreMethod.MODIFIED)
        assert isinstance(result, OutlierDetection)


class TestDetectOutliers:
    """Tests for detect_outliers dispatcher function."""

    def test_iqr_method(self, sample_df: pd.DataFrame) -> None:
        """Should use IQR method."""
        config = ToolkitConfig(outlier_method="iqr")
        result = detect_outliers(sample_df, config=config)
        assert isinstance(result, OutlierDetection)

    def test_zscore_method(self, sample_df: pd.DataFrame) -> None:
        """Should use z-score method."""
        config = ToolkitConfig(outlier_method="zscore")
        result = detect_outliers(sample_df, config=config)
        assert isinstance(result, OutlierDetection)

    def test_disabled_detection(self, sample_df: pd.DataFrame) -> None:
        """Should still return OutlierDetection (detection is always performed)."""
        config = ToolkitConfig(detect_outliers=False)
        result = detect_outliers(sample_df, config=config)
        assert isinstance(result, OutlierDetection)


class TestOutlierDetection:
    """Tests for OutlierDetection dataclass."""

    def test_outlier_detection_fields(self, sample_df: pd.DataFrame) -> None:
        """OutlierDetection should have required fields."""
        result = detect_outliers_iqr(sample_df)
        assert hasattr(result, "method")
        assert hasattr(result, "total_outliers")
        assert hasattr(result, "columns")
        assert hasattr(result, "columns_with_outliers")
        assert hasattr(result, "outlier_mask")
