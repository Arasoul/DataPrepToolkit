"""DataPrepToolkit — Automated data preprocessing, profiling, and quality reporting.

A reusable Python toolkit that automates the most common data preprocessing
tasks performed before Exploratory Data Analysis (EDA), dashboard development,
or machine learning.
"""

from __future__ import annotations

# -- Public API surface --
# Only re-export items that form the user-facing surface.
# Internal helpers stay internal.
from datapreptoolkit._internal.analyzer import (
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
from datapreptoolkit._internal.cleaner import (
    CleaningResult,
    ImputationRecord,
    InvalidValueRule,
    clean_dataset,
    detect_invalid_values,
    handle_missing_values,
    parse_datetimes,
    remove_duplicates,
)
from datapreptoolkit._internal.config import (
    EncodingStrategy,
    ToolkitConfig,
    ZScoreMethod,
)
from datapreptoolkit._internal.exceptions import (
    CleaningError,
    ConfigError,
    DataPrepError,
    EmptyDatasetError,
    FileFormatError,
    IncompatibleDataError,
    InvalidColumnError,
    LoadError,
    QualityThresholdError,
    ReportError,
    ValidationError,
)
from datapreptoolkit._internal.loader import (
    ColumnProfile,
    DatasetProfile,
    load_csv,
    load_dataframe,
    profile_dataset,
)
from datapreptoolkit._internal.optimizer import (
    ColumnOptimization,
    OptimizationResult,
    optimise_datatypes,
    optimise_memory,
)
from datapreptoolkit._internal.outliers import (
    ColumnOutlierInfo,
    OutlierDetection,
    detect_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
)
from datapreptoolkit._internal.reporter import (
    EncodingRecommendation,
    QualityReport,
    export_csv_summary,
    export_html_report,
    generate_encoding_recommendations,
    generate_quality_report,
)
from datapreptoolkit._internal.utils import format_bytes, identify_column_types
from datapreptoolkit._internal.validator import (
    ValidationResult,
    ValidationRule,
    ValidationViolation,
    validate_dataset,
)
from datapreptoolkit._version import __version__

# Experimental: contract adapter
from datapreptoolkit.contracts import build_preprocessing_result

__all__ = [
    # Version
    "__version__",
    # Config
    "ToolkitConfig",
    "EncodingStrategy",
    "ZScoreMethod",
    # Exceptions
    "DataPrepError",
    "LoadError",
    "FileFormatError",
    "EmptyDatasetError",
    "CleaningError",
    "InvalidColumnError",
    "IncompatibleDataError",
    "ValidationError",
    "QualityThresholdError",
    "ReportError",
    "ConfigError",
    # Analyzer
    "analyze_missing_values",
    "analyze_numeric_columns",
    "analyze_categorical_columns",
    "generate_feature_summaries",
    "MissingValueAnalysis",
    "NumericAnalysis",
    "NumericColumnStats",
    "CategoricalAnalysis",
    "CategoricalColumnStats",
    "FeatureSummary",
    "ColumnMissingInfo",
    # Cleaner
    "handle_missing_values",
    "parse_datetimes",
    "remove_duplicates",
    "detect_invalid_values",
    "clean_dataset",
    "CleaningResult",
    "ImputationRecord",
    "InvalidValueRule",
    # Optimizer
    "optimise_datatypes",
    "optimise_memory",
    "OptimizationResult",
    "ColumnOptimization",
    # Outliers
    "detect_outliers",
    "detect_outliers_iqr",
    "detect_outliers_zscore",
    "OutlierDetection",
    "ColumnOutlierInfo",
    # Reporter
    "generate_quality_report",
    "generate_encoding_recommendations",
    "export_html_report",
    "export_csv_summary",
    "QualityReport",
    "EncodingRecommendation",
    # Loader
    "load_csv",
    "load_dataframe",
    "profile_dataset",
    "DatasetProfile",
    "ColumnProfile",
    # Utils
    "identify_column_types",
    "format_bytes",
    # Validator
    "validate_dataset",
    "ValidationRule",
    "ValidationResult",
    "ValidationViolation",
    # Experimental
    "build_preprocessing_result",
]
