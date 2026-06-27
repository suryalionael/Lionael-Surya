import pytest
import pandas as pd
import numpy as np
from src.preprocessing import clean_data

def test_clean_data_total_charges():
    # Test dataset with spaces and NaN in TotalCharges
    data = pd.DataFrame({
        "customerID": ["1", "2", "3", "4"],
        "tenure": [0, 10, 0, 5],
        "MonthlyCharges": [20.0, 50.0, 30.0, 80.0],
        "TotalCharges": [" ", "500.0", "", "400.0"],
        "Churn": ["No", "Yes", "No", "No"]
    })
    
    cleaned = clean_data(data, is_train=True)
    
    # Check that spaces and empty strings are handled
    # Row 1: tenure is 0 -> TotalCharges should be 0.0
    assert cleaned.loc[0, "TotalCharges"] == 0.0
    # Row 2: TotalCharges should be float
    assert cleaned.loc[1, "TotalCharges"] == 500.0
    # Row 3: tenure is 0 -> TotalCharges should be 0.0
    assert cleaned.loc[2, "TotalCharges"] == 0.0
    # Row 4: TotalCharges should remain 400.0
    assert cleaned.loc[3, "TotalCharges"] == 400.0
    
    # Check that Churn is mapped to binary
    assert list(cleaned["Churn"]) == [0, 1, 0, 0]

def test_clean_data_missing_total_charges_fallback():
    # Test smart filling when TotalCharges is missing entirely (NaN) and tenure > 0
    data = pd.DataFrame({
        "customerID": ["1"],
        "tenure": [10],
        "MonthlyCharges": [50.0],
        "TotalCharges": [np.nan],
        "Churn": ["No"]
    })
    cleaned = clean_data(data, is_train=True)
    # TotalCharges should be tenure * MonthlyCharges = 500.0
    assert cleaned.loc[0, "TotalCharges"] == 500.0
