"""Shared fixtures for DataPrepToolkit test suite."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from datapreptoolkit import ToolkitConfig


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create a sample DataFrame with intentional data quality issues."""
    np.random.seed(42)
    n = 100

    data = {
        "id": range(1, n + 1),
        "name": [f"Person_{i}" for i in range(1, n + 1)],
        "age": np.random.choice([np.nan, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0], n),
        "salary": np.random.uniform(30000, 120000, n),
        "department": np.random.choice(
            ["Engineering", "Marketing", "Sales", "HR", "Finance"], n
        ),
        "join_date": pd.date_range("2020-01-01", periods=n, freq="D").astype(str),
        "is_active": np.random.choice([True, False], n),
    }

    # Add some missing values
    df = pd.DataFrame(data)
    df.loc[5, "salary"] = np.nan
    df.loc[10, "salary"] = np.nan
    df.loc[15, "age"] = np.nan
    df.loc[20, "join_date"] = np.nan

    return df


@pytest.fixture
def minimal_df() -> pd.DataFrame:
    """Create a minimal clean DataFrame for basic testing."""
    return pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": [10.0, 20.0, 30.0, 40.0, 50.0],
            "c": ["x", "y", "z", "x", "y"],
        }
    )


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """Create an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def constant_df() -> pd.DataFrame:
    """Create a DataFrame with constant columns."""
    return pd.DataFrame(
        {
            "const_col": [1] * 10,
            "normal_col": range(10),
            "all_null": [np.nan] * 10,
        }
    )


@pytest.fixture
def duplicate_df() -> pd.DataFrame:
    """Create a DataFrame with duplicate rows."""
    data = {
        "id": [1, 2, 2, 3, 3, 3],
        "value": ["a", "b", "b", "c", "c", "c"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def high_cardinality_df() -> pd.DataFrame:
    """Create a DataFrame with high cardinality columns."""
    return pd.DataFrame(
        {
            "id": range(100),
            "unique_col": [f"unique_{i}" for i in range(100)],
            "low_card": np.random.choice(["A", "B", "C"], 100),
        }
    )


@pytest.fixture
def default_config() -> ToolkitConfig:
    """Create a default ToolkitConfig."""
    return ToolkitConfig()


@pytest.fixture
def test_csv_path(tmp_path: Path) -> Path:
    """Create a temporary CSV file for testing."""
    df = pd.DataFrame(
        {
            "col1": [1, 2, 3],
            "col2": ["a", "b", "c"],
        }
    )
    path = tmp_path / "test.csv"
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def reports_dir(tmp_path: Path) -> Path:
    """Create a temporary reports directory."""
    reports = tmp_path / "reports"
    reports.mkdir()
    return reports
