"""Data quality reporting: encoding recommendations, quality scoring,
HTML and CSV export.

Assembles every analysis module into a single :class:`QualityReport`
and provides functions to render it as a self-contained HTML file or
a CSV summary.

Example::

    from datapreptoolkit.reporter import (
        generate_quality_report,
        export_html_report,
    )

    report = generate_quality_report(df)
    export_html_report(report)
"""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from datapreptoolkit.analyzer import (
    CategoricalAnalysis,
    FeatureSummary,
    MissingValueAnalysis,
    NumericAnalysis,
    analyze_categorical_columns,
    analyze_missing_values,
    analyze_numeric_columns,
    generate_feature_summaries,
)
from datapreptoolkit.config import EncodingStrategy, ToolkitConfig
from datapreptoolkit.exceptions import ReportError
from datapreptoolkit.loader import DatasetProfile, profile_dataset
from datapreptoolkit.outliers import OutlierDetection, detect_outliers
from datapreptoolkit.utils import ensure_directory

logger = logging.getLogger("datapreptoolkit")


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EncodingRecommendation:
    """Recommended encoding for a single categorical column.

    Attributes:
        column: Column name.
        strategy: Recommended strategy — ``"label"``, ``"one_hot"``,
            ``"frequency"``, or ``"none"``.
        reason: Human-readable justification.
        unique_values: Number of unique values in the column.
        estimated_new_columns: Number of columns after encoding
            (1 for label/frequency, N for one-hot).
    """

    column: str
    strategy: str
    reason: str
    unique_values: int
    estimated_new_columns: int


@dataclass
class QualityReport:
    """Complete data quality report for a DataFrame.

    Populated by :func:`generate_quality_report`.  Contains every
    analysis result plus computed recommendations and an overall
    quality score.

    Attributes:
        shape: Dataset shape (rows, cols).
        memory_human: Human-readable memory string.
        overall_quality_score: 0-100 composite score.
        profile: Dataset profile from the loader.
        missing: Missing-value analysis.
        numeric: Numeric-column analysis.
        categorical: Categorical-column analysis.
        outliers: Outlier detection result.
        feature_summaries: Per-column summaries.
        encoding_recommendations: Per-column encoding advice.
        cleaning_recommendations: Actionable cleaning steps.
    """

    shape: tuple[int, int] = (0, 0)
    memory_human: str = "0 B"
    overall_quality_score: float = 0.0
    profile: DatasetProfile | None = None
    missing: MissingValueAnalysis | None = None
    numeric: NumericAnalysis | None = None
    categorical: CategoricalAnalysis | None = None
    outliers: OutlierDetection | None = None
    feature_summaries: list[FeatureSummary] = field(default_factory=list)
    encoding_recommendations: list[EncodingRecommendation] = field(default_factory=list)
    cleaning_recommendations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Encoding recommendations
# ---------------------------------------------------------------------------

