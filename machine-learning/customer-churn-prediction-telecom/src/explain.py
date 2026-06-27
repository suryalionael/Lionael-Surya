import os
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt
from typing import Dict, Any, List, Tuple
from src.config import CONFIG
from src.logger import logger

def get_shap_explainer(model: Any, X_train: np.ndarray) -> shap.Explainer:
    """Creates a SHAP explainer for the given model and training data."""
    logger.info("Initializing SHAP explainer...")
    
    # Extract base estimator if model is CalibratedClassifierCV
    if hasattr(model, "estimator"):
        base_model = model.estimator
    elif hasattr(model, "calibrated_classifiers_") and len(model.calibrated_classifiers_) > 0:
        base_model = model.calibrated_classifiers_[0].estimator
    else:
        base_model = model

    # If base_model is a FrozenEstimator, unwrap it to get the raw model
    if base_model.__class__.__name__ == "FrozenEstimator":
        base_model = base_model.estimator

    # Create explainer depending on model type
    try:
        # Check if it's a tree-based model (RandomForest, XGBoost, LightGBM)
        model_name = base_model.__class__.__name__.lower()
        if "forest" in model_name or "xgb" in model_name or "lgb" in model_name:
            explainer = shap.TreeExplainer(base_model)
        elif "logistic" in model_name:
            explainer = shap.LinearExplainer(base_model, X_train)
        else:
            explainer = shap.Explainer(base_model, X_train)
    except Exception as e:
        logger.warning(f"Could not use specialized explainer. Falling back to default SHAP Explainer. Error: {e}")
        explainer = shap.Explainer(base_model, X_train)
        
    return explainer

def generate_global_shap_plots(
    explainer: shap.Explainer, 
    X_val: np.ndarray, 
    feature_names: List[str], 
    figures_dir: str = None
) -> None:
    """Generates global SHAP summary and bar plots and saves them to disk."""
    if figures_dir is None:
        figures_dir = CONFIG["paths"]["figures_dir"]
    os.makedirs(figures_dir, exist_ok=True)
    
    logger.info("Computing global SHAP values...")
    shap_values = explainer(X_val)
    
    # Handle multi-class shap values (binary classification output could be a list of 2 arrays, or 3D)
    # TreeExplainer on classification can return shapes like (N, D, 2) or (N, D)
    if isinstance(shap_values, list):
        # Multi-class or binary list
        shap_values_to_plot = shap_values[1] # positive class
    elif len(shap_values.shape) == 3:
        # Shape is (N, D, 2)
        shap_values_to_plot = shap_values[:, :, 1]
    else:
        shap_values_to_plot = shap_values
        
    # 1. Summary Plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values_to_plot, X_val, feature_names=feature_names, show=False)
    plt.title("Global Feature Importance (SHAP Summary)", fontsize=14, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "shap_summary_plot.png"), dpi=300)
    plt.close()
    
    # 2. Bar Plot
    plt.figure(figsize=(10, 6))
    # Create a separate explanation object to plot bar chart correctly
    explanation_obj = shap.Explanation(
        values=shap_values_to_plot.values,
        base_values=shap_values_to_plot.base_values,
        data=X_val,
        feature_names=feature_names
    )
    shap.plots.bar(explanation_obj, max_display=15, show=False)
    plt.title("Feature Importance (SHAP Bar Plot)", fontsize=14, pad=15)
    plt.tight_layout()
    plt.savefig(os.path.join(figures_dir, "shap_bar_plot.png"), dpi=300)
    plt.close()
    
    logger.info("Saved global SHAP plots successfully.")

