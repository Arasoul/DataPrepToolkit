# DataPrepToolkit v1.0.0

First stable release of DataPrepToolkit — a production-quality Python toolkit for automated data preprocessing, profiling, and quality reporting.

## Overview

DataPrepToolkit automates the repetitive data preparation tasks that precede every analysis project: loading, validation, cleaning, optimization, outlier detection, and quality reporting. Instead of rewriting the same preprocessing code for every project, use DataPrepToolkit as a reusable foundation.

The toolkit is designed for data analysts, business intelligence engineers, and data scientists who need a consistent, tested, and well-documented preprocessing pipeline.

## Major Features

### Data Loading & Profiling
- Load CSV files or Pandas DataFrames with automatic dataset profiling
- Instant visibility into shape, memory usage, column types, and quality score

### Data Validation
- Rule-based validation with six rule types: `range`, `regex`, `not_null`, `no_duplicates`, `required`, `in_set`
- Clear violation reporting with column-level detail

### Data Cleaning
- 10 imputation strategies: mean, median, mode, forward-fill, back-fill, interpolation, drop rows, drop columns, zero, empty
- Automatic duplicate detection and removal
- Datetime column parsing with revert safety
- Invalid value detection with customizable rules

### Memory Optimization
- Automatic integer downcasting (`int64` to `int8`/`int16`/`int32`)
- Float downcasting (`float64` to `float32`)
- Object-to-category conversion for low-cardinality columns
- Measurable memory savings with before/after reporting

### Outlier Detection
- IQR method (configurable multiplier)
- Z-score method (standard and modified/MAD-based)
- Per-column outlier statistics with bound reporting

### Quality Reporting
- Composite quality score with configurable weights
- Professional HTML report with dataset overview, missing values analysis, numeric/categorical statistics, encoding recommendations, and outlier summary
- CSV summary export for programmatic consumption

## Engineering Improvements

- **171 unit and integration tests** with 92% code coverage
- **Type hints** on all public APIs with `mypy` enforcement
- **PEP 561 compliant** (`py.typed` marker for downstream type checkers)
- **Hardened CI/CD**: ruff lint, ruff format check, mypy, coverage floor (85%), multi-Python matrix (3.11, 3.12, 3.13), pip caching, Codecov v5
- **Clean dependency footprint**: only `pandas` and `numpy` as runtime dependencies
- **Immutable configuration**: `quality_weights` enforced via `MappingProxyType`
- **Consistent exception hierarchy**: all errors inherit from `DataPrepError`
- **Production/Stable classifier** on PyPI

## Breaking Changes

No breaking changes. This is the first stable public release.

## Known Limitations

- **In-memory processing**: All operations run on Pandas DataFrames in memory. Large-than-memory datasets are not supported.
- **Configuration via Python objects**: No YAML/CLI configuration interface; all settings are passed through `ToolkitConfig`.
- **No streaming support**: Data is loaded and processed in full.

## Installation

```bash
pip install datapreptoolkit
```

Requires Python 3.11+. Only depends on `pandas` and `numpy`.

## Quick Start

```python
from datapreptoolkit import load_csv, generate_quality_report, export_html_report

# Load and profile
df = load_csv("your_data.csv")

# Generate quality report
report = generate_quality_report(df)
print(f"Quality score: {report.overall_quality_score}")

# Export as HTML
export_html_report(report, "reports/quality_report.html")
```

## Future Roadmap

DataPrepToolkit is the foundation of a planned automation ecosystem. Upcoming projects:

- **AutoEDA** — Automated exploratory data analysis
- **AutoAnalytics** — Automated statistical analysis and insight generation
- **AutoBI** — Automated business intelligence report generation

## Links

- [Documentation](https://github.com/Arasoul/DataPrepToolkit#readme)
- [Changelog](CHANGELOG.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Issue Tracker](https://github.com/Arasoul/DataPrepToolkit/issues)

## License

MIT License
