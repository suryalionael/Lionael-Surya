import os
import pytest
import pandas as pd
from src.predict import ChurnPredictor
from src.config import CONFIG

@pytest.fixture
def predictor():
    models_dir = CONFIG["paths"]["models_dir"]
    model_path = os.path.join(models_dir, "model.pkl")
    if not os.path.exists(model_path):
        pytest.skip("Model not trained yet, skipping prediction integration tests.")
    return ChurnPredictor()

def test_predict_single_customer(predictor):
    # Standard customer details matching schemas
    customer = {
        "customerID": "1234-TEST",
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 12,
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "Fiber optic",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "Yes",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 85.00,
        "TotalCharges": 1020.00
    }
    
    result = predictor.predict_single(customer)
    
    # Check return structure and keys
    assert "churn_probability" in result
    assert "prediction" in result
    assert "confidence" in result
    assert "risk_category" in result
    assert "recommended_action" in result
    assert "top_risk_drivers" in result
    assert "top_protective_factors" in result
    
    # Assert bounds and data types
    assert 0.0 <= result["churn_probability"] <= 1.0
    assert result["prediction"] in [0, 1]
    assert 0.5 <= result["confidence"] <= 1.0
    assert result["risk_category"] in ["Low", "Medium", "High", "Critical"]
    assert isinstance(result["recommended_action"], str)

def test_predict_batch_customers(predictor):
    # Create batch input
    batch_df = pd.DataFrame([
        {
            "customerID": "1234-A",
            "gender": "Female",
            "SeniorCitizen": 0,
            "Partner": "Yes",
            "Dependents": "No",
            "tenure": 12,
            "PhoneService": "Yes",
            "MultipleLines": "No",
            "InternetService": "Fiber optic",
            "OnlineSecurity": "No",
            "OnlineBackup": "Yes",
            "DeviceProtection": "No",
            "TechSupport": "No",
            "StreamingTV": "Yes",
            "StreamingMovies": "No",
            "Contract": "Month-to-month",
            "PaperlessBilling": "Yes",
            "PaymentMethod": "Electronic check",
            "MonthlyCharges": 85.00,
            "TotalCharges": 1020.00
        },
        {
            "customerID": "1234-B",
            "gender": "Male",
            "SeniorCitizen": 1,
            "Partner": "No",
            "Dependents": "No",
            "tenure": 60,
            "PhoneService": "Yes",
            "MultipleLines": "Yes",
            "InternetService": "DSL",
            "OnlineSecurity": "Yes",
            "OnlineBackup": "Yes",
            "DeviceProtection": "Yes",
            "TechSupport": "Yes",
            "StreamingTV": "No",
            "StreamingMovies": "Yes",
            "Contract": "Two year",
            "PaperlessBilling": "No",
            "PaymentMethod": "Credit card (automatic)",
            "MonthlyCharges": 75.00,
            "TotalCharges": 4500.00
        }
    ])
    
    predictions_df = predictor.predict_batch(batch_df)
    
    assert len(predictions_df) == 2
    assert "customerID" in predictions_df.columns
    assert "churn_probability" in predictions_df.columns
    assert "prediction" in predictions_df.columns
    assert "risk_category" in predictions_df.columns
    assert "recommended_action" in predictions_df.columns
