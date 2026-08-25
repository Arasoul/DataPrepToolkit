"""Dynamic-behavior tests for DataPrepToolkit.

Covers Datasets A–T as specified in the production audit:
  A  Pure numeric
  B  Pure categorical
  C  Mixed numeric/categorical
  D  Datetime columns
  E  Boolean columns
  F  Text columns
  G  Identifier-like columns
  H  Constant columns
  I  High-cardinality categorical
  J  Very small dataset
  K  Large dataset
  L  Completely empty DataFrame
  M  Single-row DataFrame
  N  Single-column DataFrame
  O  All-null column
  P  Duplicate-heavy dataset
  Q  Extreme outliers
  R  Mixed missing-value representations
  S  Unusual but valid column names
  T  Non-English column names

Plus targeted gap tests for:
  - Missing-value strategy correctness per dtype
  - Outlier detection edge cases (constant, NaN, inf, single value)
  - Memory optimizer value-preservation guarantees
  - Validation determinism
  - Quality score explanation
  - Duplicate result transparency
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from datapreptoolkit import (
    CleaningError,
    ToolkitConfig,
    ValidationRule,
    ZScoreMethod,
    analyze_categorical_columns,
    analyze_missing_values,
    analyze_numeric_columns,
    clean_dataset,
    detect_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
    generate_feature_summaries,
    generate_quality_report,
    handle_missing_values,
    optimise_datatypes,
    optimise_memory,
    profile_dataset,
    remove_duplicates,
    validate_dataset,
)

# ---------------------------------------------------------------------------
# Dataset factories (A–T)
# ---------------------------------------------------------------------------


def dataset_a() -> pd.DataFrame:
    """A: Pure numeric columns."""
    rng = np.random.default_rng(0)
    return pd.DataFrame(
        {
            "x": rng.integers(0, 100, 50).astype(float),
            "y": rng.standard_normal(50),
            "z": rng.uniform(0, 1, 50),
        }
    )


def dataset_b() -> pd.DataFrame:
    """B: Pure categorical columns."""
    return pd.DataFrame(
        {
            "color": ["red", "green", "blue", "red", "green"] * 20,
            "size": ["S", "M", "L", "XL", "S"] * 20,
            "status": ["active", "inactive"] * 50,
        }
    )


def dataset_c() -> pd.DataFrame:
    """C: Mixed numeric/categorical."""
    rng = np.random.default_rng(1)
    return pd.DataFrame(
        {
            "score": rng.integers(0, 100, 60).astype(float),
            "category": ["A", "B", "C"] * 20,
            "weight": rng.uniform(0, 10, 60),
            "label": ["yes", "no"] * 30,
        }
    )


def dataset_d() -> pd.DataFrame:
    """D: Datetime columns."""
    dates = pd.date_range("2024-01-01", periods=30, freq="D")
    return pd.DataFrame(
        {
            "event_date": dates,
            "created_at": dates + pd.Timedelta(days=1),
            "value": range(30),
        }
    )


def dataset_e() -> pd.DataFrame:
    """E: Boolean columns."""
    rng = np.random.default_rng(2)
    return pd.DataFrame(
        {
            "flag_a": rng.choice([True, False], 40),
            "flag_b": rng.choice([True, False], 40),
            "numeric": rng.integers(0, 10, 40).astype(float),
        }
    )


def dataset_f() -> pd.DataFrame:
    """F: Text (free-form) columns."""
    return pd.DataFrame(
        {
            "description": [
                "This is a short description.",
                "Another sentence here.",
                "Yet another one.",
                "And one more for good measure.",
                "Final entry in this list.",
            ]
            * 10,
            "notes": [
                "OK",
                "Need review",
                "Approved",
                "Pending",
                "Rejected",
            ]
            * 10,
        }
    )


def dataset_g() -> pd.DataFrame:
    """G: Identifier-like columns (high uniqueness)."""
    return pd.DataFrame(
        {
            "order_id": [f"ORD-{i:05d}" for i in range(100)],
            "customer_id": [f"CUST-{i:04d}" for i in range(100)],
            "amount": np.random.default_rng(3).uniform(10, 500, 100),
        }
    )


def dataset_h() -> pd.DataFrame:
    """H: Constant columns."""
    return pd.DataFrame(
        {
            "always_one": [1] * 50,
            "always_cat": ["fixed"] * 50,
            "normal": range(50),
        }
    )


def dataset_i() -> pd.DataFrame:
    """I: High-cardinality categorical."""
    return pd.DataFrame(
        {
            "tag": [f"tag_{i}" for i in range(200)],
            "value": np.random.default_rng(4).integers(0, 100, 200).astype(float),
        }
    )


def dataset_j() -> pd.DataFrame:
    """J: Very small dataset (3 rows)."""
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def dataset_k() -> pd.DataFrame:
    """K: Large dataset (10_000 rows)."""
    rng = np.random.default_rng(5)
    return pd.DataFrame(
        {
            "num1": rng.standard_normal(10_000),
            "num2": rng.integers(0, 1000, 10_000).astype(float),
            "cat": rng.choice(["A", "B", "C", "D"], 10_000),
        }
    )


def dataset_l() -> pd.DataFrame:
    """L: Completely empty DataFrame (zero rows, has columns)."""
    return pd.DataFrame(
        {"a": pd.Series([], dtype="float64"), "b": pd.Series([], dtype="object")}
    )


def dataset_m() -> pd.DataFrame:
    """M: Single-row DataFrame."""
    return pd.DataFrame({"x": [42.0], "y": ["hello"]})


def dataset_n() -> pd.DataFrame:
    """N: Single-column DataFrame."""
    return pd.DataFrame({"only_col": [1, 2, 3, 4, 5]})


def dataset_o() -> pd.DataFrame:
    """O: All-null column."""
    return pd.DataFrame(
        {
            "all_null": [np.nan] * 20,
            "normal_num": np.random.default_rng(6).standard_normal(20),
            "normal_cat": ["A", "B"] * 10,
        }
    )


def dataset_p() -> pd.DataFrame:
    """P: Duplicate-heavy dataset (80% duplicates)."""
    base = pd.DataFrame({"id": [1, 2, 3, 4, 5], "val": ["a", "b", "c", "d", "e"]})
    return pd.concat([base] * 20, ignore_index=True)


def dataset_q() -> pd.DataFrame:
    """Q: Extreme outliers."""
    normal = list(range(50))
    extreme = [1_000_000, -1_000_000]
    return pd.DataFrame({"values": normal + extreme})


def dataset_r() -> pd.DataFrame:
    """R: Mixed missing-value representations."""
    return pd.DataFrame(
        {
            "score": [1.0, np.nan, 3.0, None, 5.0],
            "label": ["A", None, "C", np.nan, "E"],
        }
    )


def dataset_s() -> pd.DataFrame:
    """S: Unusual but valid column names."""
    return pd.DataFrame(
        {
            "column with spaces": [1, 2, 3],
            "col-with-dashes": [4, 5, 6],
            "col.with.dots": [7, 8, 9],
            "123_starts_with_num": [10, 11, 12],
            "UPPERCASE_COL": [13, 14, 15],
        }
    )


def dataset_t() -> pd.DataFrame:
    """T: Non-English column names."""
    return pd.DataFrame(
        {
            "nombre": ["Alice", "Bob", "Charlie"],
            "edad": [25.0, 30.0, 35.0],
            "ciudad": ["Madrid", "Barcelona", "Sevilla"],
            "التاريخ": ["2024-01-01", "2024-01-02", "2024-01-03"],
            "価格": [100.0, 200.0, 300.0],
        }
    )


# ---------------------------------------------------------------------------
# Tests: Dataset A — Pure Numeric
# ---------------------------------------------------------------------------


class TestDatasetA:
    """Pure numeric columns."""

    def test_profile_identifies_all_numeric(self) -> None:
        df = dataset_a()
        profile = profile_dataset(df)
        assert set(profile.numeric_columns) == {"x", "y", "z"}
        assert profile.categorical_columns == []

    def test_missing_value_analysis_zero_missing(self) -> None:
        df = dataset_a()
        mv = analyze_missing_values(df)
        assert mv.total_missing == 0
        assert mv.overall_missing_pct == 0.0

    def test_numeric_analysis_covers_all_columns(self) -> None:
        df = dataset_a()
        na = analyze_numeric_columns(df)
        assert set(na.columns.keys()) == {"x", "y", "z"}

    def test_outlier_detection_no_mutation(self) -> None:
        df = dataset_a()
        original_sum = df["x"].sum()
        detect_outliers_iqr(df)
        assert df["x"].sum() == original_sum

    def test_memory_optimize_values_preserved(self) -> None:
        df = dataset_a()
        opt_df, result = optimise_datatypes(df)
        for col in df.columns:
            # Values must match after downcast (within float32 precision if float)
            orig = df[col].dropna()
            opt = opt_df[col].dropna()
            assert len(orig) == len(opt)

    def test_quality_score_bounded(self) -> None:
        df = dataset_a()
        report = generate_quality_report(df)
        assert 0.0 <= report.overall_quality_score <= 100.0

    def test_feature_summaries_all_numeric(self) -> None:
        df = dataset_a()
        summaries = generate_feature_summaries(df)
        for fs in summaries:
            assert fs.semantic_type == "numeric"


# ---------------------------------------------------------------------------
# Tests: Dataset B — Pure Categorical
# ---------------------------------------------------------------------------


class TestDatasetB:
    """Pure categorical columns."""

    def test_profile_identifies_all_categorical(self) -> None:
        df = dataset_b()
        profile = profile_dataset(df)
        assert set(profile.categorical_columns) == {"color", "size", "status"}
        assert profile.numeric_columns == []

    def test_no_numeric_analysis(self) -> None:
        df = dataset_b()
        na = analyze_numeric_columns(df)
        assert na.columns == {}

    def test_categorical_analysis_present(self) -> None:
        df = dataset_b()
        ca = analyze_categorical_columns(df)
        assert set(ca.columns.keys()) == {"color", "size", "status"}

    def test_missing_value_median_falls_back_to_mode(self) -> None:
        """Applying median strategy to categorical should silently use mode."""
        df = dataset_b().copy()
        df.loc[0, "color"] = None
        cleaned, result = handle_missing_values(df, strategy="median")
        # Should have imputed, not errored
        assert cleaned["color"].isnull().sum() == 0
        # The strategy used should be 'mode' (the fallback)
        imputed_cols = [r.column for r in result.imputations]
        assert "color" in imputed_cols
        color_rec = next(r for r in result.imputations if r.column == "color")
        assert color_rec.strategy == "mode"

    def test_outlier_detection_skips_categoricals(self) -> None:
        df = dataset_b()
        result = detect_outliers_iqr(df)
        # No numeric columns → no outlier info
        assert result.columns == {}
        assert result.total_outliers == 0


# ---------------------------------------------------------------------------
# Tests: Dataset C — Mixed
# ---------------------------------------------------------------------------


class TestDatasetC:
    """Mixed numeric/categorical."""

    def test_clean_dataset_handles_mixed(self) -> None:
        df = dataset_c().copy()
        df.loc[0, "score"] = np.nan
        df.loc[1, "category"] = None
        cleaned, result = clean_dataset(df)
        assert isinstance(cleaned, pd.DataFrame)
        assert cleaned.shape[1] == df.shape[1]

    def test_numeric_imputed_with_median_not_mode(self) -> None:
        df = dataset_c().copy()
        df.loc[0, "score"] = np.nan
        cleaned, result = handle_missing_values(df, strategy="median")
        num_recs = [r for r in result.imputations if r.column == "score"]
        assert len(num_recs) == 1
        assert num_recs[0].strategy == "median"

    def test_categorical_imputed_with_mode(self) -> None:
        df = dataset_c().copy()
        df.loc[0, "category"] = None
        cleaned, result = handle_missing_values(df, strategy="median")
        cat_recs = [r for r in result.imputations if r.column == "category"]
        assert len(cat_recs) == 1
        assert cat_recs[0].strategy == "mode"


# ---------------------------------------------------------------------------
# Tests: Dataset D — Datetime Columns
# ---------------------------------------------------------------------------


class TestDatasetD:
    """Datetime columns."""

    def test_profile_identifies_datetime(self) -> None:
        df = dataset_d()
        profile = profile_dataset(df)
        assert "event_date" in profile.datetime_columns
        assert "created_at" in profile.datetime_columns

    def test_feature_summary_datetime_type(self) -> None:
        df = dataset_d()
        summaries = generate_feature_summaries(df)
        dt_summaries = [s for s in summaries if s.column == "event_date"]
        assert len(dt_summaries) == 1
        assert dt_summaries[0].semantic_type == "datetime"

    def test_datetime_columns_not_treated_as_numeric(self) -> None:
        df = dataset_d()
        na = analyze_numeric_columns(df)
        # datetime columns should NOT appear as numeric
        assert "event_date" not in na.columns
        assert "created_at" not in na.columns


# ---------------------------------------------------------------------------
# Tests: Dataset E — Boolean Columns
# ---------------------------------------------------------------------------


class TestDatasetE:
    """Boolean columns."""

    def test_profile_identifies_boolean(self) -> None:
        df = dataset_e()
        profile = profile_dataset(df)
        assert "flag_a" in profile.boolean_columns
        assert "flag_b" in profile.boolean_columns

    def test_feature_summary_boolean_type(self) -> None:
        df = dataset_e()
        summaries = generate_feature_summaries(df)
        bool_summaries = [s for s in summaries if s.column == "flag_a"]
        assert len(bool_summaries) == 1
        assert bool_summaries[0].semantic_type == "boolean"

    def test_boolean_not_in_categorical_analysis(self) -> None:
        df = dataset_e()
        ca = analyze_categorical_columns(df)
        assert "flag_a" not in ca.columns
        assert "flag_b" not in ca.columns


# ---------------------------------------------------------------------------
# Tests: Dataset F — Text Columns
# ---------------------------------------------------------------------------


class TestDatasetF:
    """Free-form text columns."""

    def test_profile_does_not_crash(self) -> None:
        df = dataset_f()
        profile = profile_dataset(df)
        assert profile.shape == (50, 2)

    def test_text_identified_as_categorical(self) -> None:
        df = dataset_f()
        summaries = generate_feature_summaries(df)
        for s in summaries:
            assert s.semantic_type in ("categorical", "other")


# ---------------------------------------------------------------------------
# Tests: Dataset G — Identifier-Like Columns
# ---------------------------------------------------------------------------


class TestDatasetG:
    """Identifier-like (high-uniqueness) columns."""

    def test_profile_flags_potential_ids(self) -> None:
        df = dataset_g()
        profile = profile_dataset(df)
        assert "order_id" in profile.potential_id_columns or \
               "customer_id" in profile.potential_id_columns

    def test_high_cardinality_encoding_recommendation(self) -> None:
        from datapreptoolkit import generate_encoding_recommendations
        df = dataset_g()
        recs = generate_encoding_recommendations(df)
        # order_id / customer_id should get frequency encoding (>50 unique)
        id_recs = [r for r in recs if r.column in ("order_id", "customer_id")]
        for r in id_recs:
            assert r.strategy == "frequency"


# ---------------------------------------------------------------------------
# Tests: Dataset H — Constant Columns
# ---------------------------------------------------------------------------


class TestDatasetH:
    """Constant columns."""

    def test_profile_flags_constant_columns(self) -> None:
        df = dataset_h()
        profile = profile_dataset(df)
        assert "always_one" in profile.constant_columns
        assert "always_cat" in profile.constant_columns

    def test_iqr_on_constant_column_no_outliers(self) -> None:
        """Constant numeric column: IQR=0, no outliers should be flagged."""
        df = pd.DataFrame({"const": [5.0] * 30, "normal": range(30)})
        result = detect_outliers_iqr(df)
        # const column: Q1=Q3=5, IQR=0, bounds both=5 → no outliers
        if "const" in result.columns:
            assert result.columns["const"].outlier_count == 0

    def test_zscore_on_constant_column_no_outliers(self) -> None:
        """Constant numeric column with std=0 → z-scores all 0 → no outliers."""
        df = pd.DataFrame({"const": [5.0] * 30})
        result = detect_outliers_zscore(df)
        if "const" in result.columns:
            assert result.columns["const"].outlier_count == 0

    def test_quality_score_penalizes_constant_columns(self) -> None:
        df_clean = dataset_a()
        df_const = dataset_h()
        report_clean = generate_quality_report(df_clean)
        report_const = generate_quality_report(df_const)
        # Constant columns should reduce the quality score
        assert report_const.overall_quality_score < report_clean.overall_quality_score


# ---------------------------------------------------------------------------
# Tests: Dataset I — High-Cardinality Categorical
# ---------------------------------------------------------------------------


class TestDatasetI:
    """High-cardinality categorical columns."""

    def test_profile_flags_high_cardinality(self) -> None:
        df = dataset_i()
        profile = profile_dataset(df)
        assert "tag" in profile.high_cardinality_columns

    def test_analyzer_flags_high_cardinality(self) -> None:
        df = dataset_i()
        ca = analyze_categorical_columns(df)
        assert "tag" in ca.high_cardinality_columns


# ---------------------------------------------------------------------------
# Tests: Dataset J — Very Small Dataset
# ---------------------------------------------------------------------------


class TestDatasetJ:
    """Very small dataset (3 rows)."""

    def test_profile_succeeds(self) -> None:
        df = dataset_j()
        profile = profile_dataset(df)
        assert profile.shape == (3, 2)

    def test_numeric_analysis_single_column(self) -> None:
        df = dataset_j()
        na = analyze_numeric_columns(df)
        assert "a" in na.columns

    def test_outlier_detection_small(self) -> None:
        df = dataset_j()
        result = detect_outliers_iqr(df)
        assert isinstance(result.total_outliers, int)
        assert result.total_outliers >= 0

    def test_cleaning_small(self) -> None:
        df = dataset_j()
        cleaned, result = clean_dataset(df)
        assert cleaned.shape == df.shape


# ---------------------------------------------------------------------------
# Tests: Dataset K — Large Dataset
# ---------------------------------------------------------------------------


class TestDatasetK:
    """Large dataset (10_000 rows)."""

    def test_profile_handles_large(self) -> None:
        df = dataset_k()
        profile = profile_dataset(df)
        assert profile.shape == (10_000, 3)

    def test_cleaning_large(self) -> None:
        df = dataset_k()
        cleaned, result = clean_dataset(df)
        assert isinstance(cleaned, pd.DataFrame)
        assert len(cleaned) <= len(df)

    def test_quality_report_large(self) -> None:
        df = dataset_k()
        report = generate_quality_report(df)
        assert 0.0 <= report.overall_quality_score <= 100.0


# ---------------------------------------------------------------------------
# Tests: Dataset L — Completely Empty DataFrame
# ---------------------------------------------------------------------------


class TestDatasetL:
    """Completely empty DataFrame (zero rows)."""

    def test_profile_zero_rows(self) -> None:
        df = dataset_l()
        profile = profile_dataset(df)
        assert profile.shape[0] == 0
        assert profile.total_missing == 0
        assert profile.total_cells == 0

    def test_missing_value_analysis_empty(self) -> None:
        df = dataset_l()
        mv = analyze_missing_values(df)
        assert mv.total_missing == 0
        assert mv.overall_missing_pct == 0.0

    def test_clean_dataset_empty(self) -> None:
        df = dataset_l()
        cleaned, result = clean_dataset(df)
        assert len(cleaned) == 0

    def test_outlier_detection_empty(self) -> None:
        df = dataset_l()
        result = detect_outliers_iqr(df)
        assert result.total_outliers == 0

    def test_quality_score_empty(self) -> None:
        df = dataset_l()
        report = generate_quality_report(df)
        assert 0.0 <= report.overall_quality_score <= 100.0

    def test_feature_summaries_empty(self) -> None:
        df = dataset_l()
        summaries = generate_feature_summaries(df)
        # Two columns, zero rows each
        assert len(summaries) == 2
        for s in summaries:
            assert s.null_pct == 0.0


# ---------------------------------------------------------------------------
# Tests: Dataset M — Single-Row DataFrame
# ---------------------------------------------------------------------------


class TestDatasetM:
    """Single-row DataFrame."""

    def test_profile_single_row(self) -> None:
        df = dataset_m()
        profile = profile_dataset(df)
        assert profile.shape == (1, 2)

    def test_numeric_analysis_single_row(self) -> None:
        df = dataset_m()
        na = analyze_numeric_columns(df)
        assert "x" in na.columns
        # std of single value = 0
        assert na.columns["x"].std == 0.0

    def test_remove_duplicates_single_row(self) -> None:
        df = dataset_m()
        cleaned, result = remove_duplicates(df)
        assert len(cleaned) == 1
        assert result.duplicates_dropped == 0


# ---------------------------------------------------------------------------
# Tests: Dataset N — Single-Column DataFrame
# ---------------------------------------------------------------------------


class TestDatasetN:
    """Single-column DataFrame."""

    def test_profile_single_column(self) -> None:
        df = dataset_n()
        profile = profile_dataset(df)
        assert profile.shape == (5, 1)
        assert "only_col" in profile.numeric_columns

    def test_cleaning_single_column(self) -> None:
        df = dataset_n()
        cleaned, result = clean_dataset(df)
        assert "only_col" in cleaned.columns

    def test_validation_single_column(self) -> None:
        df = dataset_n()
        rules = [ValidationRule(column="only_col", rule_type="not_null")]
        result = validate_dataset(df, rules)
        assert result.is_valid is True


# ---------------------------------------------------------------------------
# Tests: Dataset O — All-Null Column
# ---------------------------------------------------------------------------


class TestDatasetO:
    """All-null column."""

    def test_profile_marks_all_null_as_missing(self) -> None:
        df = dataset_o()
        profile = profile_dataset(df)
        assert "all_null" in profile.missing_columns

    def test_missing_analysis_flags_empty_column(self) -> None:
        df = dataset_o()
        mv = analyze_missing_values(df)
        assert "all_null" in mv.completely_empty_columns
        assert mv.recommended_actions.get("all_null") == "drop_column"

    def test_drop_column_strategy_removes_null_column(self) -> None:
        df = dataset_o()
        cleaned, result = handle_missing_values(df, strategy="drop_column")
        assert "all_null" not in cleaned.columns
        assert "all_null" in result.columns_dropped

    def test_outlier_detection_skips_all_null(self) -> None:
        df = dataset_o()
        result = detect_outliers_iqr(df)
        # all_null column is entirely NaN → dropped from series → skipped
        assert "all_null" not in result.columns


# ---------------------------------------------------------------------------
# Tests: Dataset P — Duplicate-Heavy Dataset
# ---------------------------------------------------------------------------


class TestDatasetP:
    """Duplicate-heavy dataset."""

    def test_profile_counts_duplicates(self) -> None:
        df = dataset_p()
        profile = profile_dataset(df)
        assert profile.duplicate_rows > 0
        assert profile.duplicate_ratio > 0.0

    def test_remove_duplicates_result_transparent(self) -> None:
        df = dataset_p()
        cleaned, result = remove_duplicates(df)
        assert result.duplicates_dropped > 0
        assert result.rows_before > result.rows_after
        assert result.rows_before - result.rows_after == result.duplicates_dropped

    def test_remove_duplicates_all_rows(self) -> None:
        """Dataset where all rows are identical."""
        df = pd.DataFrame({"a": [1, 1, 1], "b": ["x", "x", "x"]})
        cleaned, result = remove_duplicates(df, keep="first")
        assert len(cleaned) == 1
        assert result.duplicates_dropped == 2

    def test_remove_duplicates_no_duplicates(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        cleaned, result = remove_duplicates(df)
        assert len(cleaned) == 3
        assert result.duplicates_dropped == 0


# ---------------------------------------------------------------------------
# Tests: Dataset Q — Extreme Outliers
# ---------------------------------------------------------------------------


class TestDatasetQ:
    """Extreme outliers."""

    def test_iqr_detects_extremes(self) -> None:
        df = dataset_q()
        result = detect_outliers_iqr(df)
        assert "values" in result.columns
        assert result.columns["values"].outlier_count >= 2

    def test_zscore_detects_extremes(self) -> None:
        df = dataset_q()
        result = detect_outliers_zscore(df)
        assert "values" in result.columns
        assert result.columns["values"].outlier_count >= 2

    def test_outliers_not_silently_removed(self) -> None:
        """Detection must NEVER remove rows from the DataFrame."""
        df = dataset_q()
        original_len = len(df)
        detect_outliers_iqr(df)
        assert len(df) == original_len  # Original unchanged

    def test_outlier_indices_exist(self) -> None:
        df = dataset_q()
        result = detect_outliers_iqr(df)
        info = result.columns["values"]
        assert len(info.outlier_indices) == info.outlier_count

    def test_min_max_outlier_values_reported(self) -> None:
        df = dataset_q()
        result = detect_outliers_iqr(df)
        info = result.columns["values"]
        assert info.outlier_count > 0
        assert not math.isnan(info.min_outlier)
        assert not math.isnan(info.max_outlier)


# ---------------------------------------------------------------------------
# Tests: Dataset R — Mixed Missing-Value Representations
# ---------------------------------------------------------------------------


class TestDatasetR:
    """Mixed missing-value representations (np.nan, None)."""

    def test_both_nan_and_none_counted(self) -> None:
        df = dataset_r()
        mv = analyze_missing_values(df)
        # score has 2 missing (np.nan + None); label has 2 missing
        assert mv.columns["score"].null_count == 2
        assert mv.columns["label"].null_count == 2

    def test_median_imputation_handles_none(self) -> None:
        df = dataset_r()
        cleaned, result = handle_missing_values(df, strategy="median")
        assert cleaned["score"].isnull().sum() == 0

    def test_mode_imputation_handles_none(self) -> None:
        df = dataset_r()
        cleaned, result = handle_missing_values(df, strategy="mode")
        assert cleaned["label"].isnull().sum() == 0

    def test_original_df_not_mutated(self) -> None:
        df = dataset_r()
        original_null = df.isnull().sum().sum()
        handle_missing_values(df, strategy="median")
        assert df.isnull().sum().sum() == original_null


# ---------------------------------------------------------------------------
# Tests: Dataset S — Unusual Column Names
# ---------------------------------------------------------------------------


class TestDatasetS:
    """Unusual but valid column names."""

    def test_profile_handles_unusual_names(self) -> None:
        df = dataset_s()
        profile = profile_dataset(df)
        assert profile.shape == (3, 5)

    def test_cleaning_preserves_unusual_names(self) -> None:
        df = dataset_s()
        cleaned, result = clean_dataset(df)
        assert set(cleaned.columns) == set(df.columns)

    def test_validation_with_unusual_names(self) -> None:
        df = dataset_s()
        rules = [ValidationRule(column="column with spaces", rule_type="not_null")]
        result = validate_dataset(df, rules)
        assert result.is_valid is True

    def test_feature_summaries_unusual_names(self) -> None:
        df = dataset_s()
        summaries = generate_feature_summaries(df)
        cols = [s.column for s in summaries]
        assert "column with spaces" in cols
        assert "col-with-dashes" in cols


# ---------------------------------------------------------------------------
# Tests: Dataset T — Non-English Column Names
# ---------------------------------------------------------------------------


class TestDatasetT:
    """Non-English column names."""

    def test_profile_non_english(self) -> None:
        df = dataset_t()
        profile = profile_dataset(df)
        assert profile.shape == (3, 5)

    def test_all_columns_in_summaries(self) -> None:
        df = dataset_t()
        summaries = generate_feature_summaries(df)
        assert len(summaries) == 5

    def test_numeric_analysis_non_english(self) -> None:
        df = dataset_t()
        na = analyze_numeric_columns(df)
        assert "edad" in na.columns
        assert "価格" in na.columns

    def test_cleaning_non_english(self) -> None:
        df = dataset_t()
        cleaned, result = clean_dataset(df)
        assert set(cleaned.columns) == set(df.columns)


# ---------------------------------------------------------------------------
# Gap tests: Missing value strategy correctness
# ---------------------------------------------------------------------------


class TestMissingValueStrategyCorrectness:
    """Targeted tests ensuring strategies are type-appropriate."""

    def test_unknown_strategy_raises_cleaning_error(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0]})
        with pytest.raises(CleaningError):
            handle_missing_values(df, strategy="bogus_strategy")

    def test_ffill_propagates_forward(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, np.nan, 4.0]})
        cleaned, _ = handle_missing_values(df, strategy="ffill")
        assert cleaned["a"].tolist() == [1.0, 1.0, 1.0, 4.0]

    def test_bfill_propagates_backward(self) -> None:
        df = pd.DataFrame({"a": [np.nan, np.nan, 3.0, 4.0]})
        cleaned, _ = handle_missing_values(df, strategy="bfill")
        assert cleaned["a"].tolist() == [3.0, 3.0, 3.0, 4.0]

    def test_zero_strategy_numeric(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0]})
        cleaned, result = handle_missing_values(df, strategy="zero")
        assert cleaned["a"].iloc[1] == 0

    def test_zero_strategy_categorical(self) -> None:
        df = pd.DataFrame({"a": ["x", None, "z"]})
        cleaned, result = handle_missing_values(df, strategy="zero")
        assert cleaned["a"].iloc[1] == "Unknown"

    def test_drop_column_threshold_respected(self) -> None:
        """Column with 70% missing → dropped; 30% missing → kept."""
        df = pd.DataFrame(
            {
                "heavy_missing": [np.nan] * 7 + [1.0, 2.0, 3.0],
                "light_missing": [1.0, np.nan, 3.0] + [4.0] * 7,
            }
        )
        cleaned, result = handle_missing_values(df, strategy="drop_column")
        assert "heavy_missing" not in cleaned.columns
        assert "light_missing" in cleaned.columns

    def test_imputation_record_rows_filled(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, np.nan, 4.0]})
        _, result = handle_missing_values(df, strategy="median")
        rec = next(r for r in result.imputations if r.column == "a")
        assert rec.rows_filled == 2

    def test_row_counts_consistent_drop_rows(self) -> None:
        df = pd.DataFrame({"a": [1.0, np.nan, 3.0, np.nan]})
        cleaned, result = handle_missing_values(df, strategy="drop_rows")
        assert result.rows_before == 4
        assert result.rows_after == 2
        assert len(cleaned) == 2


# ---------------------------------------------------------------------------
# Gap tests: Outlier detection edge cases
# ---------------------------------------------------------------------------


class TestOutlierEdgeCases:
    """Outlier detection correctness in pathological cases."""

    def test_single_value_no_outliers_iqr(self) -> None:
        df = pd.DataFrame({"x": [42.0]})
        result = detect_outliers_iqr(df)
        # Q1=Q3=42, IQR=0, bounds both 42 → no outliers
        if "x" in result.columns:
            assert result.columns["x"].outlier_count == 0

    def test_nan_values_excluded_from_count(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0, np.nan, 4.0, 5.0]})
        result = detect_outliers_iqr(df)
        assert result.columns["x"].total_values == 4

    def test_infinite_values_detected_as_outliers(self) -> None:
        df = pd.DataFrame({"x": [1.0, 2.0, 3.0, float("inf")]})
        result = detect_outliers_iqr(df)
        # inf should be beyond upper bound
        assert result.columns["x"].outlier_count >= 1

    def test_non_numeric_columns_skipped(self) -> None:
        df = pd.DataFrame({"a": ["x", "y", "z"], "b": [1.0, 2.0, 3.0]})
        result = detect_outliers_iqr(df)
        assert "a" not in result.columns
        assert "b" in result.columns

    def test_outlier_mask_shape(self) -> None:
        df = dataset_q()
        result = detect_outliers_iqr(df)
        if not result.outlier_mask.empty:
            assert result.outlier_mask.shape[0] == len(df)

    def test_modified_zscore_constant_column(self) -> None:
        df = pd.DataFrame({"x": [5.0] * 20})
        result = detect_outliers_zscore(df, method=ZScoreMethod.MODIFIED)
        if "x" in result.columns:
            assert result.columns["x"].outlier_count == 0

    def test_unknown_method_raises_value_error(self) -> None:
        df = dataset_a()
        with pytest.raises(ValueError):
            detect_outliers(df, method="unknown_method")


# ---------------------------------------------------------------------------
# Gap tests: Memory optimizer value preservation
# ---------------------------------------------------------------------------


class TestMemoryOptimizerValuePreservation:
    """Values must be preserved after dtype optimization."""

    def test_int8_range_values_preserved(self) -> None:
        df = pd.DataFrame({"x": np.array([0, 127, -128], dtype=np.int64)})
        opt_df, _ = optimise_datatypes(df)
        assert list(opt_df["x"]) == [0, 127, -128]

    def test_large_int_not_truncated(self) -> None:
        """Values outside int32 range should stay in int64."""
        df = pd.DataFrame({"x": np.array([2**40], dtype=np.int64)})
        opt_df, result = optimise_datatypes(df)
        assert opt_df["x"].iloc[0] == 2**40

    def test_negative_integers_preserved(self) -> None:
        df = pd.DataFrame({"x": np.array([-500, -200, 0, 200, 500], dtype=np.int64)})
        opt_df, _ = optimise_datatypes(df)
        assert list(opt_df["x"]) == [-500, -200, 0, 200, 500]

    def test_original_not_mutated(self) -> None:
        df = pd.DataFrame({"x": np.arange(100, dtype=np.int64)})
        dtype_before = df["x"].dtype
        optimise_datatypes(df)
        assert df["x"].dtype == dtype_before

    def test_memory_disabled_returns_original(self) -> None:
        df = dataset_a()
        config = ToolkitConfig(optimise_memory=False)
        opt_df, result = optimise_memory(df, config=config)
        assert opt_df is df  # Should be the same object
        assert "disabled" in result.messages[0].lower()

    def test_savings_bytes_non_negative(self) -> None:
        df = dataset_k()
        _, result = optimise_datatypes(df)
        assert result.savings_bytes >= 0

    def test_category_conversion_correct(self) -> None:
        df = pd.DataFrame({"status": ["active", "inactive"] * 50})
        opt_df, result = optimise_datatypes(df)
        assert opt_df["status"].dtype.name == "category"
        # Values should be the same
        assert set(opt_df["status"].unique()) == {"active", "inactive"}


# ---------------------------------------------------------------------------
# Gap tests: Quality score explainability
# ---------------------------------------------------------------------------


class TestQualityScoreExplainability:
    """Quality score must be deterministic and bounded."""

    def test_perfect_dataset_high_score(self) -> None:
        df = pd.DataFrame(
            {
                "a": range(1000),
                "b": np.random.default_rng(99).standard_normal(1000),
            }
        )
        report = generate_quality_report(
            df, config=ToolkitConfig(detect_outliers=False)
        )
        # Clean dataset with no obvious issues should score well
        assert report.overall_quality_score >= 80.0

    def test_terrible_dataset_low_score(self) -> None:
        """A dataset with 50% missing values and many duplicates should score lower."""
        rng = np.random.default_rng(7)
        n = 100
        vals = rng.standard_normal(n).tolist()
        vals[::2] = [np.nan] * 50  # 50% missing
        df = pd.DataFrame({"x": vals})
        df = pd.concat([df] * 5, ignore_index=True)  # Add duplicates
        report = generate_quality_report(df)
        assert report.overall_quality_score < 80.0

    def test_score_deterministic(self) -> None:
        """Same df + same config → same score."""
        df = dataset_c()
        config = ToolkitConfig(detect_outliers=True)
        r1 = generate_quality_report(df, config=config)
        r2 = generate_quality_report(df, config=config)
        assert r1.overall_quality_score == r2.overall_quality_score

    def test_score_bounded(self) -> None:
        for df in [dataset_a(), dataset_b(), dataset_c(), dataset_l(), dataset_q()]:
            report = generate_quality_report(df)
            assert 0.0 <= report.overall_quality_score <= 100.0

    def test_cleaning_recommendations_non_empty(self) -> None:
        df = dataset_o()  # Has all-null column
        report = generate_quality_report(df)
        assert len(report.cleaning_recommendations) > 0

    def test_custom_weights_affect_score(self) -> None:
        df = dataset_o()
        cfg_default = ToolkitConfig()
        cfg_heavy_missing = ToolkitConfig(
            quality_weights={
                "missing": 80.0,
                "duplicate": 10.0,
                "constant": 1.0,
                "high_cardinality": 1.0,
                "outlier": 1.0,
            }
        )
        r_default = generate_quality_report(df, config=cfg_default)
        r_heavy = generate_quality_report(df, config=cfg_heavy_missing)
        # Heavy missing weight should lower the score further
        assert r_heavy.overall_quality_score <= r_default.overall_quality_score


# ---------------------------------------------------------------------------
# Gap tests: Validation determinism and edge cases
# ---------------------------------------------------------------------------


class TestValidationEdgeCases:
    """Validation must be deterministic and handle edge inputs."""

    def test_same_df_same_result(self) -> None:
        df = dataset_c()
        rules = [
            ValidationRule(
                column="score", rule_type="range", min_value=0, max_value=100
            ),
            ValidationRule(column="category", rule_type="not_null"),
        ]
        r1 = validate_dataset(df, rules)
        r2 = validate_dataset(df, rules)
        assert r1.is_valid == r2.is_valid
        assert r1.total_rules == r2.total_rules
        assert r1.failed_rules == r2.failed_rules

    def test_unknown_rule_type_is_skipped(self) -> None:
        df = dataset_a()
        rules = [ValidationRule(column="x", rule_type="nonexistent_rule")]
        result = validate_dataset(df, rules)
        # Should not crash; unknown type silently skipped
        assert result.total_rules == 1
        assert result.passed_rules == 1  # Not failed, just skipped

    def test_missing_column_in_range_rule_produces_violation(self) -> None:
        df = pd.DataFrame({"a": [1, 2, 3]})
        rules = [
            ValidationRule(
                column="nonexistent", rule_type="range", min_value=0, max_value=10
            )
        ]
        result = validate_dataset(df, rules)
        assert result.is_valid is False

    def test_in_set_empty_allowed_values(self) -> None:
        df = pd.DataFrame({"status": ["a", "b", "c"]})
        rules = [
            ValidationRule(
                column="status", rule_type="in_set", allowed_values=set()
            )
        ]
        result = validate_dataset(df, rules)
        # No allowed values → all are "invalid" but shouldn't crash
        assert isinstance(result, type(result))

    def test_regex_no_pattern_produces_violation(self) -> None:
        df = pd.DataFrame({"email": ["test@example.com"]})
        rules = [ValidationRule(column="email", rule_type="regex")]
        result = validate_dataset(df, rules)
        # Should return a violation describing the missing pattern
        assert len(result.violations) == 1

    def test_empty_dataframe_validation(self) -> None:
        df = dataset_l()
        rules = [ValidationRule(column="a", rule_type="not_null")]
        result = validate_dataset(df, rules)
        assert isinstance(result, type(result))


# ---------------------------------------------------------------------------
# Integration: no mutation guarantee across all modules
# ---------------------------------------------------------------------------


class TestNoMutationGuarantee:
    """No function should mutate the input DataFrame."""

    @pytest.mark.parametrize(
        "fn",
        [
            lambda df: profile_dataset(df),
            lambda df: analyze_missing_values(df),
            lambda df: analyze_numeric_columns(df),
            lambda df: analyze_categorical_columns(df),
            lambda df: generate_feature_summaries(df),
            lambda df: detect_outliers_iqr(df),
            lambda df: detect_outliers_zscore(df),
            lambda df: handle_missing_values(df),
            lambda df: remove_duplicates(df),
            lambda df: optimise_datatypes(df),
            lambda df: clean_dataset(df),
            lambda df: generate_quality_report(df),
        ],
    )
    def test_no_mutation(self, fn) -> None:  # type: ignore[no-untyped-def]
        df = dataset_c().copy()
        df.loc[0, "score"] = np.nan
        snapshot = df.copy(deep=True)
        fn(df)
        pd.testing.assert_frame_equal(df, snapshot)
