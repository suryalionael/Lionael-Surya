import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
try:
    from sklearn.calibration import FrozenEstimator
    HAS_FROZEN_ESTIMATOR = True
except ImportError:
    HAS_FROZEN_ESTIMATOR = False
from sklearn.metrics import brier_score_loss
from typing import Tuple, Dict, Any
from src.config import CONFIG
from src.logger import logger

def calibrate_model(model: Any, X_train: pd.DataFrame, y_train: pd.Series, X_val: pd.DataFrame, y_val: pd.Series) -> Tuple[CalibratedClassifierCV, float]:
    """
    Fits a calibrated classifier wrapper around a pre-trained model.
    Uses Platt scaling (sigmoid) or isotonic regression as specified in config.yaml.
    """
    method = CONFIG["calibration"].get("method", "sigmoid")
    logger.info(f"Calibrating model using CalibratedClassifierCV with method: {method}")
    
    # We calibrate on the validation set since the base model is already trained.
    if HAS_FROZEN_ESTIMATOR:
        logger.info("Using FrozenEstimator for calibration (scikit-learn 1.4+).")
        calibrated_model = CalibratedClassifierCV(estimator=FrozenEstimator(model), method=method, cv=None)
    else:
        logger.info("Using cv='prefit' for calibration (legacy scikit-learn).")
        calibrated_model = CalibratedClassifierCV(estimator=model, method=method, cv="prefit")
        
    calibrated_model.fit(X_val, y_val)
    
    # Calculate calibrated Brier score
    y_prob_calibrated = calibrated_model.predict_proba(X_val)[:, 1]
    brier_score = brier_score_loss(y_val, y_prob_calibrated)
    logger.info(f"Calibrated Model Brier Score: {brier_score:.5f}")
    
    return calibrated_model, brier_score

def evaluate_calibration(
    base_model: Any, 
    calibrated_model: Any, 
    X_val: pd.DataFrame, 
    y_val: pd.Series,
    output_path: str = None
) -> Dict[str, Any]:
    """
    Compares base vs calibrated model probabilities, computes Brier scores,
    and plots reliability diagrams and probability histograms.
    """
    if output_path is None:
        output_path = os.path.join(CONFIG["paths"]["figures_dir"], "calibration_comparison.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Get probabilities
    y_prob_base = base_model.predict_proba(X_val)[:, 1]
    y_prob_calib = calibrated_model.predict_proba(X_val)[:, 1]
    
    # Compute Brier scores
    brier_base = brier_score_loss(y_val, y_prob_base)
    brier_calib = brier_score_loss(y_val, y_prob_calib)
    
    # Calculate calibration curves
    prob_true_base, prob_pred_base = calibration_curve(y_val, y_prob_base, n_bins=10)
    prob_true_calib, prob_pred_calib = calibration_curve(y_val, y_prob_calib, n_bins=10)
    
    # Generate Plots
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    # Plot 1: Reliability Diagram / Calibration Curve
    axes[0].plot([0, 1], [0, 1], "k--", label="Perfect Calibration")
    axes[0].plot(prob_pred_base, prob_true_base, "s-", color="red", label=f"Uncalibrated (Brier={brier_base:.4f})")
    axes[0].plot(prob_pred_calib, prob_true_calib, "o-", color="blue", label=f"Calibrated (Brier={brier_calib:.4f})")
    axes[0].set_xlabel("Mean Predicted Probability", fontsize=12)
    axes[0].set_ylabel("Fraction of Positives", fontsize=12)
    axes[0].set_title("Calibration Curve (Reliability Diagram)", fontsize=14)
    axes[0].legend(loc="upper left")
    axes[0].grid(True, linestyle=":")
    
    # Plot 2: Probability Histograms
    axes[1].hist(y_prob_base, range=(0, 1), bins=20, color="red", histtype="step", lw=2, label="Uncalibrated")
    axes[1].hist(y_prob_calib, range=(0, 1), bins=20, color="blue", histtype="step", lw=2, label="Calibrated")
    axes[1].set_xlabel("Predicted Probability of Churn", fontsize=12)
    axes[1].set_ylabel("Count", fontsize=12)
    axes[1].set_title("Probability Distribution Histogram", fontsize=14)
    axes[1].legend(loc="upper right")
    axes[1].grid(True, linestyle=":")
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()
    logger.info(f"Saved calibration comparison figure to {output_path}")
    
    comparison_metrics = {
        "uncalibrated_brier": float(brier_base),
        "calibrated_brier": float(brier_calib),
        "brier_improvement": float(brier_base - brier_calib)
    }
    
    return comparison_metrics
