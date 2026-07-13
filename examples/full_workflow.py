{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# DataPrepToolkit - Full Workflow Example\n",
    "\n",
    "This notebook demonstrates the complete data preprocessing pipeline using DataPrepToolkit:\n",
    "\n",
    "1. **Load** - Load and profile a dataset\n",
    "2. **Validate** - Validate data quality rules\n",
    "3. **Analyze** - Analyze missing values, numeric, and categorical columns\n",
    "4. **Clean** - Handle missing values, duplicates, and invalid data\n",
    "5. **Optimize** - Reduce memory usage with datatype optimization\n",
    "6. **Detect Outliers** - Identify outliers using IQR or Z-score methods\n",
    "7. **Report** - Generate a professional HTML quality report"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Setup"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import pandas as pd\n",
    "import numpy as np\n",
    "\n",
    "from datapreptoolkit import (\n",
    "    # Config\n",
    "    ToolkitConfig, EncodingStrategy, ZScoreMethod,\n",
    "    # Loader\n",
    "    load_csv, profile_dataset,\n",
    "    # Analyzer\n",
    "    analyze_missing_values, analyze_numeric_columns,\n",
    "    analyze_categorical_columns, generate_feature_summaries,\n",
    "    # Cleaner\n",
    "    handle_missing_values, parse_datetimes, remove_duplicates,\n",
    "    clean_dataset,\n",
    "    # Optimizer\n",
    "    optimise_memory,\n",
    "    # Outliers\n",
    "    detect_outliers,\n",
    "    # Validator\n",
    "    validate_dataset, ValidationRule,\n",
    "    # Reporter\n",
    "    generate_quality_report, export_html_report, export_csv_summary,\n",
    ")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Create Sample Dataset\n",
    "\n",
    "We create a realistic employee dataset with intentional data quality issues:\n",
    "- Missing values in age, salary, and join_date\n",
    "- Potential outliers in salary\n",
    "- Mixed data types"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "np.random.seed(42)\n",
    "n = 200\n",
    "\n",
    "departments = [\"Engineering\", \"Marketing\", \"Sales\", \"HR\", \"Finance\", \"Operations\"]\n",
    "\n",
    "df = pd.DataFrame({\n",
    "    \"employee_id\": range(1001, 1001 + n),\n",
    "    \"name\": [f\"Employee_{i}\" for i in range(1, n + 1)],\n",
    "    \"age\": np.random.choice([np.nan, 22, 25, 28, 30, 35, 40, 45, 50, 55, 60, 65], n),\n",
    "    \"salary\": np.concatenate([\n",
    "        np.random.uniform(40000, 120000, n - 5),\n",
    "        [250000, 300000, 15, 0, -5000]  # outliers\n",
    "    ]),\n",
    "    \"department\": np.random.choice(departments, n),\n",
    "    \"join_date\": pd.date_range(\"2018-01-01\", periods=n, freq=\"5D\").astype(str),\n",
    "    \"is_active\": np.random.choice([True, False], n, p=[0.8, 0.2]),\n",
    "    \"performance_score\": np.random.uniform(1, 10, n),\n",
    "})\n",
    "\n",
    "# Inject missing values\n",
    "df.loc[np.random.choice(df.index, 20), \"age\"] = np.nan\n",
    "df.loc[np.random.choice(df.index, 15), \"salary\"] = np.nan\n",
    "df.loc[np.random.choice(df.index, 10), \"join_date\"] = np.nan\n",
    "\n",
    "print(f\"Dataset shape: {df.shape}\")\n",
    "df.head(10)"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 1: Configure the Toolkit\n",
    "\n",
    "DataPrepToolkit uses a central `ToolkitConfig` to control all behavior.\n",
    "You can customize quality scoring weights, outlier detection, encoding, and more."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "config = ToolkitConfig(\n",
    "    # Duplicate handling\n",
    "    remove_duplicates=True,\n",
    "    \n",
    "    # Memory optimization\n",
    "    optimize_memory=True,\n",
    "    \n",
    "    # Outlier detection\n",
    "    detect_outliers=True,\n",
    "    outlier_method=\"iqr\",\n",
    "    iqr_multiplier=1.5,\n",
    "    \n",
    "    # Encoding\n",
    "    encoding_strategy=EncodingStrategy.LABEL,\n",
    "    \n",
    "    # Custom quality scoring weights\n",
    "    quality_weights={\n",
    "        \"missing\": 40.0,\n",
    "        \"duplicate\": 20.0,\n",
    "        \"constant\": 2.0,\n",
    "        \"high_cardinality\": 1.0,\n",
    "        \"outlier\": 3.0,\n",
    "    },\n",
    ")\n",
    "\n",
    "print(\"Configuration created successfully!\")\n",
    "print(f\"  Outlier method: {config.outlier_method}\")\n",
    "print(f\"  Quality weights: {config.quality_weights}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 2: Profile the Dataset\n",
    "\n",
    "The profiler gives you a comprehensive overview of your data:\n",
    "- Shape, memory usage, column types\n",
    "- Missing values, duplicates, constant columns\n",
    "- Potential IDs, target columns, and data leakage"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "profile = profile_dataset(df, config)\n",
    "\n",
    "print(\"=== Dataset Profile ===\")\n",
    "print(f\"  Shape: {profile.shape}\")\n",
    "print(f\"  Memory: {profile.memory_human}\")\n",
    "print(f\"  Quality Score: {profile.overall_quality_score}/100\")\n",
    "print(f\"  Missing columns: {profile.missing_columns}\")\n",
    "print(f\"  Duplicate rows: {profile.duplicate_rows} ({profile.duplicate_ratio:.1%})\")\n",
    "print(f\"  Constant columns: {profile.constant_columns}\")\n",
    "print(f\"  High cardinality: {profile.high_cardinality_columns}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 3: Validate Data Quality Rules\n",
    "\n",
    "Before cleaning, define and validate business rules:\n",
    "- Age must be between 0 and 120\n",
    "- Salary must be positive\n",
    "- Employee ID must be unique\n",
    "- Department must be in the allowed set"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "rules = [\n",
    "    ValidationRule(column=\"age\", rule_type=\"range\", min_value=0, max_value=120),\n",
    "    ValidationRule(column=\"salary\", rule_type=\"range\", min_value=0),\n",
    "    ValidationRule(column=\"employee_id\", rule_type=\"no_duplicates\"),\n",
    "    ValidationRule(\n",
    "        column=\"department\",\n",
    "        rule_type=\"in_set\",\n",
    "        allowed_values=set(departments),\n",
    "    ),\n",
    "    ValidationRule(column=\"name\", rule_type=\"not_null\"),\n",
    "]\n",
    "\n",
    "val_result = validate_dataset(df, rules)\n",
    "\n",
    "print(f\"=== Validation Results ===\")\n",
    "print(f\"  Rules checked: {val_result.total_rules}\")\n",
    "print(f\"  Passed: {val_result.passed_rules}\")\n",
    "print(f\"  Failed: {val_result.failed_rules}\")\n",
    "print(f\"  Is valid: {val_result.is_valid}\")\n",
    "\n",
    "if val_result.violations:\n",
    "    print(\"\\nViolations:\")\n",
    "    for v in val_result.violations:\n",
    "        print(f\"  - [{v.rule_type}] {v.column}: {v.violation_count} violations ({v.violation_pct:.1f}%)\")\n",
    "        if v.sample_violations:\n",
    "            print(f\"    Samples: {v.sample_violations[:3]}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 4: Analyze the Data\n",
    "\n",
    "Deep-dive analysis of missing values, numeric distributions, and categorical frequencies."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Missing Value Analysis\n",
    "missing = analyze_missing_values(df, config)\n",
    "print(\"=== Missing Values ===\")\n",
    "print(f\"  Total missing: {missing.total_missing} / {missing.total_cells} ({missing.overall_missing_pct:.2f}%)\")\n",
    "print(f\"  Complete columns: {len(missing.complete_columns)}\")\n",
    "print(f\"  Columns with missing: {list(missing.recommended_actions.keys())}\")\n",
    "print(f\"\\n  Recommended actions:\")\n",
    "for col, action in missing.recommended_actions.items():\n",
    "    print(f\"    {col}: {action}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Numeric Analysis\n",
    "numeric = analyze_numeric_columns(df, config)\n",
    "print(\"=== Numeric Columns ===\")\n",
    "print(f\"  Analyzed: {list(numeric.columns.keys())}\")\n",
    "print(f\"  Highly skewed: {numeric.highly_skewed}\")\n",
    "print(f\"  With outliers: {numeric.columns_with_outliers}\")\n",
    "\n",
    "for name, stats in numeric.columns.items():\n",
    "    print(f\"\\n  {name}:\")\n",
    "    print(f\"    Mean: {stats.mean:.2f}, Median: {stats.median:.2f}, Std: {stats.std:.2f}\")\n",
    "    print(f\"    Range: [{stats.min:.2f}, {stats.max:.2f}], Outliers: {stats.outlier_count_iqr}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Categorical Analysis\n",
    "categorical = analyze_categorical_columns(df, config)\n",
    "print(\"=== Categorical Columns ===\")\n",
    "print(f\"  Analyzed: {list(categorical.columns.keys())}\")\n",
    "print(f\"  High cardinality: {categorical.high_cardinality_columns}\")\n",
    "\n",
    "for name, stats in categorical.columns.items():\n",
    "    print(f\"\\n  {name}:\")\n",
    "    print(f\"    Unique: {stats.unique_count}, Mode: {stats.mode}\")\n",
    "    print(f\"    Top values: {stats.top_values[:3]}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 5: Clean the Data\n",
    "\n",
    "Apply cleaning operations based on the analysis."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Handle missing values with median/mode imputation\n",
    "df_cleaned, clean_result = handle_missing_values(df, strategy=\"median\", config=config)\n",
    "\n",
    "print(\"=== Missing Value Treatment ===\")\n",
    "print(f\"  Rows before: {clean_result.rows_before}, After: {clean_result.rows_after}\")\n",
    "print(f\"  Imputations: {len(clean_result.imputations)}\")\n",
    "for imp in clean_result.imputations:\n",
    "    print(f\"    {imp.column}: {imp.strategy} ({imp.rows_filled} rows filled)\")\n",
    "\n",
    "print(f\"\\n  Missing before: {df.isnull().sum().sum()}\")\n",
    "print(f\"  Missing after: {df_cleaned.isnull().sum().sum()}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Remove duplicates\n",
    "df_deduped, dup_result = remove_duplicates(df_cleaned, config=config)\n",
    "print(f\"Duplicates removed: {dup_result.duplicates_dropped}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 6: Optimize Memory\n",
    "\n",
    "Down-cast numeric types and convert low-cardinality objects to categories."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "df_optimized, opt_result = optimise_memory(df_deduped, config)\n",
    "\n",
    "print(\"=== Memory Optimization ===\")\n",
    "print(f\"  Before: {opt_result.memory_before_human}\")\n",
    "print(f\"  After:  {opt_result.memory_after_human}\")\n",
    "print(f\"  Saved:  {opt_result.savings_mb} MB ({opt_result.savings_pct:.1f}% reduction)\")\n",
    "print(f\"\\n  Column changes:\")\n",
    "for change in opt_result.column_changes:\n",
    "    print(f\"    {change.column}: {change.dtype_before} -> {change.dtype_after}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 7: Detect Outliers\n",
    "\n",
    "Identify outliers using IQR or Z-score methods."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "outlier_result = detect_outliers(df_optimized, config=config)\n",
    "\n",
    "print(\"=== Outlier Detection ===\")\n",
    "print(f\"  Method: {outlier_result.method}\")\n",
    "print(f\"  Total outliers: {outlier_result.total_outliers}\")\n",
    "print(f\"  Columns with outliers: {outlier_result.columns_with_outliers}\")\n",
    "\n",
    "for name, info in outlier_result.columns.items():\n",
    "    if info.outlier_count > 0:\n",
    "        print(f\"\\n  {name}:\")\n",
    "        print(f\"    Outliers: {info.outlier_count} ({info.outlier_pct:.1f}%)\")\n",
    "        print(f\"    Bounds: [{info.lower_bound:.2f}, {info.upper_bound:.2f}]\")\n",
    "        print(f\"    Min outlier: {info.min_outlier:.2f}, Max outlier: {info.max_outlier:.2f}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Step 8: Generate Quality Report\n",
    "\n",
    "Generate a comprehensive HTML report that looks like a professional data audit."
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "report = generate_quality_report(df, config)\n",
    "\n",
    "print(\"=== Quality Report ===\")\n",
    "print(f\"  Quality Score: {report.overall_quality_score}/100\")\n",
    "print(f\"  Shape: {report.shape}\")\n",
    "print(f\"  Memory: {report.memory_human}\")\n",
    "print(f\"\\n  Encoding Recommendations:\")\n",
    "for rec in report.encoding_recommendations:\n",
    "    print(f\"    {rec.column}: {rec.strategy} ({rec.reason})\")\n",
    "\n",
    "print(f\"\\n  Cleaning Recommendations:\")\n",
    "for rec in report.cleaning_recommendations:\n",
    "    print(f\"    - {rec}\")"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "# Export as HTML\n",
    "html_path = export_html_report(report, \"reports/example_report.html\")\n",
    "print(f\"HTML report saved to: {html_path}\")\n",
    "\n",
    "# Export as CSV\n",
    "csv_path = export_csv_summary(report, \"reports/example_summary.csv\")\n",
    "print(f\"CSV summary saved to: {csv_path}\")"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Summary\n",
    "\n",
    "This notebook demonstrated the complete DataPrepToolkit workflow:\n",
    "\n",
    "| Step | Module | What it does |\n",
    "|------|--------|-------------|\n",
    "| 1 | `ToolkitConfig` | Configure all behavior centrally |\n",
    "| 2 | `profile_dataset` | Get an overview of your data |\n",
    "| 3 | `validate_dataset` | Check business rules |\n",
    "| 4 | `analyze_*` | Deep-dive analysis |\n",
    "| 5 | `clean_dataset` | Handle missing values, duplicates |\n",
    "| 6 | `optimise_memory` | Reduce memory footprint |\n",
    "| 7 | `detect_outliers` | Find anomalous values |\n",
    "| 8 | `generate_quality_report` | Generate professional reports |"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.11.0"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
