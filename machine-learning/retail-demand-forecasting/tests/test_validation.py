import numpy as np
import pandas as pd

from src.data.validation import DataValidation


def test_check_missing_values():
    df = pd.DataFrame({"a": [1, 2, np.nan], "b": [4, 5, 6]})
    validator = DataValidation()
    result = validator.check_missing_values(df)
    assert result.loc["a", "missing_count"] == 1


def test_check_duplicates():
    df = pd.DataFrame({"a": [1, 2, 2], "b": [4, 5, 5]})
    validator = DataValidation()
    assert validator.check_duplicates(df) == 1


def test_check_data_types():
    df = pd.DataFrame({"a": [1, 2], "b": [1.0, 2.0], "c": ["x", "y"]})
    validator = DataValidation()
    result = validator.check_data_types(df)
    assert "dtype" in result.columns


def test_validate_online_retail():
    df = pd.DataFrame(
        {
            "quantity": [10, -5, 0, 15],
            "price": [5.0, 0.0, -1.0, 2.0],
            "invoice": ["123", "456", "C789", "012"],
            "invoicedate": pd.date_range("2010-01-01", periods=4),
        }
    )
    validator = DataValidation()
    issues = validator.validate_online_retail(df)
    assert issues["negative_quantity"] == 1
    assert issues["invalid_price"] == 2
    assert issues["cancelled_invoices"] == 1
