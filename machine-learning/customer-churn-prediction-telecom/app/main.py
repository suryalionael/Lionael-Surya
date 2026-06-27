import os
import sys
import logging
from fastapi import FastAPI, HTTPException, status
from typing import Any, Dict, List
import pandas as pd

# Add the project root to PYTHONPATH to ensure src module can be resolved
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.schemas.customer import (
    CustomerInput,
    PredictionResponse,
    BatchPredictionResponse,
)
from src.predict import ChurnPredictor
from src.utils import load_json
from src.config import CONFIG
from src.drift import evaluate_drift

# Configure logger for FastAPI app
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api")

app = FastAPI(
    title="Telecom Customer Churn Prediction API",
    description="Production-grade Machine Learning API to predict, explain, and recommend interventions for telecom customer churn.",
    version="1.0.0",
)

# Global predictor instance
predictor = None


def _customer_to_dict(customer: CustomerInput) -> Dict[str, Any]:
    """Supports both Pydantic v1 and v2 request models."""
    if hasattr(customer, "model_dump"):
        return customer.model_dump()
    return customer.dict()


@app.on_event("startup")
def startup_event():
    """Loads the model artifacts on API startup."""
    global predictor
    models_dir = CONFIG["paths"]["models_dir"]
    model_path = os.path.join(models_dir, "model.pkl")

    if not os.path.exists(model_path):
        logger.error(
            f"Model file not found at {model_path}. You must run the training pipeline first."
        )
        # We don't raise an exception on startup to allow testing container build without artifacts present,
        # but subsequent calls will fail if not loaded.
    else:
        try:
            predictor = ChurnPredictor()
            logger.info("Churn predictor loaded successfully on API startup.")
        except Exception as e:
            logger.error(f"Error loading ChurnPredictor: {e}")


@app.get("/", tags=["General"])
def read_root():
    """Returns basic details about the API."""
    return {
        "app_name": "Telecom Customer Churn Prediction System",
        "version": "1.0.0",
        "description": "Production API for real-time customer churn prediction, explanation, and retention planning.",
        "documentation": "/docs",
    }


@app.get("/health", tags=["Monitoring"])
def health_check():
    """Checks the health of the API and verifies if model is loaded."""
    if predictor is None:
        return {
            "status": "unhealthy",
            "message": "Model is not loaded. Please train the model and restart the service.",
        }
    return {"status": "healthy", "model_loaded": True}


@app.get("/metrics", tags=["Monitoring"])
def get_metrics():
    """Returns the model performance and business evaluation metrics."""
    metrics_path = os.path.join(CONFIG["paths"]["models_dir"], "metrics.json")
    if not os.path.exists(metrics_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model metrics file not found. Ensure the model has been trained and evaluated.",
        )
    try:
        metrics = load_json(metrics_path)
        return metrics
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load metrics: {e}",
        )


@app.get("/model-info", tags=["General"])
def get_model_info():
    """Returns metadata about the deployed model, including feature schema and decision threshold."""
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded.",
        )

    best_params_path = os.path.join(CONFIG["paths"]["models_dir"], "best_params.json")
    best_params = {}
    if os.path.exists(best_params_path):
        best_params = load_json(best_params_path)

    return {
        "optimal_threshold": predictor.optimal_threshold,
        "feature_count": len(predictor.feature_names),
        "features": predictor.feature_names,
        "hyperparameters": best_params,
    }


@app.post("/predict", response_model=PredictionResponse, tags=["Inference"])
def predict(customer: CustomerInput):
    """
    Predicts churn probability, binary prediction, confidence, and tailored recommendations
    for a single customer. Returns top SHAP drivers for explainability.
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded. Ensure training pipeline has run.",
        )

    try:
        customer_dict = _customer_to_dict(customer)
        result = predictor.predict_single(customer_dict)
        # Ensure customer ID is set
        result["customerID"] = customer.customerID or "unknown"
        return result
    except Exception as e:
        logger.error(f"Error predicting single record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {e}",
        )


@app.post("/batch_predict", response_model=BatchPredictionResponse, tags=["Inference"])
def batch_predict(customers: List[CustomerInput]):
    """
    Predicts churn probability and recommendations for a batch of customers.
    """
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model is not loaded.",
        )

    try:
        # Convert list of Pydantic models to a pandas DataFrame
        records = [_customer_to_dict(c) for c in customers]
        df_batch = pd.DataFrame(records)

        # Batch predict
        df_results = predictor.predict_batch(df_batch)

        # Convert df back to list of dicts
        predictions = df_results.to_dict(orient="records")

        return {"predictions": predictions, "total_processed": len(predictions)}
    except Exception as e:
        logger.error(f"Error predicting batch records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch prediction failed: {e}",
        )


@app.post("/drift", tags=["Monitoring"])
def monitor_drift(customers: List[CustomerInput]):
    """
    Compares a batch of recent customer records against the training reference profile.
    """
    reference_path = os.path.join(CONFIG["paths"]["models_dir"], "drift_reference.json")
    if not os.path.exists(reference_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Drift reference file not found. Run the training pipeline to generate it.",
        )

    try:
        records = [_customer_to_dict(c) for c in customers]
        df_batch = pd.DataFrame(records)
        reference = load_json(reference_path)
        return evaluate_drift(reference, df_batch)
    except Exception as e:
        logger.error(f"Error monitoring drift: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drift monitoring failed: {e}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
