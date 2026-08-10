"""
Unit Tests for Data Validation & Business Integrity Rules.
"""
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PARQUET_PATH = PROJECT_ROOT / "data" / "dataset.parquet"

@pytest.fixture(scope="module")
def dataset():
    assert DATA_PARQUET_PATH.exists(), f"Parquet dataset missing at {DATA_PARQUET_PATH}"
    df = pd.read_parquet(DATA_PARQUET_PATH)
    return df

def test_dataset_dimensions(dataset):
    assert len(dataset) == 145898, f"Expected 145,898 rows, got {len(dataset)}"
    assert len(dataset.columns) == 71, f"Expected 71 columns, got {len(dataset.columns)}"

def test_zero_nulls(dataset):
    total_nulls = dataset.isnull().sum().sum()
    assert total_nulls == 0, f"Found {total_nulls} null values in dataset"

def test_zero_duplicate_keys(dataset):
    dup_count = dataset.duplicated(subset=["Product_ID", "City", "Date"]).sum()
    assert dup_count == 0, f"Found {dup_count} duplicate (Product_ID, City, Date) records"

def test_price_positivity(dataset):
    assert (dataset["Cost_Price"] > 0).all(), "Found non-positive Cost_Price"
    assert (dataset["Current_Price"] > 0).all(), "Found non-positive Current_Price"
    assert (dataset["MRP"] > 0).all(), "Found non-positive MRP"
    assert (dataset["Optimal_Price"] > 0).all(), "Found non-positive Optimal_Price"

def test_funnel_monotonicity(dataset):
    funnel_violations = ((dataset["Orders"] > dataset["Cart_Adds"]) |
                         (dataset["Cart_Adds"] > dataset["Clicks"]) |
                         (dataset["Clicks"] > dataset["Views"])).sum()
    assert funnel_violations == 0, f"Found {funnel_violations} funnel monotonicity violations"

def test_price_guardrails_adherence(dataset):
    bound_violations = ((dataset["Optimal_Price"] < dataset["Min_Allowed_Price"]) |
                        (dataset["Optimal_Price"] > dataset["Max_Allowed_Price"])).sum()
    assert bound_violations == 0, f"Found {bound_violations} boundary violations in Optimal_Price"
