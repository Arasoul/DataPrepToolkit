# Changelog

All notable changes to DataPrepToolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-07-19

First stable release of DataPrepToolkit.

### Overview

DataPrepToolkit is a production-quality Python toolkit that automates the most
common data preprocessing tasks performed before exploratory analysis, business
intelligence reporting, or machine learning workflows.

### Added

- **Loader**: CSV and DataFrame loading with automatic profiling
- **Analyzer**: Missing value, numeric, and categorical analysis
- **Cleaner**: 10 imputation strategies, deduplication, invalid value detection
- **Optimizer**: Automatic int/float downcasting, object-to-category conversion
- **Outliers**: IQR and Z-score (standard/modified) outlier detection
- **Validator**: Rule-based validation (range, regex, not_null, no_duplicates, required, in_set)
- **Reporter**: Quality scoring, HTML/CSV export, encoding recommendations
- **Config**: Centralized ToolkitConfig with customizable quality weights
- `py.typed` marker for PEP 561 compliance
- 171 unit and integration tests across all modules
- Complete workflow example notebook
- Professional HTML and CSV report export

### Changed

- **Config**: Renamed `optimize_memory` to `optimise_memory` for spelling consistency
- **Loader**: `load_csv()` now raises `LoadError` instead of `FileNotFoundError` for consistent exception hierarchy
- **Config**: `quality_weights` dict is now truly immutable (`MappingProxyType`)
- **CI/CD**: Format check with `ruff format --check`, coverage floor enforcement (`--cov-fail-under=85`), pip caching, codecov v5

### Fixed

- **Analyzer**: Fixed dead code branch in `generate_feature_summaries()` (`"bool"` -> `"boolean"`)
- **Cleaner**: Removed unused `_STRATEGY_DISPATCH` dict
- **Cleaner**: Narrowed `except Exception` to `except (ValueError, TypeError)` in `detect_invalid_values()`

### Removed

- Unused runtime dependencies: `scikit-learn`, `tabulate`

## [0.1.0] - 2024-01-01

### Added

- **Loader**: CSV and DataFrame loading with automatic profiling
- **Analyzer**: Missing value, numeric, and categorical analysis
- **Cleaner**: 10 imputation strategies, deduplication, invalid value detection
- **Optimizer**: Automatic int/float downcasting, object-to-category conversion
- **Outliers**: IQR and Z-score (standard/modified) outlier detection
- **Validator**: Rule-based validation (range, regex, not_null, no_duplicates, required, in_set)
- **Reporter**: Quality scoring, HTML/CSV export, encoding recommendations
- **Config**: Centralized ToolkitConfig with customizable quality weights
- **Tests**: 166 unit tests across all modules
- **Examples**: Complete workflow demonstration script