def explain_single_customer(
    explainer: shap.Explainer, 
    customer_vector: np.ndarray, 
    feature_names: List[str]
) -> Tuple[Dict[str, float], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Computes SHAP values for a single customer and return drivers translated to business language.
    """
    # customer_vector should be shape (1, num_features)
    if len(customer_vector.shape) == 1:
        customer_vector = customer_vector.reshape(1, -1)
        
    shap_vals = explainer(customer_vector)
    
    # Extract positive class SHAP values
    if isinstance(shap_vals, list):
        single_shap = shap_vals[1]
    elif len(shap_vals.shape) == 3:
        single_shap = shap_vals[:, :, 1]
    else:
        single_shap = shap_vals
        
    shap_scores = single_shap.values[0]
    raw_values = single_shap.data[0]
    
    # Map feature names to SHAP scores and raw values
    feature_impacts = []
    for name, score, raw_val in zip(feature_names, shap_scores, raw_values):
        feature_impacts.append({
            "feature": name,
            "shap_value": float(score),
            "raw_value": float(raw_val) if isinstance(raw_val, (int, float, np.number)) else str(raw_val)
        })
        
    # Sort by absolute SHAP value
    feature_impacts.sort(key=lambda x: abs(x["shap_value"]), reverse=True)
    
    # Separate Risk Drivers (positive SHAP) and Protective Factors (negative SHAP)
    risk_drivers = [x for x in feature_impacts if x["shap_value"] > 0.001]
    protective_factors = [x for x in feature_impacts if x["shap_value"] < -0.001]
    
    # Generate business language translations
    translated_risks = []
    for r in risk_drivers[:4]: # top 4
        translated_risks.append({
            "feature": r["feature"],
            "shap_value": r["shap_value"],
            "raw_value": r["raw_value"],
            "business_explanation": translate_feature_to_business(r["feature"], r["raw_value"], is_risk=True)
        })
        
    translated_protects = []
    for p in protective_factors[:4]: # top 4
        translated_protects.append({
            "feature": p["feature"],
            "shap_value": p["shap_value"],
            "raw_value": p["raw_value"],
            "business_explanation": translate_feature_to_business(p["feature"], p["raw_value"], is_risk=False)
        })
        
    shap_dict = {f["feature"]: f["shap_value"] for f in feature_impacts}
    
    return shap_dict, translated_risks, translated_protects

def translate_feature_to_business(feature_name: str, raw_value: Any, is_risk: bool) -> str:
    """Translates a technical feature impact into friendly, non-technical business descriptions."""
    # Match categorical features
    if "Contract" in feature_name:
        if "Month-to-month" in feature_name:
            return "Being on a Month-to-Month contract is a major risk factor, making it easy for the customer to cancel."
        elif "Two year" in feature_name:
            return "The 2-Year Contract provides high security and strongly protects against churn."
        elif "One year" in feature_name:
            return "The 1-Year Contract acts as a stabilizer, decreasing churn risk compared to month-to-month."
            
    if "tenure" in feature_name:
        if feature_name == "tenure":
            if is_risk:
                return f"A low tenure ({int(raw_value)} months) indicates a new customer who is still in the high-risk onboarding phase."
            else:
                return f"A long tenure ({int(raw_value)} months) indicates high customer loyalty and lowers churn risk."
        elif "tenure_group" in feature_name:
            if "0-1yr" in feature_name:
                return "The customer is in their first year, which is historically the highest-risk churn period."
            elif "5yr+" in feature_name:
                return "Being a long-term customer (5+ years) indicates strong brand loyalty."
                
    if "InternetService" in feature_name:
        if "Fiber optic" in feature_name:
            return "Having Fiber Optic internet increases risk, often tied to higher price tiers or service reliability issues."
        elif "DSL" in feature_name:
            return "Having DSL internet is associated with stable retention, though it represents a lower revenue bracket."
        elif "No" in feature_name:
            return "Not having internet service decreases churn risk, as these are typically low-complexity accounts."
            
    if "PaymentMethod" in feature_name:
        if "Electronic check" in feature_name:
            return "Paying via Electronic Check is highly linked to churn, possibly due to manual monthly intervention requirements."
        elif "automatic" in feature_name:
            return "Using an automatic payment method (credit card/bank transfer) reduces billing friction and increases retention."
            
    if "OnlineSecurity" in feature_name and "Yes" in feature_name:
        return "Subscribing to Online Security is a major protective factor, increasing customer dependency and product stickiness."
    if "TechSupport" in feature_name and "Yes" in feature_name:
        return "Having active Tech Support subscription indicates the customer receives help, decreasing churn risk."
    if "PaperlessBilling" in feature_name:
        if "Yes" in feature_name and is_risk:
            return "Paperless Billing is active, which sometimes correlates with high digital awareness and competitive price shopping."
            
    if "service_count" in feature_name:
        if is_risk:
            return f"Low service count ({int(raw_value)}) means low product stickiness; they can easily switch to a competitor."
        else:
            return f"High service count ({int(raw_value)}) indicates deep integration with our services, increasing switching costs."
            
    if "MonthlyCharges" in feature_name or "tenure_monthly_interaction" in feature_name:
        if is_risk:
            return "Higher than average monthly charges create bill shock and make them sensitive to cheaper competitor deals."
        else:
            return "Reasonable monthly pricing reduces billing pressure, acting as a retention driver."
            
    if "security_count" in feature_name:
        if is_risk:
            return f"Having few security/support features ({int(raw_value)}) reduces switching costs and makes churn easier."
        else:
            return f"Subscribing to multiple security/backup/support services ({int(raw_value)}) makes the account highly sticky."

    # Generic Fallback
    action_term = "increases churn risk" if is_risk else "supports retention"
    return f"Feature '{feature_name}' (value: {raw_value}) {action_term}."
