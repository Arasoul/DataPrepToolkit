"""Configuration module for DataPrepToolkit.

Provides a centralised, immutable configuration object that controls
every configurable behaviour in the toolkit.
"""

from __future__ import annotations

import types
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Literal


class EncodingStrategy(StrEnum):
    """Supported encoding strategies for categorical columns."""

    LABEL = "label"
    ONE_HOT = "one_hot"
    FREQUENCY = "frequency"
    NONE = "none"


class ZScoreMethod(StrEnum):
    """Z-score threshold methods."""

    STANDARD = "standard"
    MODIFIED = "modified"


@dataclass(frozen=True)
class ToolkitConfig:
    """Central configuration for the DataPrepToolkit.

    All behavioural knobs are exposed here so that callers never need
    to touch internals.  Create an instance (optionally overriding
    defaults) and pass it to any public function.

    Attributes:
        remove_duplicates: Whether to drop duplicate rows during cleaning.
        duplicate_subset: Column names to consider for duplicate detection.
                          ``None`` means all columns.
        duplicate_keep: Which duplicate to keep — ``"first"``, ``"last"``,
                        or ``"none"`` (drop all).
        parse_datetimes: Attempt automatic datetime column parsing.
        datetime_format: strftime format string for parsing.  ``None``
                         lets pandas infer the format.
        datetime_columns: Explicit list of columns to parse as datetimes.
                          ``None`` = attempt all object columns.
        optimise_memory: Down-cast numeric types to save memory.
        detect_outliers: Run outlier detection during profiling.
        outlier_method: ``"iqr"`` or ``"zscore"``.
        iqr_multiplier: IQR multiplier for the IQR method (default 1.5).
        zscore_threshold: Absolute z-score threshold (default 3.0).
        zscore_method: ``"standard"`` or ``"modified"`` (median-based).
        generate_html_report: Render a full HTML quality report.
        report_dir: Directory for saving reports.
        encoding_strategy: Recommended encoding for categorical columns.
        high_cardinality_threshold: Unique-value ratio above which a
            categorical column is flagged as high-cardinality.
        constant_threshold: Ratio above which a column is considered
            constant (all identical values).
        id_column_threshold: Unique-value ratio above which a column is
            flagged as a potential identifier.
        log_level: Logging level string (``"DEBUG"``, ``"INFO"``, etc.).
        quality_weights: Dict of quality score weights for computing
            the overall quality score. Keys: missing, duplicate,
            constant, high_cardinality, outlier.
    """

    # -- Duplicate handling --
    remove_duplicates: bool = False
    duplicate_subset: tuple[str, ...] | None = None
    duplicate_keep: Literal["first", "last", "none"] = "first"

    # -- Datetime parsing --
    parse_datetimes: bool = True
    datetime_format: str | None = None
    datetime_columns: list[str] | None = None

    # -- Memory optimisation --
    optimise_memory: bool = True

    # -- Outlier detection --
    detect_outliers: bool = True
    outlier_method: Literal["iqr", "zscore"] = "iqr"
    iqr_multiplier: float = 1.5
    zscore_threshold: float = 3.0
    zscore_method: ZScoreMethod = ZScoreMethod.STANDARD

    # -- Reporting --
    generate_html_report: bool = True
    report_dir: Path = Path("reports")

    # -- Encoding --
    encoding_strategy: EncodingStrategy = EncodingStrategy.LABEL

    # -- Thresholds --
    high_cardinality_threshold: float = 0.95
    constant_threshold: float = 0.99
    id_column_threshold: float = 0.95

    # -- Quality scoring weights --
    quality_weights: dict[str, float] = field(
        default_factory=lambda: {
            "missing": 40.0,
            "duplicate": 20.0,
            "constant": 2.0,
            "high_cardinality": 1.0,
            "outlier": 3.0,
        }
    )

    # -- Logging --
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    def __post_init__(self) -> None:
        """Validate configuration values after initialisation.

        Raises:
            ValueError: If any value falls outside its valid range.
        """
        if self.iqr_multiplier <= 0:
            raise ValueError(
                f"iqr_multiplier must be positive, got {self.iqr_multiplier}"
            )
        if self.zscore_threshold <= 0:
            raise ValueError(
                f"zscore_threshold must be positive, got {self.zscore_threshold}"
            )
        if not 0.0 < self.high_cardinality_threshold <= 1.0:
            raise ValueError(
                "high_cardinality_threshold must be in (0, 1], "
                f"got {self.high_cardinality_threshold}"
            )
        if not 0.0 < self.constant_threshold <= 1.0:
            raise ValueError(
                f"constant_threshold must be in (0, 1], got {self.constant_threshold}"
            )
        if not 0.0 < self.id_column_threshold <= 1.0:
            raise ValueError(
                f"id_column_threshold must be in (0, 1], got {self.id_column_threshold}"
            )
        if self.duplicate_keep not in ("first", "last", "none"):
            raise ValueError(
                f"duplicate_keep must be 'first', 'last', or 'none', "
                f"got '{self.duplicate_keep}'"
            )
        # Validate quality_weights
        valid_keys = {"missing", "duplicate", "constant", "high_cardinality", "outlier"}
        if set(self.quality_weights.keys()) != valid_keys:
            raise ValueError(
                f"quality_weights must have keys {valid_keys}, "
                f"got {set(self.quality_weights.keys())}"
            )
        # Wrap in MappingProxyType for true immutability
        object.__setattr__(
            self,
            "quality_weights",
            types.MappingProxyType(self.quality_weights),
        )
