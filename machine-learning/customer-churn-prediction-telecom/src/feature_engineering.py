import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from typing import List, Dict, Any, Tuple
from src.config import CONFIG
from src.logger import logger

class FeatureEngineer(BaseEstimator, TransformerMixin):
    """
    Custom Scikit-Learn Transformer to engineer telecom churn features from real-world data:
    1. tenure buckets
    2. average monthly revenue (TotalCharges / tenure)
    3. service count (total services subscribed)
    4. streaming service count (TV + Movies)
    5. security service count (Security + Backup + Device Protection + Tech Support)
    6. high-value customer indicator (MonthlyCharges > 80th percentile)
    7. tenure * MonthlyCharges interaction
    """
    def __init__(self):
        self.high_value_threshold = None
        self.monthly_percentiles = None
        self.categorical_features_output = []
        self.numerical_features_output = []

    def fit(self, X: pd.DataFrame, y: pd.Series = None):
        # Calculate thresholds from the training data for high-value customer flag
        if "MonthlyCharges" in X.columns:
            self.high_value_threshold = X["MonthlyCharges"].quantile(0.80)
            self.monthly_percentiles = X["MonthlyCharges"].describe()
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        
        # 1. Tenure Buckets
        if "tenure" in X.columns:
            # Create discrete numerical groups
            X["tenure_group_12"] = X["tenure"] // 12
            X["tenure_group"] = pd.cut(
                X["tenure"],
                bins=[-1, 12, 24, 48, 60, 100],
                labels=["0-1yr", "1-2yr", "2-4yr", "4-5yr", "5yr+"]
            ).astype(str)
        else:
            X["tenure_group_12"] = 0
            X["tenure_group"] = "0-1yr"
            
        # 2. Service Count (Total services subscribed)
        services = [
            "PhoneService", "MultipleLines", "OnlineSecurity", 
            "OnlineBackup", "DeviceProtection", "TechSupport", 
            "StreamingTV", "StreamingMovies"
        ]
        
        service_cols_present = [col for col in services if col in X.columns]
        service_sum = pd.Series(0, index=X.index)
        for col in service_cols_present:
            service_sum += X[col].apply(lambda val: 1 if val == "Yes" else 0)
            
        if "InternetService" in X.columns:
            service_sum += X["InternetService"].apply(lambda val: 1 if val in ["DSL", "Fiber optic"] else 0)
            
        X["service_count"] = service_sum
        
        # 3. Streaming service count
        streaming_services = ["StreamingTV", "StreamingMovies"]
        streaming_cols_present = [col for col in streaming_services if col in X.columns]
        streaming_sum = pd.Series(0, index=X.index)
        for col in streaming_cols_present:
            streaming_sum += X[col].apply(lambda val: 1 if val == "Yes" else 0)
        X["streaming_count"] = streaming_sum
        
        # 4. Security / Support service count
        security_services = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"]
        security_cols_present = [col for col in security_services if col in X.columns]
        security_sum = pd.Series(0, index=X.index)
        for col in security_cols_present:
            security_sum += X[col].apply(lambda val: 1 if val == "Yes" else 0)
        X["security_count"] = security_sum
        
        # 5. Average Monthly Revenue (TotalCharges / tenure)
        if "TotalCharges" in X.columns and "tenure" in X.columns:
            # Prevent division by zero: if tenure is 0, avg monthly revenue is MonthlyCharges
            X["avg_monthly_revenue"] = np.where(
                X["tenure"] == 0,
                X["MonthlyCharges"] if "MonthlyCharges" in X.columns else 0.0,
                X["TotalCharges"] / X["tenure"]
            )
            # Fallback check
            X["avg_monthly_revenue"] = X["avg_monthly_revenue"].fillna(X["MonthlyCharges"] if "MonthlyCharges" in X.columns else 0.0)
            
        # 6. High-Value Customer Indicator
        if "MonthlyCharges" in X.columns and self.high_value_threshold is not None:
            X["high_value_customer"] = (X["MonthlyCharges"] > self.high_value_threshold).astype(int)
        else:
            X["high_value_customer"] = 0
            
        # 7. Tenure x MonthlyCharges Interaction
        if "tenure" in X.columns and "MonthlyCharges" in X.columns:
            X["tenure_monthly_interaction"] = X["tenure"] * X["MonthlyCharges"]
            
        # Drop customerID if it is present
        id_col = CONFIG["data"]["id_column"]
        if id_col in X.columns:
            X = X.drop(columns=[id_col])
            
        return X

def get_preprocessing_pipeline() -> Tuple[Pipeline, List[str], List[str]]:
    """
    Defines the main Scikit-Learn Pipeline and ColumnTransformer.
    Returns: pipeline, numeric_features, categorical_features
    """
    # Features configured in config.yaml
    config_numerical = CONFIG["data"]["numerical_features"]
    config_categorical = CONFIG["data"]["categorical_features"]
    
    # Define features after custom feature engineering
    # Engineered numeric features
    engineered_numerical = [
        "tenure_group_12",
        "service_count",
        "streaming_count",
        "security_count",
        "avg_monthly_revenue",
        "high_value_customer",
        "tenure_monthly_interaction"
    ]
    
    # Engineered categorical features
    engineered_categorical = [
        "tenure_group"
    ]
    
    all_numerical = config_numerical + engineered_numerical
    all_categorical = config_categorical + engineered_categorical
    
    # Preprocessor for numerical features: Scale values
    num_transformer = Pipeline(steps=[
        ("scaler", StandardScaler())
    ])
    
    # Preprocessor for categorical features: One-Hot Encode
    cat_transformer = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])
    
    # Bundle preprocessing into a ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, all_numerical),
            ("cat", cat_transformer, all_categorical)
        ],
        remainder="drop" # Drop customerID and any unconfigured columns
    )
    
    # Main Pipeline: Feature Engineering first, then preprocessing scaling/encoding
    main_pipeline = Pipeline(steps=[
        ("feature_engineer", FeatureEngineer()),
        ("preprocessor", preprocessor)
    ])
    
    return main_pipeline, all_numerical, all_categorical

def get_feature_names_out(pipeline: Pipeline, numerical_cols: List[str], categorical_cols: List[str]) -> List[str]:
    """Retrieves the list of feature names output from the preprocessor pipeline."""
    # Get the OneHotEncoder step
    preprocessor = pipeline.named_steps["preprocessor"]
    cat_encoder = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    
    # Get encoded feature names
    try:
        encoded_cat_names = cat_encoder.get_feature_names_out(categorical_cols).tolist()
    except Exception:
        # Fallback if fit hasn't run yet
        encoded_cat_names = []
        
    return numerical_cols + encoded_cat_names
