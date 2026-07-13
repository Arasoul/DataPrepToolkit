"""DataPrepToolkit — Automated data preprocessing, profiling, and quality reporting.

A reusable Python toolkit that automates the most common data preprocessing
tasks performed before Exploratory Data Analysis (EDA), dashboard development,
or machine learning.

Quick start::

    from datapreptoolkit import ToolkitConfig

    config = ToolkitConfig(remove_duplicates=True, detect_outliers=True)

The package is designed to work seamlessly with both CSV files and Pandas
DataFrames.
"""

from __future__ import annotations

__version__ = "0.1.0"
__author__ = "Ahmed"

# -- Public API surface --
# Only re-export items that form the user-facing surface.
# Internal helpers stay internal.

from datapreptoolkit.analyzer import (
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
from datapreptoolkit.cleaner import (
    CleaningResult,
    ImputationRecord,
    InvalidValueRule,
    clean_dataset,
    detect_invalid_values,
    handle_missing_values,
    parse_datetimes,
    remove_duplicates,
)
from datapreptoolkit.config import EncodingStrategy, ToolkitConfig, ZScoreMethod
from datapreptoolkit.exceptions import (
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
from datapreptoolkit.loader import (
    ColumnProfile,
    DatasetProfile,
    load_csv,
    load_dataframe,
    profile_dataset,
)
from datapreptoolkit.optimizer import (
    ColumnOptimization,
    OptimizationResult,
    optimise_datatypes,
    optimise_memory,
)
from datapreptoolkit.outliers import (
    ColumnOutlierInfo,
    OutlierDetection,
    detect_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
)
from datapreptoolkit.reporter import (
    EncodingRecommendation,
    QualityReport,
    export_csv_summary,
    export_html_report,
    generate_encoding_recommendations,
    generate_quality_report,
)
from datapreptoolkit.utils import (
    copy_dataframe,
    format_bytes,
    identify_column_types,
    memory_usage_mb,
    setup_logging,
    validate_columns,
)
from datapreptoolkit.validator import (
    ValidationResult,
    ValidationRule,
    ValidationViolation,
    validate_dataset,
)

__all__ = [
    # Version
    "__version__",
    "__author__",
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
    "setup_logging",
    "copy_dataframe",
    "validate_columns",
    "format_bytes",
    "memory_usage_mb",
    "identify_column_types",
    # Validator
    "validate_dataset",
    "ValidationRule",
    "ValidationResult",
    "ValidationViolation",
]
