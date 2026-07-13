# Changelog

All notable changes to DataPrepToolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
