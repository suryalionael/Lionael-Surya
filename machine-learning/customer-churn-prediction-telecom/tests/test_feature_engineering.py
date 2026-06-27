import pytest
import pandas as pd
import numpy as np
from src.feature_engineering import FeatureEngineer, get_preprocessing_pipeline

def test_feature_engineer_transformer():
    # Create a small dummy dataframe that has all required input features
    df = pd.DataFrame({
        "gender": ["Female", "Male"],
        "SeniorCitizen": [0, 1],
        "Partner": ["Yes", "No"],
        "Dependents": ["No", "Yes"],
        "tenure": [12, 0],
        "PhoneService": ["Yes", "No"],
        "MultipleLines": ["No", "No phone service"],
        "InternetService": ["Fiber optic", "DSL"],
        "OnlineSecurity": ["Yes", "No"],
        "OnlineBackup": ["No", "Yes"],
        "DeviceProtection": ["No", "No"],
        "TechSupport": ["No", "No"],
        "StreamingTV": ["Yes", "No"],
        "StreamingMovies": ["No", "Yes"],
        "Contract": ["Month-to-month", "Two year"],
        "PaperlessBilling": ["Yes", "No"],
        "PaymentMethod": ["Electronic check", "Mailed check"],
        "MonthlyCharges": [85.0, 45.0],
        "TotalCharges": [1020.0, 0.0]
    })
    
    transformer = FeatureEngineer()
    transformer.fit(df)
    transformed = transformer.transform(df)
    
    # Check that engineered columns are present
    assert "tenure_group" in transformed.columns
    assert "service_count" in transformed.columns
    assert "streaming_count" in transformed.columns
    assert "security_count" in transformed.columns
    assert "avg_monthly_revenue" in transformed.columns
    assert "high_value_customer" in transformed.columns
    assert "tenure_monthly_interaction" in transformed.columns
    
    # Verify service_count calculation
    # Customer 1 services: PhoneService (Yes:1), InternetService (Fiber:1), OnlineSecurity (Yes:1), StreamingTV (Yes:1) = 4
    # Wait, check if MultipleLines is No, so not counted.
    assert transformed.loc[0, "service_count"] == 4
    
    # Customer 2 services: InternetService (DSL:1), OnlineBackup (Yes:1), StreamingMovies (Yes:1) = 3
    assert transformed.loc[1, "service_count"] == 3
    
    # Verify average monthly revenue
    # Customer 1: TotalCharges (1020.0) / tenure (12) = 85.0
    assert transformed.loc[0, "avg_monthly_revenue"] == 85.0
    # Customer 2: TotalCharges (0.0) / tenure (0) -> should prevent division by 0 and equal MonthlyCharges = 45.0
    assert transformed.loc[1, "avg_monthly_revenue"] == 45.0
