# DataPrepToolkit

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/tests-171%20passing-brightgreen.svg" alt="Tests">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/version-1.1.0-orange.svg" alt="Version">
  <img src="https://img.shields.io/badge/contracts-automation--core%20v0.1.0-blue.svg" alt="automation-core">
</p>

<p align="center">
  <strong>Automated Data Preprocessing, Profiling, and Quality Reporting</strong>
</p>

<p align="center">
  <a href="#installation">Installation</a> |
  <a href="#quick-start">Quick Start</a> |
  <a href="#features">Features</a> |
  <a href="#api-reference">API Reference</a> |
  <a href="#ecosystem">Ecosystem</a>
</p>

---

## Overview

DataPrepToolkit is a production-quality Python package that automates the most common data preprocessing tasks performed before exploratory analysis, business intelligence reporting, or machine learning workflows.

Instead of writing repetitive cleaning code for every project, use DataPrepToolkit to:

- **Load** and **profile** your dataset in one line
- **Validate** data against business rules
- **Clean** missing values, duplicates, and invalid data
- **Optimize** memory usage with automatic type downcasting
- **Detect** outliers using statistical methods
- **Report** data quality with professional HTML/CSV exports

## Ecosystem

DataPrepToolkit is the first component of a modular data analysis ecosystem:

| Component | Purpose | Version |
|-----------|---------|---------|
| **DataPrepToolkit** | Data preprocessing, cleaning, validation | v1.1.0 |
| [AutoEDA](https://github.com/Arasoul/AutoEDA) | Exploratory data analysis, visualization | v1.0.0 |
| [AutoAnalytics](https://github.com/Arasoul/AutoAnalytics) | Statistical analysis, modelling | v1.0.0 |
| [AutoBI](https://github.com/Arasoul/AutoBI) | Dashboard generation, BI export | v1.0.0 |
| [automation-core](https://github.com/Arasoul/automation-core) | Shared contracts and serialization | v0.1.0 |

**Contract flow:** DataPrepToolkit produces a `PreprocessingResult` contract that downstream packages consume via `UpstreamReference`.

## Installation

```bash
pip install datapreptoolkit
```

For development:

```bash
git clone https://github.com/Arasoul/DataPrepToolkit.git
cd DataPrepToolkit
pip install -e ".[dev]"
```

## Quick Start

```python
from datapreptoolkit import load_csv, generate_quality_report, export_html_report

# Load your data
df = load_csv("your_data.csv")

# Generate a complete quality report
report = generate_quality_report(df)
report.overall_quality_score  # e.g. 95.54

# Export as professional HTML report
export_html_report(report, "reports/quality_report.html")
```

## Features

### Load Data

```python
from datapreptoolkit import load_csv, load_dataframe

df = load_csv("data.csv")
df = load_dataframe(your_df)
```

### Profile Dataset

```python
from datapreptoolkit import profile_dataset

profile = profile_dataset(df)
profile.shape              # (1000, 12)
profile.memory_human       # "456.78 KB"
profile.overall_quality_score  # 92.62
```

### Validate Data

```python
from datapreptoolkit import validate_dataset, ValidationRule

rules = [
    ValidationRule(column="age", rule_type="range", min_value=0, max_value=120),
    ValidationRule(column="email", rule_type="regex", pattern=r"^[\w.-]+@[\w.-]+\.\w+$"),
    ValidationRule(column="id", rule_type="no_duplicates"),
]

result = validate_dataset(df, rules)
result.is_valid       # False
result.failed_rules   # 1
```

### Clean Data

```python
from datapreptoolkit import clean_dataset

df_final, result = clean_dataset(df)
```

### Optimize Memory

```python
from datapreptoolkit import optimise_memory

df_optimized, result = optimise_memory(df)
result.savings_pct  # 27.6
```

### Detect Outliers

```python
from datapreptoolkit import detect_outliers

result = detect_outliers(df, method="iqr")
result.total_outliers  # 15
```

### Generate Reports

```python
from datapreptoolkit import generate_quality_report, export_html_report

report = generate_quality_report(df)
export_html_report(report, "reports/quality_report.html")
```

### Contract Adapter

```python
from datapreptoolkit.contracts import build_preprocessing_result
from datapreptoolkit._internal.models import RuntimeAnalysisState

state = RuntimeAnalysisState()
state.log_change("Cleaned data")

# Produces a PreprocessingResult contract for downstream packages
result = build_preprocessing_result(df, original_df=original_df, state=state)
```

## Architecture

```
DataPrepToolkit/
├── src/datapreptoolkit/
│   ├── __init__.py        # Public API
│   ├── _version.py        # __version__ = "1.1.0"
│   ├── contracts.py       # build_preprocessing_result adapter
│   ├── config.py          # ToolkitConfig, enums
│   ├── exceptions.py      # Custom exception hierarchy
│   ├── utils.py           # Delegates to automation_core.utils
│   ├── loader.py          # CSV/DataFrame loading, profiling
│   ├── analyzer.py        # Missing values, numeric, categorical analysis
│   ├── cleaner.py         # Imputation, deduplication, validation
│   ├── optimizer.py       # Memory/dtype optimization
│   ├── outliers.py        # IQR, Z-score outlier detection
│   ├── validator.py       # Rule-based data validation
│   └── reporter.py        # Quality scoring, HTML/CSV export
├── tests/                 # 171 unit tests
├── pyproject.toml
├── LICENSE
└── README.md
```

## API Reference

### Loader
- `load_csv(filepath, encoding)` — Load CSV file
- `load_dataframe(df)` — Load from existing DataFrame
- `profile_dataset(df, config)` — Generate DatasetProfile

### Cleaner
- `handle_missing_values(df, strategy, config)` — Impute/drop missing
- `remove_duplicates(df, subset, config)` — Remove duplicate rows
- `clean_dataset(df, config)` — Run full cleaning pipeline

### Optimizer
- `optimise_datatypes(df, config)` — Down-cast types
- `optimise_memory(df, config)` — High-level memory optimization

### Outliers
- `detect_outliers(df, method, config)` — Auto-detect outliers

### Validator
- `validate_dataset(df, rules, config)` — Validate against rules

### Reporter
- `generate_quality_report(df, config)` — Generate QualityReport
- `export_html_report(report, filepath, config)` — Export HTML
- `export_csv_summary(report, filepath, config)` — Export CSV

### Contract
- `build_preprocessing_result(df, original_df, state, upstream_ref)` — Build `PreprocessingResult`

## Testing

```bash
python -m pytest tests/ -v
python -m pytest tests/ --cov=datapreptoolkit --cov-report=html
```

## Requirements

- Python 3.11+
- pandas >= 2.1.0
- numpy >= 1.25.0
- automation-core >= 0.1.0

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

**Ahmed** - [GitHub](https://github.com/Arasoul)
