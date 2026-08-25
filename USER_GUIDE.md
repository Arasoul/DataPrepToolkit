# DataPrepToolkit — User Guide & Technical Documentation

**Package Version:** `1.1.0`  
**Python Compatibility:** Python `>= 3.11`  
**Core Dependencies:** `pandas >= 2.1.0`, `numpy >= 1.25.0`  

---

## Table of Contents

1. [Overview & Core Concept](#1-overview--core-concept)
2. [Ecosystem Architecture](#2-ecosystem-architecture)
3. [Installation & Requirements](#3-installation--requirements)
4. [Quick Start (30-Second Workflow)](#4-quick-start-30-second-workflow)
5. [Feature Map & Code Examples](#5-feature-map--code-examples)
   - [Data Loading & Dataset Profiling](#data-loading--dataset-profiling)
   - [Missing Value Analysis & Imputation](#missing-value-analysis--imputation)
   - [Duplicate Detection & Removal](#duplicate-detection--removal)
   - [Datetime Parsing](#datetime-parsing)
   - [Invalid Value Detection & Custom Rules](#invalid-value-detection--custom-rules)
   - [Outlier Detection (IQR & Z-Score)](#outlier-detection-iqr--z-score)
   - [Memory Optimization & Type Downcasting](#memory-optimization--type-downcasting)
   - [Rule-Based Data Validation](#rule-based-data-validation)
   - [Categorical Encoding Recommendations](#categorical-encoding-recommendations)
   - [Quality Scoring & HTML/CSV Reporting](#quality-scoring--htmlcsv-reporting)
6. [Real-World Business Scenario Walkthrough](#6-real-world-business-scenario-walkthrough)
7. [Handling Missing Values Guide](#7-handling-missing-values-guide)
8. [Outlier Detection Guide](#8-outlier-detection-guide)
9. [Rule-Based Data Validation Guide](#9-rule-based-data-validation-guide)
10. [Memory Optimization Guide](#10-memory-optimization-guide)
11. [Profiling & Quality Scoring Mechanics](#11-profiling--quality-scoring-mechanics)
12. [Centralized Configuration (`ToolkitConfig`)](#12-centralized-configuration-toolkitconfig)
13. [Role-Based Workflows](#13-role-based-workflows)
    - [Beginner Workflow](#beginner-workflow)
    - [Data Analyst Workflow](#data-analyst-workflow)
    - [Developer & Pipeline Workflow](#developer--pipeline-workflow)
14. [Error Handling & Exception Hierarchy](#14-error-handling--exception-hierarchy)
15. [Edge Cases & Tested Robustness](#15-edge-cases--tested-robustness)
16. [Offline Execution & AI Independence](#16-offline-execution--ai-independence)
17. [Decision Matrix: "Which Feature Should I Use?"](#17-decision-matrix-which-feature-should-i-use)
18. [Complete End-to-End Executable Script](#18-complete-end-to-end-executable-script)
19. [API Reference Index](#19-api-reference-index)

---

## 1. Overview & Core Concept

### What is DataPrepToolkit?

**DataPrepToolkit** is a deterministic Python library designed for automated dataset profiling, data quality assessment, safe cleaning, rule validation, outlier detection, memory optimization, and HTML/CSV reporting. 

It prepares raw tabular data (`pandas.DataFrame`) for Exploratory Data Analysis (EDA), machine learning pipelines, or business intelligence tools.

```text
Raw Dataset (CSV / DataFrame)
            │
            ▼
 ┌────────────────────────────────────────────────────────┐
 │                   DataPrepToolkit                      │
 │ ┌─────────────┐ ┌─────────────┐ ┌────────────────────┐ │
 │ │  Profiling  │ │  Validation │ │ Missing Imputation │ │
 │ └─────────────┘ └─────────────┘ └────────────────────┘ │
 │ ┌─────────────┐ ┌─────────────┐ ┌────────────────────┐ │
 │ │ Deduplication│ │ Outliers    │ │ Memory Downcasting │ │
 │ └─────────────┘ └─────────────┘ └────────────────────┘ │
 └────────────────────────────────────────────────────────┘
            │
            ▼
 Clean, Validated, & Optimized DataFrame + Quality Report
```

### What DataPrepToolkit is NOT

- **NOT an AI/LLM wrapper:** Uses no OpenAI, Anthropic, Gemini, API keys, HTTP requests, or prompt templates.
- **NOT an AutoML framework:** Does not train machine learning models or perform hyperparameter tuning.
- **NOT a BI/Dashboard app:** Focuses strictly on data hygiene, contract validation, and data quality scoring.
- **NOT an EDA visualization generator:** Does not generate matplotlib/seaborn plots (that is handled downstream by `AutoEDA`).

### Core Design Guarantees

1. **Pure Read-Only / Non-Mutating:** Input DataFrames are **never modified in-place**. Every cleaning or optimization function returns a **new DataFrame** alongside a structured summary object.
2. **100% Offline Execution:** Operates entirely locally using Standard Library, `pandas`, `numpy`, and `automation-core`.
3. **Fully Dynamic:** Adapts to any dataset without requiring hardcoded column names (e.g., `"Age"`, `"Salary"`).

---

## 2. Ecosystem Architecture

DataPrepToolkit forms the **foundational data preparation and quality layer** of a modular data analysis ecosystem:

```text
               DataPrepToolkit
(Data Preparation, Quality Assurance, Hygiene)
                      │
                      ▼
                   AutoEDA
 (Exploratory Analysis, Statistics & Visuals)
                      │
                      ▼
                AutoAnalytics
 (Statistical Diagnostics & Analytical Models)
                      │
                      ▼
                    AutoBI
(Interactive Dashboards & Decision Communication)
```

- **Layer Ownership:** `DataPrepToolkit` answers the question: *"Can I trust, clean, optimize, and validate this dataset for downstream work?"*
- **Independent Deployment:** `DataPrepToolkit` operates completely independently. You can use it as a standalone library in scripts, notebooks, or ETL pipelines without installing `AutoEDA`, `AutoAnalytics`, or `AutoBI`.

---

## 3. Installation & Requirements

### System Requirements

- **Python:** `3.11` or higher (`3.11`, `3.12`, `3.13`, `3.14` supported)
- **Dependencies:** `pandas>=2.1.0`, `numpy>=1.25.0`

### Standard Installation

Install via `pip`:

```bash
pip install datapreptoolkit
```

### Development Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/Arasoul/DataPrepToolkit.git
cd DataPrepToolkit
pip install -e .[dev]
```

To verify the installation, run:

```bash
python -c "import datapreptoolkit as dpt; print(dpt.__version__)"
```

---

## 4. Quick Start (30-Second Workflow)

Here is a runnable example demonstrating dataset profiling, automated cleaning, validation, and HTML report generation:

```python
import pandas as pd
import datapreptoolkit as dpt

# 1. Create or load a sample dataset with common issues
raw_data = pd.DataFrame({
    "customer_id": [101, 102, 102, 104, 105],
    "age": [25.0, np.nan, 30.0, 45.0, 120.0],
    "join_date": ["2023-01-15", "2023-02-01", "2023-02-01", "invalid_date", "2023-05-10"],
    "score": [88.5, 92.0, 92.0, 75.0, 99.0],
})

# 2. Generate a comprehensive dataset profile
profile = dpt.profile_dataset(raw_data)
print(f"Shape: {profile.shape} | Memory: {profile.memory_human}")
print(f"Missing Cells: {profile.total_missing} | Duplicates: {profile.duplicate_rows}")

# 3. Execute automated cleaning pipeline
cleaned_df, clean_res = dpt.clean_dataset(raw_data)
print(f"Cleaned Shape: {cleaned_df.shape}")
print(f"Logged changes: {clean_res.messages}")

# 4. Validate data against business rules
rules = [
    dpt.ValidationRule(column="customer_id", rule_type="no_duplicates"),
    dpt.ValidationRule(column="age", rule_type="range", min_value=0, max_value=100),
]
val_res = dpt.validate_dataset(cleaned_df, rules)
print(f"Validation Passed: {val_res.is_valid} ({val_res.passed_rules}/{val_res.total_rules} rules passed)")

# 5. Generate and export a quality report
report = dpt.generate_quality_report(cleaned_df)
html_path = dpt.export_html_report(report, "data_quality_report.html")
print(f"Quality Score: {report.overall_quality_score}/100 | Report saved to: {html_path}")
```

---

## 5. Feature Map & Code Examples

### Data Loading & Dataset Profiling

Load CSV files cleanly with format and existence checks, or profile existing DataFrames.

```python
from datapreptoolkit import load_csv, profile_dataset

# Load CSV safely (raises LoadError if missing, FileFormatError if not .csv)
df = load_csv("sales_data.csv")

# Profile dataset (Read-only)
profile = profile_dataset(df)

print(profile.shape)                     # e.g., (1000, 12)
print(profile.numeric_columns)           # ['quantity', 'price']
print(profile.categorical_columns)       # ['region', 'category']
print(profile.potential_id_columns)      # ['order_id']
print(profile.constant_columns)          # ['country'] (if 100% identical)
```

---

### Missing Value Analysis & Imputation

Analyze missing cell counts per column and impute missing values using custom strategies.

```python
from datapreptoolkit import analyze_missing_values, handle_missing_values

# 1. Analyze missingness
missing_info = analyze_missing_values(df)
print(f"Overall Missing: {missing_info.overall_missing_pct}%")
print(f"Recommended Actions: {missing_info.recommended_actions}")

# 2. Impute with default strategy (median for numeric, mode for categorical)
cleaned_df, result = handle_missing_values(df, strategy="median")

# 3. Impute with per-column strategy map
cleaned_df, result = handle_missing_values(
    df,
    strategy="median",
    strategy_map={
        "price": "mean",
        "category": "mode",
        "notes": "empty",       # Fills object nulls with "Unknown"
        "heavy_null": "drop_column", # Drops column if null % > drop_threshold
    },
    drop_threshold=0.6,
)

for imp in result.imputations:
    print(f"Col: {imp.column} | Strategy: {imp.strategy} | Filled: {imp.rows_filled} rows")
```

---

### Duplicate Detection & Removal

Detect and drop full-row or subset-based duplicate rows transparently.

```python
from datapreptoolkit import remove_duplicates

# Deduplicate based on all columns
cleaned_df, result = remove_duplicates(df, keep="first")
print(f"Dropped {result.duplicates_dropped} duplicate rows.")

# Deduplicate based on specific primary key columns
cleaned_df, result = remove_duplicates(df, subset=["order_id", "product_id"], keep="last")
```

---

### Datetime Parsing

Safely convert string/object columns to Pandas `datetime64` types. Reverts automatically if conversion produces $>50\%$ `NaT` (Not a Time) values to avoid data loss.

```python
from datapreptoolkit import parse_datetimes

# Auto-detect date candidates or pass explicit columns
cleaned_df, result = parse_datetimes(
    df,
    columns=["order_date", "ship_date"],
    datetime_format="%Y-%m-%d",
)

print(f"Parsed datetime columns: {result.columns_parsed}")
```

---

### Invalid Value Detection & Custom Rules

Scan dataset columns for domain violations using built-in negative-number checks or custom callables.

```python
from datapreptoolkit import detect_invalid_values, InvalidValueRule

# Define custom rules for invalid row identification
custom_rules = [
    InvalidValueRule(
        column="age",
        condition=lambda s: (s < 0) | (s > 120),
        description="Age must be between 0 and 120",
    ),
    InvalidValueRule(
        column="discount",
        condition=lambda s: s > 1.0,
        description="Discount ratio cannot exceed 1.0",
    ),
]

invalid_map, result = detect_invalid_values(
    df,
    rules=custom_rules,
    check_negative_non_negative=True, # Auto-checks columns named price, age, quantity, etc.
)

for col, bad_indices in invalid_map.items():
    print(f"Column '{col}' has {len(bad_indices)} invalid rows at indices {bad_indices[:5]}")
```

---

### Outlier Detection (IQR & Z-Score)

Detect statistical outliers using Interquartile Range (IQR) or Z-score (Standard or Modified MAD-based).

> **Important:** Outlier detection is **read-only**. It identifies and flags outlier row indices without deleting valid business records.

```python
from datapreptoolkit import detect_outliers, detect_outliers_iqr, detect_outliers_zscore, ZScoreMethod

# Method 1: IQR (default multiplier 1.5)
iqr_outliers = detect_outliers_iqr(df, multiplier=1.5)
print(f"Total IQR Outliers: {iqr_outliers.total_outliers}")
print(f"Columns with Outliers: {iqr_outliers.columns_with_outliers}")

# Inspect specific column bounds
price_info = iqr_outliers.columns["price"]
print(f"Price Bounds: [{price_info.lower_bound}, {price_info.upper_bound}]")
print(f"Outlier Indices: {price_info.outlier_indices}")

# Method 2: Z-Score (Modified MAD-based, robust against extreme outliers)
z_outliers = detect_outliers_zscore(
    df,
    threshold=3.0,
    method=ZScoreMethod.MODIFIED,
)

# Outlier boolean mask DataFrame
mask_df = iqr_outliers.outlier_mask
```

---

### Memory Optimization & Type Downcasting

Reduce memory usage by down-casting numeric types (`int64` $\to$ `int8`/`int16`/`int32`, `float64` $\to$ `float32`) and converting low-cardinality string columns to `category`.

```python
from datapreptoolkit import optimise_memory, optimise_datatypes

# Run automatic memory optimization
opt_df, opt_res = optimise_memory(df)

print(f"Memory Before: {opt_res.memory_before_human}")
print(f"Memory After:  {opt_res.memory_after_human}")
print(f"Savings:       {opt_res.savings_human} ({opt_res.savings_pct}%)")

for change in opt_res.column_changes:
    print(f"Column '{change.column}': {change.dtype_before} -> {change.dtype_after}")
```

---

### Rule-Based Data Validation

Validate DataFrames against declarative data-quality rules before sending them to downstream analytics or ML models.

```python
from datapreptoolkit import validate_dataset, ValidationRule

rules = [
    ValidationRule(column="order_id", rule_type="required"),
    ValidationRule(column="order_id", rule_type="no_duplicates"),
    ValidationRule(column="price", rule_type="not_null"),
    ValidationRule(column="price", rule_type="range", min_value=0.01, max_value=10000.0),
    ValidationRule(column="email", rule_type="regex", pattern=r"^[\w.-]+@[\w.-]+\.\w+$"),
    ValidationRule(column="status", rule_type="in_set", allowed_values={"shipped", "pending", "cancelled"}),
]

val_result = validate_dataset(df, rules)

print(f"Valid: {val_result.is_valid}")
print(f"Passed Rules: {val_result.passed_rules} / {val_result.total_rules}")

for v in val_result.violations:
    print(f"FAILED [{v.rule_type}] on '{v.column}': {v.violation_count} rows ({v.violation_pct}%). Samples: {v.sample_violations}")
```

---

### Categorical Encoding Recommendations

Suggest optimal categorical encoding strategies (One-Hot, Label, Frequency, or None) based on column cardinality.

```python
from datapreptoolkit import generate_encoding_recommendations

recs = generate_encoding_recommendations(df)

for r in recs:
    print(f"Col: {r.column:<15} | Strategy: {r.strategy:<10} | Unique: {r.unique_values:<4} | Reason: {r.reason}")
```

---

### Quality Scoring & HTML/CSV Reporting

Generate a comprehensive quality report with a composite $0\text{--}100$ quality score and export it to HTML or CSV.

```python
from datapreptoolkit import (
    generate_quality_report,
    export_html_report,
    export_csv_summary,
)

# 1. Assemble complete quality report
report = generate_quality_report(df)
print(f"Overall Quality Score: {report.overall_quality_score} / 100")
print(f"Cleaning Advice: {report.cleaning_recommendations}")

# 2. Export standalone HTML report
html_file = export_html_report(report, "reports/quality_report.html")

# 3. Export CSV summary
csv_file = export_csv_summary(report, "reports/quality_summary.csv")
```

---

## 6. Real-World Business Scenario Walkthrough

### Scenario: Cleaning an Unrefined E-Commerce Retail Dataset (`retail_sales.csv`)

Imagine an e-commerce order table containing missing prices, duplicate orders, incorrect datetimes, negative quantities, and unoptimized datatypes:

```python
import pandas as pd
import numpy as np
import datapreptoolkit as dpt

# --- Step 1: Load Raw Business Data ---
raw_df = pd.DataFrame({
    "order_id": [1001, 1002, 1002, 1004, 1005, 1006, 1007, 1008],
    "order_date": ["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-04", "invalid", "2024-01-06", "2024-01-07", "2024-01-08"],
    "region": ["North", "South", "South", "East", "West", None, "North", "South"],
    "quantity": [2, 1, 1, -5, 3, 4, 1, 2],
    "unit_price": [150.0, 200.0, 200.0, np.nan, 50.0, 300.0, 120.0, np.nan],
    "store_code": ["STORE_A", "STORE_A", "STORE_A", "STORE_A", "STORE_A", "STORE_A", "STORE_A", "STORE_A"], # Constant column
})

print("=== 1. Initial State ===")
initial_profile = dpt.profile_dataset(raw_df)
print(f"Shape: {initial_profile.shape}")
print(f"Memory: {initial_profile.memory_human}")
print(f"Missing Cells: {initial_profile.total_missing}")
print(f"Duplicate Rows: {initial_profile.duplicate_rows}")

# --- Step 2: Configure Cleaning Controls ---
config = dpt.ToolkitConfig(
    remove_duplicates=True,
    duplicate_keep="first",
    parse_datetimes=True,
    optimise_memory=True,
    detect_outliers=True,
    outlier_method="iqr",
)

# --- Step 3: Run Full Cleaning Pipeline ---
cleaned_df, clean_res = dpt.clean_dataset(raw_df, config=config)

# --- Step 4: Detect Invalid Negative Quantities ---
invalid_rules = [
    dpt.InvalidValueRule(column="quantity", condition=lambda s: s <= 0, description="Quantity must be > 0")
]
bad_map, _ = dpt.detect_invalid_values(cleaned_df, rules=invalid_rules)
if "quantity (custom)" in bad_map:
    # Filter out invalid negative quantity rows
    cleaned_df = cleaned_df.drop(index=bad_map["quantity (custom)"]).reset_index(drop=True)

# --- Step 5: Optimize Memory & Datatypes ---
optimized_df, opt_res = dpt.optimise_memory(cleaned_df, config=config)

# --- Step 6: Final Validation & Quality Check ---
val_rules = [
    dpt.ValidationRule(column="order_id", rule_type="no_duplicates"),
    dpt.ValidationRule(column="unit_price", rule_type="not_null"),
]
val_res = dpt.validate_dataset(optimized_df, val_rules)
final_report = dpt.generate_quality_report(optimized_df, config=config)

print("\n=== 2. Final Cleaned State ===")
print(f"Shape: {optimized_df.shape}")
print(f"Memory: {opt_res.memory_after_human} (Saved {opt_res.savings_pct}%)")
print(f"Validation Passed: {val_res.is_valid}")
print(f"Final Quality Score: {final_report.overall_quality_score} / 100")
```

### Before vs. After Execution Metrics

| Metric | Before Cleaning | After Preparation | Difference / Action Taken |
|---|---|---|---|
| **Rows** | `8` | `6` | Removed 1 exact duplicate, 1 invalid negative row |
| **Columns** | `6` | `6` | All required columns preserved |
| **Missing Cells** | `3` | `0` | Imputed median for `unit_price`, mode for `region` |
| **Duplicate Rows** | `1` | `0` | Removed duplicate order `1002` |
| **Datetime Types** | `0` (`object`) | `1` (`datetime64[ns]`) | `order_date` parsed cleanly |
| **Memory Footprint**| `900 B` | `420 B` | Down-casted int/float and converted strings to `category` |
| **Quality Score** | `78.20 / 100` | `98.50 / 100` | $+20.30$ improvement |

---

## 7. Handling Missing Values Guide

### Imputation Strategies Reference

| Strategy Name | Suitable For | Behavior / Operation |
|---|---|---|
| `"median"` *(default)* | Numeric columns | Replaces `NaN` with median. Categorical columns safely fall back to `"mode"`. |
| `"mean"` | Symmetric Numeric | Replaces `NaN` with mean. Categorical columns fall back to `"mode"`. |
| `"mode"` | Categorical / Discrete | Replaces `NaN` with the most frequent value. |
| `"ffill"` | Time-series / Sequential | Propagates last valid observation forward. |
| `"bfill"` | Time-series / Sequential | Propagates next valid observation backward. |
| `"interpolate"` | Ordered Numeric | Linear interpolation for numeric columns; forward-fill for non-numeric. |
| `"drop_rows"` | High-quality Target Cols | Drops any row containing `NaN` in specified columns. |
| `"drop_column"` | Heavy-missing Cols | Drops column **only** if null ratio exceeds `drop_threshold` (default `0.6` = $>60\%$). If below threshold, falls back to `"mode"`. |
| `"zero"` | Counts / Sparse Matrix | Replaces numeric nulls with `0`; categorical nulls with `"Unknown"`. |
| `"empty"` | Categoricals / Text | Leaves numeric nulls untouched; replaces categorical nulls with `"Unknown"`. |

```python
# Strategic Imputation Example
cleaned_df, result = handle_missing_values(
    df,
    strategy="median",
    strategy_map={
        "target_col": "drop_rows",
        "abandoned_survey_q": "drop_column",
    },
    drop_threshold=0.6,
)
```

---

## 8. Outlier Detection Guide

Outlier detection identifies extreme values that deviate significantly from the rest of the distribution.

### Supported Outlier Detection Methods

#### 1. Interquartile Range (IQR) Method
Calculates lower and upper bounds using percentiles:
$$\text{Lower Bound} = Q1 - (m \times \text{IQR})$$
$$\text{Upper Bound} = Q3 + (m \times \text{IQR})$$
where $\text{IQR} = Q3 - Q1$ and $m$ is `iqr_multiplier` (default `1.5`).

#### 2. Z-Score Method
- **Standard Z-Score:** $Z = \frac{x - \mu}{\sigma}$. Values with $|Z| > \text{threshold}$ (default `3.0`) are flagged.
- **Modified Z-Score (MAD-based):** Uses Median and Median Absolute Deviation ($\text{MAD}$):
$$Z_{\text{mod}} = \frac{0.6745 \times (x - \text{Median})}{\text{MAD}}$$
Robust against datasets where extreme outliers inflate standard mean and standard deviation.

```python
# Run Modified Z-score outlier check
result = detect_outliers_zscore(df, threshold=3.5, method=ZScoreMethod.MODIFIED)
```

### Core Principle: Detection $\neq$ Deletion

> [!IMPORTANT]
> **Outliers are not automatically deleted by DataPrepToolkit.**
> An outlier may represent a genuine high-value customer order, an extreme weather event, or a critical fraud signal. Outlier detection provides programmatic indices and boolean masks so analysts can inspect and treat outliers deliberately.

---

## 9. Rule-Based Data Validation Guide

### Available Validation Rules

| Rule Type | Parameters | Validation Logic |
|---|---|---|
| `"required"` | `column` | Fails if the column does not exist in the DataFrame. |
| `"not_null"` | `column` | Fails if any cell in the column is `NaN` / `None`. |
| `"no_duplicates"` / `"unique"` | `column` | Fails if duplicate values exist in the column. |
| `"range"` | `min_value`, `max_value` | Fails if numeric values fall outside $[\text{min\_value}, \text{max\_value}]$. `NaN`s are ignored. |
| `"regex"` | `pattern` | Fails if string values do not match the regular expression `pattern`. |
| `"in_set"` | `allowed_values` | Fails if values are not contained within `allowed_values` set. |

```python
rules = [
    dpt.ValidationRule(column="user_id", rule_type="required"),
    dpt.ValidationRule(column="user_id", rule_type="no_duplicates"),
    dpt.ValidationRule(column="age", rule_type="range", min_value=18, max_value=65),
    dpt.ValidationRule(column="zip_code", rule_type="regex", pattern=r"^\d{5}$"),
    dpt.ValidationRule(column="role", rule_type="in_set", allowed_values={"admin", "user", "guest"}),
]

result = dpt.validate_dataset(df, rules)
```

---

## 10. Memory Optimization Guide

### Downcasting Logic & Precision Safety

`optimise_memory()` downcasts numeric columns and converts low-cardinality strings to Pandas `category` types without semantic or value loss:

1. **Integers:** Tries `int8` ($-128 \text{ to } 127$), `int16` ($-32,768 \text{ to } 32,767$), and `int32` in sequence. If values fit within the range, the column is retyped.
2. **Floats:** Attempts downcasting `float64` $\to$ `float32`. Verifies that no `NaN` or infinity is introduced and precision loss is within acceptable limits.
3. **Categoricals:** Converts `object` or `string` columns to `category` dtype if the unique ratio ($\text{unique} / \text{total}$) is $\le \text{category\_threshold}$ (default `0.5`).

```python
# Execute memory optimization
opt_df, result = dpt.optimise_datatypes(df, category_threshold=0.5)

print(f"Memory reduction: {result.savings_pct}%")
```

---

## 11. Profiling & Quality Scoring Mechanics

### Composite Quality Score Formula

The quality score is a deterministic scalar value between `0.0` and `100.0`. It starts at `100.0` and subtracts weighted penalties based on detected issues:

$$\text{Score} = 100.0 - P_{\text{missing}} - P_{\text{duplicate}} - P_{\text{constant}} - P_{\text{cardinality}} - P_{\text{outlier}}$$

Where penalties are calculated using `config.quality_weights`:

- $P_{\text{missing}} = \left(\frac{\text{total missing cells}}{\text{total cells}}\right) \times W_{\text{missing}}$
- $P_{\text{duplicate}} = \left(\frac{\text{duplicate rows}}{\text{total rows}}\right) \times W_{\text{duplicate}}$
- $P_{\text{constant}} = \text{count}(\text{constant columns}) \times W_{\text{constant}}$
- $P_{\text{cardinality}} = \text{count}(\text{high-cardinality categoricals}) \times W_{\text{cardinality}}$
- $P_{\text{outlier}} = \text{count}(\text{columns with outliers}) \times W_{\text{outlier}}$

### Default Weights

```python
{
    "missing": 40.0,
    "duplicate": 20.0,
    "constant": 2.0,
    "high_cardinality": 1.0,
    "outlier": 3.0,
}
```

---

## 12. Centralized Configuration (`ToolkitConfig`)

`ToolkitConfig` is an immutable, centralized dataclass that controls toolkit behaviors.

```python
from datapreptoolkit import ToolkitConfig, EncodingStrategy, ZScoreMethod

config = ToolkitConfig(
    # Duplicate options
    remove_duplicates=True,
    duplicate_subset=("customer_id",),
    duplicate_keep="first",           # 'first', 'last', or 'none'

    # Datetime options
    parse_datetimes=True,
    datetime_format="%Y-%m-%d",
    datetime_columns=["created_at"],

    # Memory options
    optimise_memory=True,

    # Outlier options
    detect_outliers=True,
    outlier_method="zscore",           # 'iqr' or 'zscore'
    iqr_multiplier=1.5,
    zscore_threshold=3.0,
    zscore_method=ZScoreMethod.MODIFIED,

    # Categorical options
    encoding_strategy=EncodingStrategy.LABEL,
    high_cardinality_threshold=0.95,
    constant_threshold=0.99,
    id_column_threshold=0.95,

    # Custom weights
    quality_weights={
        "missing": 50.0,
        "duplicate": 25.0,
        "constant": 5.0,
        "high_cardinality": 2.0,
        "outlier": 5.0,
    },
)
```

---

## 13. Role-Based Workflows

### Beginner Workflow

> *"I have a CSV file and want it cleaned automatically with zero fuss."*

```python
import datapreptoolkit as dpt

# 1. Load CSV
df = dpt.load_csv("data.csv")

# 2. Clean automatically
cleaned_df, _ = dpt.clean_dataset(df)

# 3. Export cleaned result
cleaned_df.to_csv("cleaned_data.csv", index=False)
```

---

### Data Analyst Workflow

> *"I need full control over thresholds, custom validation rules, outlier inspection, and HTML quality reporting."*

```python
import pandas as pd
import datapreptoolkit as dpt

df = pd.read_csv("market_analysis.csv")

# Configure thresholds
config = dpt.ToolkitConfig(
    outlier_method="zscore",
    zscore_method=dpt.ZScoreMethod.MODIFIED,
    zscore_threshold=3.5,
)

# 1. Inspect initial quality
report = dpt.generate_quality_report(df, config=config)
dpt.export_html_report(report, "reports/initial_quality.html")

# 2. Apply selective cleaning
cleaned_df, _ = dpt.handle_missing_values(df, strategy="median", config=config)
cleaned_df, _ = dpt.remove_duplicates(cleaned_df, subset=["user_id"])

# 3. Inspect outliers
outliers = dpt.detect_outliers(cleaned_df, config=config)
outlier_rows = cleaned_df[outliers.outlier_mask.any(axis=1)]
print(f"Inspecting {len(outlier_rows)} potential outlier rows...")

# 4. Validate before visualization
rules = [dpt.ValidationRule(column="revenue", rule_type="range", min_value=0)]
val_res = dpt.validate_dataset(cleaned_df, rules)
if val_res.is_valid:
    print("Dataset validated successfully!")
```

---

### Developer & Pipeline Workflow

> *"I am building an automated ETL pipeline that hands clean data over to downstream modules (`AutoEDA`) or contracts (`automation-core`)."*

```python
import pandas as pd
import datapreptoolkit as dpt
from datapreptoolkit.contracts import build_preprocessing_result
from datapreptoolkit._internal.models import RuntimeAnalysisState

def etl_pipeline_step(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dpt.QualityReport]:
    # 1. Validate DataFrame input
    df = dpt.load_dataframe(raw_df, deep=True)

    # 2. Run Cleaning Pipeline
    cleaned_df, clean_res = dpt.clean_dataset(df)

    # 3. Optimize Memory
    opt_df, opt_res = dpt.optimise_memory(cleaned_df)

    # 4. Quality Threshold Gate
    report = dpt.generate_quality_report(opt_df)
    if report.overall_quality_score < 70.0:
        raise dpt.QualityThresholdError(report.overall_quality_score, 70.0)

    # 5. Optional Contract Envelope Build (Ecosystem adapter)
    state = RuntimeAnalysisState()
    state.parsed_datetime_columns = clean_res.columns_parsed
    contract_result = build_preprocessing_result(opt_df, original_df=raw_df, state=state)

    return opt_df, report
```

---

## 14. Error Handling & Exception Hierarchy

All toolkit exceptions inherit from `DataPrepError`, enabling unified error catching or targeted handling:

```text
DataPrepError (Base)
├── LoadError
│   ├── FileFormatError
│   └── EmptyDatasetError
├── CleaningError
│   ├── InvalidColumnError
│   └── IncompatibleDataError
├── ValidationError
│   └── QualityThresholdError
├── ReportError
└── ConfigError
```

### Exception Handling Example

```python
import datapreptoolkit as dpt

try:
    df = dpt.load_csv("missing_file.csv")
except dpt.FileFormatError as e:
    print(f"Invalid file extension: {e}")
except dpt.EmptyDatasetError as e:
    print(f"File contained no data: {e}")
except dpt.LoadError as e:
    print(f"Failed to load dataset: {e}")
except dpt.DataPrepError as e:
    print(f"General DataPrep error: {e}")
```

---

## 15. Edge Cases & Tested Robustness

DataPrepToolkit is hardened against pathological dataset conditions:

- **Empty DataFrames (0 rows):** `profile_dataset()`, `clean_dataset()`, and `analyze_missing_values()` process empty DataFrames without zero-division or index crashes.
- **Single-Row DataFrames:** Standard deviation falls back to `0.0` instead of `NaN` crashes.
- **Single-Column DataFrames:** Functions run normally without 1D/2D dimensional shape mismatch errors.
- **All-Null Columns:** Flagged as 100% missing; statistics safely compute `0` counts while recommending column drops.
- **Constant Columns (100% Identical):** Flagged correctly even on small DataFrames ($N=50$). IQR/Z-score outlier detection returns $0$ outliers without zero-variance division errors.
- **Extreme Outliers / Infinite Values:** Values like `inf` or `-inf` are flagged as outliers without corrupting finite statistical bounds ($Q1$, $Q3$, Mean, Std).
- **Mixed Missing Values:** `np.nan` and `None` are counted and imputed uniformly.
- **Non-English & Special Header Names:** Full UTF-8 support for column names containing spaces, symbols, dashed strings, or Unicode characters (Spanish, Arabic `التاريخ`, Japanese `価格`).

---

## 16. Offline Execution & AI Independence

DataPrepToolkit operates **100% offline**:

- **No AI Runtime Dependency:** Uses zero remote inference, no OpenAI/Anthropic/Gemini APIs, no LLM calls, and no prompt templates.
- **Deterministic Processing:** All cleaning, profiling, and quality scores are derived from mathematical equations, formal validation rules, and statistical algorithms.
- **Air-Gapped Ready:** Can be installed and executed in secure, network-isolated enterprise environments.

---

## 17. Decision Matrix: "Which Feature Should I Use?"

| I want to... | Use Function | Returns |
|---|---|---|
| Load a CSV file safely | `load_csv(filepath)` | `pd.DataFrame` |
| Inspect shape, memory, and types | `profile_dataset(df)` | `DatasetProfile` |
| Analyze missing cell statistics | `analyze_missing_values(df)` | `MissingValueAnalysis` |
| Impute missing values | `handle_missing_values(df, strategy=...)` | `(pd.DataFrame, CleaningResult)` |
| Deduplicate rows | `remove_duplicates(df, subset=...)` | `(pd.DataFrame, CleaningResult)` |
| Detect negative/invalid values | `detect_invalid_values(df, rules=...)` | `(dict, CleaningResult)` |
| Detect outliers (IQR / Z-Score) | `detect_outliers(df, method=...)` | `OutlierDetection` |
| Validate columns against rules | `validate_dataset(df, rules=...)` | `ValidationResult` |
| Downcast numeric types & category | `optimise_memory(df)` | `(pd.DataFrame, OptimizationResult)` |
| Run full automated clean | `clean_dataset(df)` | `(pd.DataFrame, CleaningResult)` |
| Generate quality score & report | `generate_quality_report(df)` | `QualityReport` |
| Export HTML report file | `export_html_report(report, filepath)` | `str` (Path) |

---

## 18. Complete End-to-End Executable Script

Copy and run this standalone script to verify all major toolkit capabilities in your local environment:

```python
import numpy as np
import pandas as pd
import datapreptoolkit as dpt

def main():
    print(f"DataPrepToolkit Version: {dpt.__version__}")

    # 1. Create a synthetic dirty dataset
    np.random.seed(42)
    n = 100
    df = pd.DataFrame({
        "transaction_id": list(range(1000, 1099)) + [1000], # 1 duplicate
        "user_id": np.random.choice([f"USER_{i:03d}" for i in range(10)], n),
        "amount": np.random.uniform(10.0, 500.0, n),
        "age": np.random.choice([20.0, 30.0, 40.0, np.nan, 150.0], n),
        "created_at": pd.date_range("2024-01-01", periods=n, freq="h").astype(str),
        "status": np.random.choice(["completed", "pending", "failed", None], n),
        "constant_col": ["FIXED"] * n,
    })

    # Add an extreme outlier
    df.loc[5, "amount"] = 99999.0

    print("\n--- 1. Profiling Raw Dataset ---")
    profile = dpt.profile_dataset(df)
    print(f"Raw Shape: {profile.shape} | Memory: {profile.memory_human}")
    print(f"Missing Cells: {profile.total_missing} | Duplicates: {profile.duplicate_rows}")

    print("\n--- 2. Cleaning Pipeline ---")
    config = dpt.ToolkitConfig(
        remove_duplicates=True,
        parse_datetimes=True,
        optimise_memory=True,
        detect_outliers=True,
    )
    cleaned_df, clean_res = dpt.clean_dataset(df, config=config)
    print(f"Cleaned Shape: {cleaned_df.shape}")
    print(f"Clean Messages: {clean_res.messages[:3]}...")

    print("\n--- 3. Outlier Detection ---")
    outliers = dpt.detect_outliers_iqr(cleaned_df)
    print(f"Columns with Outliers: {outliers.columns_with_outliers}")
    if "amount" in outliers.columns:
        amt_info = outliers.columns["amount"]
        print(f"Amount Outliers: {amt_info.outlier_count} bounds: [{amt_info.lower_bound}, {amt_info.upper_bound}]")

    print("\n--- 4. Memory Optimization ---")
    opt_df, opt_res = dpt.optimise_memory(cleaned_df, config=config)
    print(f"Memory Saved: {opt_res.savings_human} ({opt_res.savings_pct}%)")

    print("\n--- 5. Rule Validation ---")
    rules = [
        dpt.ValidationRule(column="transaction_id", rule_type="no_duplicates"),
        dpt.ValidationRule(column="amount", rule_type="range", min_value=0.0, max_value=10000.0),
        dpt.ValidationRule(column="status", rule_type="not_null"),
    ]
    val_res = dpt.validate_dataset(opt_df, rules)
    print(f"Validation Status: {'PASSED' if val_res.is_valid else 'FAILED'}")
    print(f"Rules Passed: {val_res.passed_rules} / {val_res.total_rules}")

    print("\n--- 6. Quality Report & Export ---")
    report = dpt.generate_quality_report(opt_df, config=config)
    print(f"Final Quality Score: {report.overall_quality_score} / 100")
    
    html_path = dpt.export_html_report(report, "reports/sample_quality_report.html")
    print(f"HTML Report generated at: {html_path}")

if __name__ == "__main__":
    main()
```

---

## 19. API Reference Index

### Core Classes & Dataclasses

- `ToolkitConfig`: Centralized immutable configuration object.
- `DatasetProfile`: Dataset profile metrics (shape, memory, type buckets, missing/duplicate counts).
- `ColumnProfile`: Per-column profile metrics and flags.
- `CleaningResult`: Structured log of cleaning changes (`imputations`, `duplicates_dropped`, `messages`).
- `ImputationRecord`: Single column imputation detail (`strategy`, `fill_value`, `rows_filled`).
- `InvalidValueRule`: Custom check rule (`column`, `condition`, `description`).
- `ValidationRule`: Validation constraint (`column`, `rule_type`, `min_value`, `max_value`, `pattern`, `allowed_values`).
- `ValidationResult`: Complete validation execution output (`is_valid`, `passed_rules`, `violations`).
- `ValidationViolation`: Individual rule failure summary (`rule_type`, `violation_count`, `sample_violations`).
- `OutlierDetection`: Aggregate outlier detection result (`columns`, `total_outliers`, `outlier_mask`).
- `ColumnOutlierInfo`: Per-column outlier metrics (`lower_bound`, `upper_bound`, `outlier_indices`).
- `OptimizationResult`: Memory downcasting summary (`memory_before`, `memory_after`, `savings_pct`).
- `QualityReport`: Complete composite report containing profile, scores, and recommendations.

### Enums

- `EncodingStrategy`: `LABEL`, `ONE_HOT`, `FREQUENCY`, `NONE`.
- `ZScoreMethod`: `STANDARD`, `MODIFIED`.

### Functions

- `load_csv(filepath, encoding="utf-8", config=None, **pd_kwargs) -> pd.DataFrame`
- `load_dataframe(df, deep=True, config=None) -> pd.DataFrame`
- `profile_dataset(df, config=None) -> DatasetProfile`
- `analyze_missing_values(df, config=None) -> MissingValueAnalysis`
- `analyze_numeric_columns(df, config=None) -> NumericAnalysis`
- `analyze_categorical_columns(df, config=None) -> CategoricalAnalysis`
- `generate_feature_summaries(df, config=None) -> list[FeatureSummary]`
- `handle_missing_values(df, strategy="median", strategy_map=None, drop_threshold=0.6, config=None) -> (pd.DataFrame, CleaningResult)`
- `parse_datetimes(df, columns=None, datetime_format=None, config=None) -> (pd.DataFrame, CleaningResult)`
- `remove_duplicates(df, subset=None, keep="first", config=None) -> (pd.DataFrame, CleaningResult)`
- `detect_invalid_values(df, rules=None, check_negative_non_negative=True, config=None) -> (dict, CleaningResult)`
- `clean_dataset(df, config=None) -> (pd.DataFrame, CleaningResult)`
- `detect_outliers(df, method=None, config=None) -> OutlierDetection`
- `detect_outliers_iqr(df, multiplier=None, config=None) -> OutlierDetection`
- `detect_outliers_zscore(df, threshold=None, method=None, config=None) -> OutlierDetection`
- `optimise_datatypes(df, category_threshold=0.5, config=None) -> (pd.DataFrame, OptimizationResult)`
- `optimise_memory(df, config=None) -> (pd.DataFrame, OptimizationResult)`
- `validate_dataset(df, rules, config=None) -> ValidationResult`
- `generate_quality_report(df, config=None) -> QualityReport`
- `generate_encoding_recommendations(df, config=None) -> list[EncodingRecommendation]`
- `export_html_report(report, filepath=None, config=None) -> str`
- `export_csv_summary(report, filepath=None, config=None) -> str`
- `build_preprocessing_result(df, *, original_df, state) -> PreprocessingResult`

---

*DataPrepToolkit is open-source software licensed under the [MIT License](LICENSE).*