def generate_encoding_recommendations(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> list[EncodingRecommendation]:
    """Suggest an encoding strategy for every categorical column.

    Rules (controlled by ``config.encoding_strategy``):
    * Columns with <= 10 unique values -> ``"one_hot"``
    * Columns with <= 50 unique values -> ``"label"``
    * Columns with > 50 unique values -> ``"frequency"``
    * If the global strategy is ``"none"`` -> ``"none"`` for all.

    Args:
        df: The DataFrame to analyse.
        config: Toolkit configuration.

    Returns:
        A list of :class:`EncodingRecommendation` objects.
    """
    cfg = config or ToolkitConfig()
    cat_cols = df.select_dtypes(
        include=["object", "category", "string"]
    ).columns
    recs: list[EncodingRecommendation] = []

    for col in cat_cols:
        n_unique = int(df[col].nunique())

        if cfg.encoding_strategy == EncodingStrategy.NONE:
            strat, reason, est = "none", "Encoding disabled in config.", 1
        elif n_unique <= 10:
            strat = "one_hot"
            reason = (
                f"{n_unique} unique values (low cardinality) - "
                f"one-hot encoding preserves all information."
            )
            est = n_unique
        elif n_unique <= 50:
            strat = "label"
            reason = (
                f"{n_unique} unique values (medium cardinality) - "
                f"label encoding avoids column explosion."
            )
            est = 1
        else:
            strat = "frequency"
            reason = (
                f"{n_unique} unique values (high cardinality) - "
                f"frequency encoding maps to occurrence counts."
            )
            est = 1

        recs.append(
            EncodingRecommendation(
                column=col,
                strategy=strat,
                reason=reason,
                unique_values=n_unique,
                estimated_new_columns=est,
            )
        )

    logger.info("Encoding recommendations: %d columns", len(recs))
    return recs


# ---------------------------------------------------------------------------
# Quality score computation (configurable weights)
# ---------------------------------------------------------------------------

def _compute_quality_score(
    profile: DatasetProfile,
    missing: MissingValueAnalysis,
    outlier: OutlierDetection | None,
    config: ToolkitConfig,
) -> float:
    """Compute a 0-100 composite quality score using configurable weights.

    The score starts at 100 and subtracts penalties based on data quality
    issues. Each penalty is weighted by the corresponding value in
    ``config.quality_weights``.

    Weights:
        missing: Penalty multiplier for missing cells (max penalty: weight).
        duplicate: Penalty multiplier for duplicate rows (max penalty: weight).
        constant: Penalty per constant column.
        high_cardinality: Penalty per high-cardinality column.
        outlier: Penalty per column with outliers.

    Returns:
        A float between 0 and 100.
    """
    n_rows, n_cols = profile.shape
    total_cells = profile.total_cells
    weights = config.quality_weights

    score = 100.0

    # Missing values penalty (proportion * weight)
    if total_cells > 0:
        score -= (profile.total_missing / total_cells) * weights["missing"]

    # Duplicate rows penalty (ratio * weight)
    if n_rows > 0:
        score -= profile.duplicate_ratio * weights["duplicate"]

    # Constant columns penalty (count * weight per column)
    score -= len(profile.constant_columns) * weights["constant"]

    # High cardinality columns penalty (count * weight per column)
    score -= len(profile.high_cardinality_columns) * weights["high_cardinality"]

    # Outlier columns penalty (count * weight per column)
    if outlier:
        score -= len(outlier.columns_with_outliers) * weights["outlier"]

    return round(max(0.0, min(100.0, score)), 2)


# ---------------------------------------------------------------------------
# Cleaning recommendations
# ---------------------------------------------------------------------------

def _build_cleaning_recommendations(
    missing: MissingValueAnalysis,
    numeric: NumericAnalysis,
    categorical: CategoricalAnalysis,
    outlier: OutlierDetection | None,
    profile: DatasetProfile,
) -> list[str]:
    """Build a prioritised list of actionable cleaning recommendations."""
    recs: list[str] = []

    # Missing values
    for col, action in missing.recommended_actions.items():
        if action == "drop_column":
            recs.append(f"Drop column '{col}' (>60% missing).")
        elif action == "impute_median":
            recs.append(f"Impute missing values in '{col}' with median.")
        elif action == "impute_mode":
            recs.append(f"Impute missing values in '{col}' with mode.")

    # Duplicates
    if profile.duplicate_rows > 0:
        recs.append(
            f"Remove {profile.duplicate_rows} duplicate rows "
            f"({profile.duplicate_ratio:.1%} of data)."
        )

    # Outliers
    if outlier and outlier.columns_with_outliers:
        cols = ", ".join(f"'{c}'" for c in outlier.columns_with_outliers)
        recs.append(f"Investigate outliers in: {cols}.")

    # Skewed numerics
    if numeric.highly_skewed:
        cols = ", ".join(f"'{c}'" for c in numeric.highly_skewed)
        recs.append(f"Consider log-transforming skewed columns: {cols}.")

    # High cardinality
    if categorical.high_cardinality_columns:
        cols = ", ".join(
            f"'{c}'" for c in categorical.high_cardinality_columns
        )
        recs.append(
            f"High-cardinality categoricals may need "
            f"frequency encoding: {cols}."
        )

    # Constant columns
    if profile.constant_columns:
        cols = ", ".join(f"'{c}'" for c in profile.constant_columns)
        recs.append(f"Drop constant columns: {cols}.")

    if not recs:
        recs.append("No cleaning actions required - dataset looks good!")

    return recs


# ---------------------------------------------------------------------------
# Public API: generate quality report
# ---------------------------------------------------------------------------

def generate_quality_report(
    df: pd.DataFrame,
    config: ToolkitConfig | None = None,
) -> QualityReport:
    """Assemble a complete :class:`QualityReport` from all analysis modules.

    This is the main entry point for the reporter.  It calls the loader,
    analyzer, and outlier modules, computes the quality score, builds
    encoding recommendations, and generates cleaning advice.

    The input DataFrame is **never modified**.

    Args:
        df: The DataFrame to report on.
        config: Toolkit configuration.

    Returns:
        A fully-populated :class:`QualityReport`.
    """
    cfg = config or ToolkitConfig()
    logger.info("Generating quality report for %d x %d DataFrame", *df.shape)

    profile = profile_dataset(df, cfg)
    missing = analyze_missing_values(df, cfg)
    numeric = analyze_numeric_columns(df, cfg)
    categorical = analyze_categorical_columns(df, cfg)
    outliers = detect_outliers(df, config=cfg) if cfg.detect_outliers else None
    feature_summaries = generate_feature_summaries(df, cfg)
    enc_recs = generate_encoding_recommendations(df, cfg)

    quality_score = _compute_quality_score(profile, missing, outliers, cfg)
    cleaning_recs = _build_cleaning_recommendations(
        missing, numeric, categorical, outliers, profile
    )

    report = QualityReport(
        shape=df.shape,
        memory_human=profile.memory_human,
        overall_quality_score=quality_score,
        profile=profile,
        missing=missing,
        numeric=numeric,
        categorical=categorical,
        outliers=outliers,
        feature_summaries=feature_summaries,
        encoding_recommendations=enc_recs,
        cleaning_recommendations=cleaning_recs,
    )

    logger.info("Quality report generated - score: %.2f/100", quality_score)
    return report


# ---------------------------------------------------------------------------
# Public API: HTML export
# ---------------------------------------------------------------------------

def _html_table(headers: list[str], rows: list[list[str]]) -> str:
    """Render an HTML table from headers and rows."""
    h = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    body = ""
    for row in rows:
        cells = "".join(f"<td>{html.escape(str(c))}</td>" for c in row)
        body += f"<tr>{cells}</tr>\n"
    return f"<table><thead><tr>{h}</tr></thead><tbody>{body}</tbody></table>"


def export_html_report(
    report: QualityReport,
    filepath: str | Path | None = None,
    config: ToolkitConfig | None = None,
) -> str:
    """Export the :class:`QualityReport` as a self-contained HTML file.

    Args:
        report: The quality report to render.
        filepath: Output file path.  ``None`` uses
            ``config.report_dir / "data_quality_report.html"``.
        config: Toolkit configuration (controls default path).

    Returns:
        The absolute path of the saved HTML file.

    Raises:
        ReportError: If writing the file fails.
    """
    cfg = config or ToolkitConfig()
    if filepath is None:
        ensure_directory(cfg.report_dir)
        filepath = cfg.report_dir / "data_quality_report.html"
    filepath = Path(filepath)

    score = report.overall_quality_score
    score_colour = "#27ae60" if score >= 80 else "#f39c12" if score >= 60 else "#e74c3c"

    sections: list[str] = []

    # --- Overview ---
    sections.append(f"""
    <div class="card">
      <h2>Dataset Overview</h2>
      {_html_table(
          ["Metric", "Value"],
          [
              ["Rows", str(report.shape[0])],
              ["Columns", str(report.shape[1])],
              ["Memory", report.memory_human],
              [
                  "Quality Score",
                  '<span style="color:'
                  f'{score_colour};font-weight:bold">'
                  f"{score}/100</span>",
              ],
          ],
      )}
    </div>""")

    # --- Missing values ---
    if report.missing:
        mv_rows = [
            [col, str(info.null_count), f"{info.null_pct:.2f}%"]
            for col, info in report.missing.columns.items()
            if info.has_missing
        ]
        sections.append(f"""
    <div class="card">
      <h2>Missing Values</h2>
      <p>Total missing cells: {report.missing.total_missing}
      ({report.missing.overall_missing_pct:.2f}%)</p>
      {_html_table(["Column", "Missing Count", "Missing %"], mv_rows)}
    </div>""")

    # --- Numeric analysis ---
    if report.numeric and report.numeric.columns:
        num_rows = [
            [name, f"{s.mean:.2f}", f"{s.median:.2f}", f"{s.std:.2f}",
             f"{s.min:.2f}", f"{s.max:.2f}", str(s.outlier_count_iqr)]
            for name, s in report.numeric.columns.items()
        ]
        sections.append(f"""
    <div class="card">
      <h2>Numeric Columns</h2>
      {_html_table(
          ["Column", "Mean", "Median", "Std",
           "Min", "Max", "Outliers"],
          num_rows,
      )}
    </div>""")

    # --- Categorical analysis ---
    if report.categorical and report.categorical.columns:
        cat_rows = [
            [name, str(s.unique_count), str(s.mode), f"{s.cardinality_ratio:.4f}"]
            for name, s in report.categorical.columns.items()
        ]
        sections.append(f"""
    <div class="card">
      <h2>Categorical Columns</h2>
      {_html_table(["Column", "Unique", "Mode", "Cardinality Ratio"], cat_rows)}
    </div>""")

    # --- Encoding recommendations ---
    if report.encoding_recommendations:
        enc_rows = [
            [r.column, r.strategy, str(r.unique_values), r.reason]
            for r in report.encoding_recommendations
        ]
        sections.append(f"""
    <div class="card">
      <h2>Encoding Recommendations</h2>
      {_html_table(["Column", "Strategy", "Unique Values", "Reason"], enc_rows)}
    </div>""")

    # --- Outlier summary ---
    if report.outliers and report.outliers.columns_with_outliers:
        out_rows = [
            [name, str(s.outlier_count), f"{s.outlier_pct:.2f}%",
             f"[{s.lower_bound}, {s.upper_bound}]"]
            for name, s in report.outliers.columns.items()
            if s.outlier_count > 0
        ]
        sections.append(f"""
    <div class="card">
      <h2>Outlier Summary</h2>
      {_html_table(["Column", "Count", "Percentage", "Bounds"], out_rows)}
    </div>""")

    # --- Cleaning recommendations ---
    if report.cleaning_recommendations:
        li_items = "".join(
            f"<li>{html.escape(r)}</li>"
            for r in report.cleaning_recommendations
        )
        sections.append(f"""
    <div class="card">
      <h2>Cleaning Recommendations</h2>
      <ul>{li_items}</ul>
    </div>""")

    # --- Assemble ---
    body = "\n".join(sections)
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Data Quality Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
         background: #f4f6f9; color: #333; padding: 2rem; }}
  h1 {{ text-align: center; margin-bottom: 0.5rem; color: #2c3e50; }}
  .subtitle {{ text-align: center; color: #7f8c8d; margin-bottom: 2rem; }}
  .card {{ background: #fff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.08);
           padding: 1.5rem; margin-bottom: 1.5rem; }}
  h2 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem;
        margin-bottom: 1rem; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 0.9rem; }}
  th {{ background: #3498db; color: #fff; padding: 0.6rem; text-align: left; }}
  td {{ padding: 0.6rem; border-bottom: 1px solid #ecf0f1; }}
  tr:hover td {{ background: #f9fbfd; }}
  ul {{ padding-left: 1.5rem; }}
  li {{ margin-bottom: 0.5rem; }}
</style>
</head>
<body>
  <h1>Data Quality Report</h1>
  <p class="subtitle">Generated by DataPrepToolkit v0.1.0</p>
  {body}
</body>
</html>"""

    try:
        filepath.write_text(html_content, encoding="utf-8")
        logger.info("HTML report saved: %s", filepath)
        return str(filepath.resolve())
    except Exception as exc:
        raise ReportError(f"Failed to write HTML report: {exc}") from exc


# ---------------------------------------------------------------------------
# Public API: CSV export
# ---------------------------------------------------------------------------

def export_csv_summary(
    report: QualityReport,
    filepath: str | Path | None = None,
    config: ToolkitConfig | None = None,
) -> str:
    """Export the per-column summary as a CSV file.

    The CSV contains one row per column with key statistics.

    Args:
        report: The quality report to export.
        filepath: Output file path.  ``None`` uses
            ``config.report_dir / "data_quality_summary.csv"``.
        config: Toolkit configuration.

    Returns:
        The absolute path of the saved CSV file.

    Raises:
        ReportError: If writing the file fails.
    """
    cfg = config or ToolkitConfig()
    if filepath is None:
        ensure_directory(cfg.report_dir)
        filepath = cfg.report_dir / "data_quality_summary.csv"
    filepath = Path(filepath)

    rows: list[dict[str, Any]] = []
    for fs in report.feature_summaries:
        row: dict[str, Any] = {
            "column": fs.column,
            "dtype": fs.dtype,
            "semantic_type": fs.semantic_type,
            "non_null": fs.non_null,
            "null_count": fs.null_count,
            "null_pct": fs.null_pct,
            "unique_count": fs.unique_count,
            "unique_ratio": fs.unique_ratio,
        }

        # Encoding rec
        enc = next(
            (r for r in report.encoding_recommendations if r.column == fs.column),
            None,
        )
        row["encoding_strategy"] = enc.strategy if enc else "N/A"

        # Outlier info
        if report.outliers and fs.column in report.outliers.columns:
            oi = report.outliers.columns[fs.column]
            row["outlier_count"] = oi.outlier_count
            row["outlier_pct"] = oi.outlier_pct
        else:
            row["outlier_count"] = 0
            row["outlier_pct"] = 0.0

        rows.append(row)

    df = pd.DataFrame(rows)

    try:
        df.to_csv(filepath, index=False)
        logger.info("CSV summary saved: %s", filepath)
        return str(filepath.resolve())
    except Exception as exc:
        raise ReportError(f"Failed to write CSV summary: {exc}") from exc
