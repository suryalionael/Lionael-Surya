from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union

class CustomerInput(BaseModel):
    customerID: Optional[str] = Field(default="unknown", description="Unique identifier for the customer")
    gender: str = Field(..., description="Gender of the customer (Male, Female)")
    SeniorCitizen: int = Field(..., ge=0, le=1, description="Whether the customer is a senior citizen (1, 0)")
    Partner: str = Field(..., description="Whether the customer has a partner (Yes, No)")
    Dependents: str = Field(..., description="Whether the customer has dependents (Yes, No)")
    tenure: int = Field(..., ge=0, le=120, description="Number of months the customer has stayed with the company")
    PhoneService: str = Field(..., description="Whether the customer has a phone service (Yes, No)")
    MultipleLines: str = Field(..., description="Whether the customer has multiple lines (Yes, No, No phone service)")
    InternetService: str = Field(..., description="Customer's internet service provider (DSL, Fiber optic, No)")
    OnlineSecurity: str = Field(..., description="Whether the customer has online security (Yes, No, No internet service)")
    OnlineBackup: str = Field(..., description="Whether the customer has online backup (Yes, No, No internet service)")
    DeviceProtection: str = Field(..., description="Whether the customer has device protection (Yes, No, No internet service)")
    TechSupport: str = Field(..., description="Whether the customer has tech support (Yes, No, No internet service)")
    StreamingTV: str = Field(..., description="Whether the customer has streaming TV (Yes, No, No internet service)")
    StreamingMovies: str = Field(..., description="Whether the customer has streaming movies (Yes, No, No internet service)")
    Contract: str = Field(..., description="The contract term of the customer (Month-to-month, One year, Two year)")
    PaperlessBilling: str = Field(..., description="Whether the customer has paperless billing (Yes, No)")
    PaymentMethod: str = Field(..., description="The customer's payment method (Electronic check, Mailed check, Bank transfer (automatic), Credit card (automatic))")
    MonthlyCharges: float = Field(..., ge=0, description="The amount charged to the customer monthly")
    TotalCharges: Union[float, str] = Field(default="", description="The total amount charged to the customer (can be float or empty string)")

    model_config = {
        "json_schema_extra": {
            "example": {
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
        }
    }

class SHAPImpact(BaseModel):
    feature: str = Field(..., description="Feature name")
    shap_value: float = Field(..., description="SHAP value indicating direction and magnitude of risk impact")
    raw_value: Union[float, str] = Field(..., description="Actual value of this feature for the customer")
    business_explanation: str = Field(..., description="Translated explanation of the feature's role in plain business terms")

class PredictionResponse(BaseModel):
    customerID: str = Field(..., description="Unique customer identifier")
    churn_probability: float = Field(..., description="Probability of churn (between 0.0 and 1.0)")
    prediction: int = Field(..., description="Binary churn prediction (1: Churn, 0: Retain) based on the optimal threshold")
    confidence: float = Field(..., description="Model confidence score normalized to [0.5, 1.0]")
    risk_category: str = Field(..., description="Risk category based on churn probability (Low, Medium, High, Critical)")
    recommended_action: str = Field(..., description="Tailored business retention campaign intervention")
    top_risk_drivers: List[SHAPImpact] = Field(..., description="Top features increasing churn risk")
    top_protective_factors: List[SHAPImpact] = Field(..., description="Top features decreasing churn risk/supporting retention")

class BatchPredictionResponse(BaseModel):
    predictions: List[Dict[str, Any]] = Field(..., description="List of predictions, probabilities, and recommendations")
    total_processed: int = Field(..., description="Total records processed in the batch")
