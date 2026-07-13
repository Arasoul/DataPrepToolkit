"""Tests for reporter module."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from datapreptoolkit import (
    EncodingRecommendation,
    EncodingStrategy,
    QualityReport,
    ToolkitConfig,
    export_csv_summary,
    export_html_report,
    generate_encoding_recommendations,
    generate_quality_report,
)


class TestGenerateQualityReport:
    """Tests for generate_quality_report function."""

    def test_returns_quality_report(self, sample_df: pd.DataFrame) -> None:
        """Should return QualityReport."""
        report = generate_quality_report(sample_df)
        assert isinstance(report, QualityReport)

    def test_report_shape(self, sample_df: pd.DataFrame) -> None:
        """Report shape should match DataFrame shape."""
        report = generate_quality_report(sample_df)
        assert report.shape == sample_df.shape

    def test_report_memory(self, sample_df: pd.DataFrame) -> None:
        """Report should have memory info."""
        report = generate_quality_report(sample_df)
        assert report.memory_human != ""

    def test_quality_score(self, sample_df: pd.DataFrame) -> None:
        """Quality score should be between 0 and 100."""
        report = generate_quality_report(sample_df)
        assert 0 <= report.overall_quality_score <= 100

    def test_report_sections(self, sample_df: pd.DataFrame) -> None:
        """Report should have all sections populated."""
        report = generate_quality_report(sample_df)
        assert report.profile is not None
        assert report.missing is not None
        assert report.numeric is not None
        assert report.categorical is not None
        assert report.feature_summaries is not None
        assert report.encoding_recommendations is not None
        assert report.cleaning_recommendations is not None

    def test_custom_config(self, sample_df: pd.DataFrame) -> None:
        """Should accept custom config."""
        config = ToolkitConfig(
            quality_weights={
                "missing": 50.0,
                "duplicate": 30.0,
                "constant": 5.0,
                "high_cardinality": 2.0,
                "outlier": 4.0,
            }
        )
        report = generate_quality_report(sample_df, config)
        assert isinstance(report, QualityReport)

    def test_disabled_outliers(self, sample_df: pd.DataFrame) -> None:
        """Should handle disabled outlier detection."""
        config = ToolkitConfig(detect_outliers=False)
        report = generate_quality_report(sample_df, config)
        assert report.outliers is None


class TestGenerateEncodingRecommendations:
    """Tests for generate_encoding_recommendations function."""

    def test_returns_encoding_recommendations(self, sample_df: pd.DataFrame) -> None:
        """Should return list of EncodingRecommendation."""
        recs = generate_encoding_recommendations(sample_df)
        assert isinstance(recs, list)
        assert all(isinstance(r, EncodingRecommendation) for r in recs)

    def test_categorical_columns_only(self, sample_df: pd.DataFrame) -> None:
        """Should only recommend for categorical columns."""
        recs = generate_encoding_recommendations(sample_df)
        for rec in recs:
            assert (
                sample_df[rec.column].dtype == object
                or sample_df[rec.column].dtype.name == "category"
            )

    def test_encoding_strategies(self, sample_df: pd.DataFrame) -> None:
        """Should use valid encoding strategies."""
        recs = generate_encoding_recommendations(sample_df)
        valid_strategies = {"label", "one_hot", "frequency", "none"}
        for rec in recs:
            assert rec.strategy in valid_strategies

    def test_no_encoding_strategy(self, sample_df: pd.DataFrame) -> None:
        """Should respect NONE encoding strategy."""
        config = ToolkitConfig(encoding_strategy=EncodingStrategy.NONE)
        recs = generate_encoding_recommendations(sample_df, config)
        for rec in recs:
            assert rec.strategy == "none"


class TestExportHTMLReport:
    """Tests for export_html_report function."""

    def test_exports_html(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        """Should export HTML report."""
        report = generate_quality_report(sample_df)
        filepath = tmp_path / "report.html"
        result = export_html_report(report, filepath)
        assert Path(result).exists()
        assert Path(result).suffix == ".html"

    def test_html_content(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        """HTML should contain expected content."""
        report = generate_quality_report(sample_df)
        filepath = tmp_path / "report.html"
        result = export_html_report(report, filepath)
        content = Path(result).read_text(encoding="utf-8")
        assert "Data Quality Report" in content
        assert "DataPrepToolkit" in content

    def test_default_path(self, sample_df: pd.DataFrame) -> None:
        """Should use default path when not specified."""
        report = generate_quality_report(sample_df)
        result = export_html_report(report)
        assert Path(result).exists()


class TestExportCSVSummary:
    """Tests for export_csv_summary function."""

    def test_exports_csv(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        """Should export CSV summary."""
        report = generate_quality_report(sample_df)
        filepath = tmp_path / "summary.csv"
        result = export_csv_summary(report, filepath)
        assert Path(result).exists()
        assert Path(result).suffix == ".csv"

    def test_csv_content(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        """CSV should have correct columns."""
        report = generate_quality_report(sample_df)
        filepath = tmp_path / "summary.csv"
        result = export_csv_summary(report, filepath)
        df = pd.read_csv(result)
        assert "column" in df.columns
        assert "dtype" in df.columns
        assert "null_pct" in df.columns


class TestQualityReport:
    """Tests for QualityReport dataclass."""

    def test_report_fields(self, sample_df: pd.DataFrame) -> None:
        """QualityReport should have required fields."""
        report = generate_quality_report(sample_df)
        assert hasattr(report, "shape")
        assert hasattr(report, "memory_human")
        assert hasattr(report, "overall_quality_score")
        assert hasattr(report, "profile")
        assert hasattr(report, "missing")
        assert hasattr(report, "numeric")
        assert hasattr(report, "categorical")
        assert hasattr(report, "outliers")
        assert hasattr(report, "feature_summaries")
        assert hasattr(report, "encoding_recommendations")
        assert hasattr(report, "cleaning_recommendations")
