"""Integration tests for the full DataPrepToolkit pipeline.

These tests exercise the complete workflow from data loading through
cleaning, analysis, validation, optimization, outlier detection, and
reporting to verify that modules compose correctly.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from datapreptoolkit import (
    CleaningResult,
    DatasetProfile,
    OptimizationResult,
    OutlierDetection,
    QualityReport,
    ToolkitConfig,
    ValidationResult,
    ValidationRule,
    clean_dataset,
    detect_outliers,
    export_csv_summary,
    export_html_report,
    generate_quality_report,
    load_csv,
    optimise_memory,
    profile_dataset,
    validate_dataset,
)


class TestFullPipeline:
    """End-to-end integration tests for the complete preprocessing pipeline."""

    def test_load_clean_optimize_report(
        self, sample_df: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Full pipeline: profile -> clean -> optimize -> detect -> report."""
        config = ToolkitConfig(
            remove_duplicates=False,
            optimise_memory=True,
            detect_outliers=True,
            generate_html_report=True,
            report_dir=tmp_path,
        )

        # Step 1: Profile
        profile = profile_dataset(sample_df, config)
        assert isinstance(profile, DatasetProfile)
        assert profile.shape == sample_df.shape
        assert profile.memory_bytes > 0

        # Step 2: Validate
        rules = [
            ValidationRule(column="age", rule_type="range", min_value=0, max_value=120),
            ValidationRule(column="id", rule_type="no_duplicates"),
        ]
        val_result = validate_dataset(sample_df, rules)
        assert isinstance(val_result, ValidationResult)
        assert val_result.total_rules == 2

        # Step 3: Clean
        cleaned, clean_result = clean_dataset(sample_df, config)
        assert isinstance(clean_result, CleaningResult)
        assert isinstance(cleaned, pd.DataFrame)
        # After cleaning, no NaN values should remain in numeric/categorical cols
        assert cleaned.isnull().sum().sum() == 0

        # Step 4: Optimize
        optimized, opt_result = optimise_memory(cleaned, config)
        assert isinstance(opt_result, OptimizationResult)
        assert opt_result.memory_before > 0
        assert opt_result.memory_after > 0

        # Step 5: Detect outliers
        outlier_result = detect_outliers(optimized, config=config)
        assert isinstance(outlier_result, OutlierDetection)

        # Step 6: Generate report
        report = generate_quality_report(sample_df, config)
        assert isinstance(report, QualityReport)
        assert report.overall_quality_score >= 0
        assert report.overall_quality_score <= 100
        assert report.profile is not None
        assert report.missing is not None

    def test_report_export_roundtrip(
        self, sample_df: pd.DataFrame, tmp_path: Path
    ) -> None:
        """Generate report and export to both HTML and CSV."""
        config = ToolkitConfig(
            detect_outliers=True,
            generate_html_report=True,
            report_dir=tmp_path,
        )

        report = generate_quality_report(sample_df, config)

        # HTML export
        html_path = tmp_path / "report.html"
        result_path = export_html_report(report, html_path, config)
        assert Path(result_path).exists()
        content = Path(result_path).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "Data Quality Report" in content

        # CSV export
        csv_path = tmp_path / "summary.csv"
        csv_result = export_csv_summary(report, csv_path, config)
        assert Path(csv_result).exists()

    def test_csv_load_to_report(self, sample_df: pd.DataFrame, tmp_path: Path) -> None:
        """Load CSV file, then run full analysis and report."""
        # Write sample data to CSV
        csv_path = tmp_path / "test_data.csv"
        sample_df.to_csv(csv_path, index=False)

        # Load from CSV
        loaded = load_csv(csv_path)
        assert loaded.shape == sample_df.shape

        # Generate report
        report = generate_quality_report(loaded)
        assert report.overall_quality_score >= 0
        assert len(report.feature_summaries) == len(sample_df.columns)

    def test_cleaning_preserves_data_integrity(self, sample_df: pd.DataFrame) -> None:
        """Verify cleaning produces valid output without corrupting data."""
        original_shape = sample_df.shape
        original_cols = set(sample_df.columns)

        cleaned, result = clean_dataset(sample_df)

        # Shape should be valid
        assert cleaned.shape[0] <= original_shape[0]
        assert cleaned.shape[1] <= original_shape[1]

        # No new columns should appear
        assert set(cleaned.columns).issubset(original_cols)

        # Result should track what happened
        assert result.rows_before == original_shape[0]
        assert result.cols_before == original_shape[1]
        assert result.rows_after == cleaned.shape[0]

    def test_pipeline_with_edge_cases(self, tmp_path: Path) -> None:
        """Pipeline should handle a DataFrame with many quality issues."""
        np.random.seed(99)
        n = 50
        # Create rows with full-row duplicates
        base_data = {
            "id": list(range(1, n + 1)),
            "value": np.random.uniform(0, 100, n),
            "category": np.random.choice(["A", "B"], n),
            "sparse_col": [np.nan] * 45 + list(range(5)),
            "all_same": ["X"] * n,
        }
        base_df = pd.DataFrame(base_data)
        # Append 3 duplicate rows (same values in all columns)
        dup_rows = base_df.iloc[[0, 1, 2]].copy()
        df = pd.concat([base_df, dup_rows], ignore_index=True)

        config = ToolkitConfig(
            remove_duplicates=True,
            detect_outliers=True,
            optimise_memory=True,
        )

        # Should not raise
        cleaned, clean_result = clean_dataset(df, config)
        assert cleaned is not None
        assert clean_result.duplicates_dropped > 0

        profile = profile_dataset(cleaned)
        assert profile.shape == cleaned.shape

        report = generate_quality_report(cleaned, config)
        assert 0 <= report.overall_quality_score <= 100
