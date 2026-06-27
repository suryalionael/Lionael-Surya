import os
import pytest
from fastapi.testclient import TestClient
from app.main import app, startup_event
from src.config import CONFIG

# Ensure app is initialized (runs startup event to load models)
@pytest.fixture(scope="module")
def client():
    # Trigger startup event to load model
    startup_event()
    return TestClient(app)

def test_api_root(client):
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["app_name"] == "Telecom Customer Churn Prediction System"
    assert "version" in json_data
    assert "documentation" in json_data

def test_api_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    json_data = response.json()
    assert "status" in json_data

def test_api_model_info(client):
    models_dir = CONFIG["paths"]["models_dir"]
    model_path = os.path.join(models_dir, "model.pkl")
    if not os.path.exists(model_path):
        pytest.skip("Model not trained yet, skipping API integration tests.")
        
    response = client.get("/model-info")
    assert response.status_code == 200
    json_data = response.json()
    assert "optimal_threshold" in json_data
    assert "feature_count" in json_data
    assert "features" in json_data
    assert "hyperparameters" in json_data

def test_api_metrics(client):
    models_dir = CONFIG["paths"]["models_dir"]
    metrics_path = os.path.join(models_dir, "metrics.json")
    if not os.path.exists(metrics_path):
        pytest.skip("Model not trained yet, skipping API metrics tests.")
        
    response = client.get("/metrics")
    assert response.status_code == 200
    json_data = response.json()
    assert "test_metrics" in json_data
    assert "test_business_simulation" in json_data

def test_api_predict_valid(client):
    models_dir = CONFIG["paths"]["models_dir"]
    model_path = os.path.join(models_dir, "model.pkl")
    if not os.path.exists(model_path):
        pytest.skip("Model not trained yet, skipping API predict tests.")
        
    payload = {
        "customerID": "7590-VHVEG",
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 1,
        "PhoneService": "No",
        "MultipleLines": "No phone service",
        "InternetService": "DSL",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 29.85,
        "TotalCharges": 29.85
    }
    
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["customerID"] == "7590-VHVEG"
    assert "churn_probability" in json_data
    assert "prediction" in json_data
    assert "confidence" in json_data
    assert "risk_category" in json_data
    assert "recommended_action" in json_data

def test_api_predict_invalid_input(client):
    # Missing required inputs
    payload = {
        "customerID": "7590-VHVEG",
        "gender": "Female"
    }
    
    response = client.post("/predict", json=payload)
    assert response.status_code == 422 # Pydantic validation error
