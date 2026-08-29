import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "clean_data.py"
SPEC = importlib.util.spec_from_file_location("clean_data", SCRIPT_PATH)
clean_data = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(clean_data)


def test_normalize_columns_cleans_names_without_mutating_input():
    original = pd.DataFrame([[1, "x"]], columns=[" Customer ID ", "Product-Name"])

    result = clean_data.normalize_columns(original)

    assert list(result.columns) == ["customer_id", "product_name"]
    assert list(original.columns) == [" Customer ID ", "Product-Name"]


def test_normalize_columns_rejects_duplicate_normalized_names():
    frame = pd.DataFrame([[1, 2]], columns=["Order ID", "order-id"])

    with pytest.raises(ValueError, match="duplicates"):
        clean_data.normalize_columns(frame)


def test_clean_missing_values_removes_empty_rows_and_cleans_values():
    frame = pd.DataFrame(
        {
            "customer_name": pd.Series([" Alice ", None, "Bob"], dtype=object),
            "total_value": [10.0, np.nan, 30.0],
            "order_date": ["2024-01-01", "2024-01-02", "2024-01-03"],
        }
    )
    frame.loc[1] = [None, np.nan, None]

    result = clean_data.clean_missing_values(frame)

    assert len(result) == 2
    assert result.loc[0, "customer_name"] == "Alice"
    assert result["total_value"].tolist() == [10.0, 30.0]
    assert pd.api.types.is_datetime64_any_dtype(result["order_date"])


def test_clean_missing_values_fills_numeric_missing_values_with_median():
    frame = pd.DataFrame({"rating_score": [1, None, 5], "record_id": ["a", "b", "c"]})

    result = clean_data.clean_missing_values(frame)

    assert result["rating_score"].tolist() == [1.0, 3.0, 5.0]
