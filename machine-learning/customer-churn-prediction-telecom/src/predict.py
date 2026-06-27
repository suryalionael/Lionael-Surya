import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from src.config import CONFIG
from src.logger import logger
from src.utils import load_pkl, load_json
from src.explain import explain_single_customer

class ChurnPredictor:
    """Inference class to load model artifacts and make predictions with explanations and recommendations."""
    def __init__(self, models_dir: str = None):
        if models_dir is None:
            models_dir = CONFIG["paths"]["models_dir"]
            
        logger.info(f"Loading churn prediction artifacts from {models_dir}...")
        
        self.model = load_pkl(os.path.join(models_dir, "model.pkl"))
        self.pipeline = load_pkl(os.path.join(models_dir, "pipeline.pkl"))
        
        feature_names_dict = load_json(os.path.join(models_dir, "feature_names.json"))
        self.feature_names = feature_names_dict["feature_names"]
        
        metrics_dict = load_json(os.path.join(models_dir, "metrics.json"))
        self.optimal_threshold = metrics_dict.get("optimal_threshold", 0.5)
        
        # Load SHAP explainer
        try:
            self.explainer = load_pkl(os.path.join(models_dir, "shap_explainer.pkl"))
        except Exception as e:
            logger.warning(f"Could not load SHAP explainer. Individual predictions will not have SHAP explanations. Error: {e}")
            self.explainer = None

    def get_risk_category(self, prob: float) -> str:
        """Determines the risk category based on the probability threshold."""
        if prob < 0.20:
            return "Low"
        elif prob < 0.50:
            return "Medium"
        elif prob < 0.80:
            return "High"
        else:
            return "Critical"

    def get_tailored_recommendation(self, prob: float, row: Dict[str, Any]) -> str:
        """Generates dynamic business interventions tailored to customer attributes and risk level."""
        risk_cat = self.get_risk_category(prob)
        
        if risk_cat == "Low":
            return "No intervention. Maintain standard automated marketing communications."
            
        # Get customer service variables
        contract = row.get("Contract", "")
        payment = row.get("PaymentMethod", "")
        security = row.get("OnlineSecurity", "")
        support = row.get("TechSupport", "")
        monthly_charges = float(row.get("MonthlyCharges", 0))
        
        recommendations = []
        
        # Risk levels: Medium, High, Critical
        if risk_cat == "Medium":
            prefix = "Email Outreach: "
            if contract == "Month-to-month":
                recommendations.append("Suggest upgrading to an annual contract with a 5% monthly discount.")
            if "Electronic check" in payment:
                recommendations.append("Promote a $5 one-time credit for enrolling in Auto-Pay.")
            if security == "No":
                recommendations.append("Offer a 14-day free trial of Online Security.")
            if not recommendations:
                recommendations.append("Send a customer satisfaction survey with usage tips.")
            return prefix + " or ".join(recommendations)
            
        elif risk_cat == "High":
            prefix = "Retention Call: "
            if contract == "Month-to-month":
                recommendations.append("Offer a 10% discount on a 1-Year Contract upgrade.")
            if security == "No" or support == "No":
                recommendations.append("Offer free Online Security + Tech Support bundle for 3 months.")
            if monthly_charges > 80:
                recommendations.append("Perform plan optimization to transition to a more cost-effective bundle.")
            if not recommendations:
                recommendations.append("Offer a loyalty check-in call with a $15 service credit.")
            return prefix + " or ".join(recommendations)
            
        else: # Critical
            prefix = "Priority loyalty offer: "
            if contract == "Month-to-month":
                recommendations.append("Urgent retention call: Offer 20% discount on a 1-Year contract, or $150 credit.")
            else:
                recommendations.append(f"Loyalty VIP offer: Direct billing credit of $100 or a plan upgrade at no extra cost.")
            if monthly_charges > 90:
                recommendations.append("Downgrade offer: Switch to a slightly lower-tier plan with waived fees.")
            return prefix + " or ".join(recommendations)

    def predict_single(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts churn risk, confidence, SHAP drivers, and recommends actions for a single customer.
        """
        # Convert dictionary to DataFrame (must contain same columns as model was trained on)
        df_customer = pd.DataFrame([customer_data])
        
        # Standard clean and preprocess
        # Ensure TotalCharges is numeric
        if "TotalCharges" in df_customer.columns:
            df_customer["TotalCharges"] = pd.to_numeric(df_customer["TotalCharges"], errors="coerce")
            mask_nan = df_customer["TotalCharges"].isnull()
            if mask_nan.any():
                df_customer.loc[mask_nan & (df_customer["tenure"] == 0), "TotalCharges"] = 0.0
                mask_nan_remaining = df_customer["TotalCharges"].isnull()
                if mask_nan_remaining.any():
                    df_customer.loc[mask_nan_remaining, "TotalCharges"] = (
                        df_customer.loc[mask_nan_remaining, "tenure"] * df_customer.loc[mask_nan_remaining, "MonthlyCharges"]
                    )
        
        # Transform customer features
        customer_trans = self.pipeline.transform(df_customer)
        
        # Predict probability
        prob = float(self.model.predict_proba(customer_trans)[0, 1])
        prediction = int(prob >= self.optimal_threshold)
        
        # Calculate confidence: distance from the decision boundary normalized to [0.5, 1.0]
        # if threshold is 0.45, and prob is 0.9, confidence is high.
        # Simple formula: 0.5 + abs(prob - threshold) * (0.5 / (threshold if prob < threshold else 1 - threshold))
        if prob >= self.optimal_threshold:
            dist = prob - self.optimal_threshold
            denom = 1.0 - self.optimal_threshold
        else:
            dist = self.optimal_threshold - prob
            denom = self.optimal_threshold
        confidence = 0.5 + 0.5 * (dist / denom if denom > 0 else 0)
        
        risk_cat = self.get_risk_category(prob)
        recommendation = self.get_tailored_recommendation(prob, customer_data)
        
        # SHAP local explanation
        risk_drivers = []
        protective_factors = []
        if self.explainer is not None:
            try:
                _, risk_drivers, protective_factors = explain_single_customer(
                    self.explainer, customer_trans[0], self.feature_names
                )
            except Exception as e:
                logger.error(f"Failed to generate SHAP drivers for customer: {e}")
                
        return {
            "churn_probability": round(prob, 4),
            "prediction": prediction,
            "confidence": round(confidence, 4),
            "risk_category": risk_cat,
            "recommended_action": recommendation,
            "top_risk_drivers": risk_drivers,
            "top_protective_factors": protective_factors
        }

    def predict_batch(self, df_batch: pd.DataFrame) -> pd.DataFrame:
        """
        Predicts churn risk and generates recommended actions for a batch of customer records.
        """
        logger.info(f"Processing batch prediction for {len(df_batch)} records.")
        df_clean = df_batch.copy()
        
        # Check customerID column
        id_col = CONFIG["data"]["id_column"]
        ids = df_clean[id_col].copy() if id_col in df_clean.columns else pd.Series(range(len(df_clean)))
        
        # Clean TotalCharges and numeric fields
        if "TotalCharges" in df_clean.columns:
            df_clean["TotalCharges"] = pd.to_numeric(df_clean["TotalCharges"], errors="coerce")
            mask_nan = df_clean["TotalCharges"].isnull()
            if mask_nan.any():
                df_clean.loc[mask_nan & (df_clean["tenure"] == 0), "TotalCharges"] = 0.0
                mask_nan_remaining = df_clean["TotalCharges"].isnull()
                if mask_nan_remaining.any():
                    df_clean.loc[mask_nan_remaining, "TotalCharges"] = (
                        df_clean.loc[mask_nan_remaining, "tenure"] * df_clean.loc[mask_nan_remaining, "MonthlyCharges"]
                    )
                    
        # Apply transformation
        batch_trans = self.pipeline.transform(df_clean)
        
        # Make predictions
        probs = self.model.predict_proba(batch_trans)[:, 1]
        preds = (probs >= self.optimal_threshold).astype(int)
        
        # Compile results
        results = []
        for idx in range(len(df_clean)):
            prob = float(probs[idx])
            pred = int(preds[idx])
            risk_cat = self.get_risk_category(prob)
            
            # Simple row dictionary for recommendation engine
            row_dict = df_clean.iloc[idx].to_dict()
            rec = self.get_tailored_recommendation(prob, row_dict)
            
            results.append({
                id_col: ids.iloc[idx],
                "churn_probability": round(prob, 4),
                "prediction": pred,
                "risk_category": risk_cat,
                "recommended_action": rec
            })
            
        return pd.DataFrame(results)
