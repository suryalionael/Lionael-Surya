import numpy as np
import pandas as pd

from src.data.cleaning import DataCleaner


def test_clean_column_names():
    df = pd.DataFrame({"Invoice Number": [1], "  Customer-ID": [2]})
    cleaner = DataCleaner()
    result = cleaner.clean_column_names(df)
    assert "invoice_number" in result.columns
    assert "customer_id" in result.columns


def test_drop_duplicates():
    df = pd.DataFrame({"a": [1, 2, 2], "b": [4, 5, 5]})
    cleaner = DataCleaner()
    result = cleaner.drop_duplicates(df)
    assert len(result) == 2


def test_remove_cancelled_invoices():
    df = pd.DataFrame({"invoice": ["C12345", "12345", "C67890", "67890"]})
    cleaner = DataCleaner()
    result = cleaner.remove_cancelled_invoices(df)
    assert len(result) == 2
    assert not any(result["invoice"].astype(str).str.startswith("C"))


def test_remove_returns():
    df = pd.DataFrame({"quantity": [10, -5, 3, -1, 0, 15]})
    cleaner = DataCleaner()
    result = cleaner.remove_returns(df)
    assert list(result["quantity"]) == [10, 3, 0, 15]


def test_remove_invalid_prices():
    df = pd.DataFrame({"price": [10.0, 0.0, -5.0, 2.5]})
    cleaner = DataCleaner()
    result = cleaner.remove_invalid_prices(df)
    assert list(result["price"]) == [10.0, 2.5]


def test_remove_invalid_quantities():
    df = pd.DataFrame({"quantity": [10, -5, 0, 3]})
    cleaner = DataCleaner()
    result = cleaner.remove_invalid_quantities(df)
    assert list(result["quantity"]) == [10, 3]


def test_handle_missing_values():
    df = pd.DataFrame(
        {
            "description": ["a", None, "c"],
            "customer_id": [1.0, None, 3.0],
            "price": [1.0, np.nan, 3.0],
        }
    )
    cleaner = DataCleaner()
    result = cleaner.handle_missing_values(df)
    assert result["description"].iloc[1] == "unknown"
    assert result["customer_id"].iloc[1] == "unknown"
    assert result["price"].iloc[1] == 0.0


def test_clean_online_retail():
    df = pd.DataFrame(
        {
            "Invoice": ["C123", "456", "789"],
            "StockCode": ["A", "B", "C"],
            "Description": ["item1", "item2", None],
            "Quantity": [10, -5, 3],
            "InvoiceDate": ["2010-01-01", "2010-01-02", "2010-01-03"],
            "Price": [5.0, 0.0, 2.5],
            "Customer ID": [1.0, None, 3.0],
            "Country": ["UK", "UK", "UK"],
        }
    )
    cleaner = DataCleaner()
    result = cleaner.clean_online_retail(df)
    assert len(result) > 0
    assert all(result["quantity"] > 0)
    assert all(result["price"] > 0)


def test_detect_outliers_iqr():
    df = pd.DataFrame({"quantity": [1, 2, 3, 4, 5, 100]})
    cleaner = DataCleaner()
    outliers = cleaner.detect_outliers_iqr(df, "quantity")
    assert outliers.iloc[5]


def test_detect_outliers_zscore():
    df = pd.DataFrame({"quantity": [1, 2, 3, 4, 5, 100]})
    cleaner = DataCleaner()
    outliers = cleaner.detect_outliers_zscore(df, "quantity", threshold=2)
    assert outliers.iloc[5]


def test_cap_outliers():
    df = pd.DataFrame({"quantity": [1, 2, 3, 4, 5, 100]})
    cleaner = DataCleaner()
    result = cleaner.cap_outliers(df, "quantity", method="iqr")
    assert result["quantity"].max() < 100
