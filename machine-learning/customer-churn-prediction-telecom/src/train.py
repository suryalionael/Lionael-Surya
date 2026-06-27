import os
import numpy as np
import pandas as pd
import optuna
import joblib
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score

from src.config import CONFIG
from src.logger import logger
from src.utils import save_pkl, save_json
from src.preprocessing import preprocess_pipeline
from src.feature_engineering import get_preprocessing_pipeline, get_feature_names_out
from src.calibration import calibrate_model, evaluate_calibration
from src.evaluate import (
    compute_metrics,
    find_optimal_threshold,
    simulate_business_roi,
    generate_evaluation_plots,
    generate_evaluation_report,
)
from src.explain import get_shap_explainer, generate_global_shap_plots
from src.drift import build_drift_reference

# Suppress Optuna logs unless warning/error
optuna.logging.set_verbosity(optuna.logging.WARNING)


def run_optuna_study(
    X_train: np.ndarray, y_train: pd.Series, X_val: np.ndarray, y_val: pd.Series
) -> dict:
    """Runs Optuna hyperparameter optimization for XGBoost."""
    logger.info("Starting Optuna hyperparameter optimization for XGBoost...")

    # Calculate class weight ratio for scale_pos_weight
    ratio = float(np.sum(y_train == 0) / np.sum(y_train == 1))

    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 50, 300),
            "max_depth": trial.suggest_int("max_depth", 3, 10),
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
            "subsample": trial.suggest_float("subsample", 0.6, 1.0),
            "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
            "gamma": trial.suggest_float("gamma", 0.0, 5.0),
            "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
            "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
            "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
            "scale_pos_weight": ratio,
            "random_state": CONFIG["train"]["random_state"],
            "eval_metric": "logloss",
        }

        # Instantiate and train model
        model = XGBClassifier(**params)
        model.fit(X_train, y_train, eval_set=[(X_val, y_val)], verbose=False)

        # We optimize for validation ROC-AUC
        val_preds = model.predict_proba(X_val)[:, 1]
        val_auc = roc_auc_score(y_val, val_preds)
        return val_auc

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=CONFIG["train"]["optuna_trials"])

    logger.info(
        f"Optuna optimization completed. Best Trial AUC: {study.best_value:.5f}"
    )

    # Save Optuna plots if possible
    try:
        fig = optuna.visualization.matplotlib.plot_optimization_history(study)
        fig_path = os.path.join(
            CONFIG["paths"]["figures_dir"], "optuna_optimization_history.png"
        )
        import matplotlib.pyplot as plt

        plt.title("XGBoost Hyperparameter Optimization History")
        plt.tight_layout()
        plt.savefig(fig_path, dpi=300)
        plt.close()
        logger.info(f"Saved Optuna optimization history plot to {fig_path}")
    except Exception as e:
        logger.warning(f"Failed to generate Optuna visualization: {e}")

    return study.best_params


def train_and_evaluate_pipeline():
    """Executes the entire end-to-end model training, calibration, explanation, and evaluation pipeline."""
    # 1. Preprocess data
    df_clean, X, y = preprocess_pipeline()

    # Split: Train/Val/Test (70% Train, 15% Val, 15% Test)
    random_state = CONFIG["train"]["random_state"]
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.15, random_state=random_state, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.1765,
        random_state=random_state,
        stratify=y_train_val,
    )  # 0.1765 * 0.85 = ~0.15 of total

    logger.info(f"Train set size: {X_train.shape[0]} rows")
    logger.info(f"Validation set size: {X_val.shape[0]} rows")
    logger.info(f"Test set size: {X_test.shape[0]} rows")

    # Preserve monthly charges for ROI simulation (from X_test)
    test_monthly_charges = X_test["MonthlyCharges"].copy()
    val_monthly_charges = X_val["MonthlyCharges"].copy()

    # 2. Get and fit feature engineering / preprocessing pipeline
    pipeline, all_numerical, all_categorical = get_preprocessing_pipeline()

    logger.info(
        "Fitting feature engineering and preprocessing pipeline on train data..."
    )
    # Fit the pipeline on X_train
    pipeline.fit(X_train, y_train)

    # Get feature names output
    feature_names = get_feature_names_out(pipeline, all_numerical, all_categorical)
    logger.info(f"Encoded dataset has {len(feature_names)} features.")

    # Transform all splits
    X_train_trans = pipeline.transform(X_train)
    X_val_trans = pipeline.transform(X_val)
    X_test_trans = pipeline.transform(X_test)
    X_train_val_trans = pipeline.transform(X_train_val)

    # 3. Model comparison using default parameters and Stratified K-Fold
    logger.info("Comparing default models using cross-validation on train data...")
    cv = StratifiedKFold(
        n_splits=CONFIG["train"]["n_splits"], shuffle=True, random_state=random_state
    )

    # Compute class weights ratio for XGBoost / scale_pos_weight
    ratio = float(np.sum(y_train == 0) / np.sum(y_train == 1))

    models = {
        "Logistic Regression": LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=random_state
        ),
        "Random Forest": RandomForestClassifier(
            class_weight="balanced", random_state=random_state
        ),
        "XGBoost": XGBClassifier(
            scale_pos_weight=ratio, random_state=random_state, eval_metric="logloss"
        ),
        "LightGBM": LGBMClassifier(
            class_weight="balanced", random_state=random_state, verbose=-1
        ),
    }

    comparison_results = []
    for name, model in models.items():
        auc_scores = []
        for train_idx, val_idx in cv.split(X_train_trans, y_train):
            X_fold_tr, X_fold_val = X_train_trans[train_idx], X_train_trans[val_idx]
            y_fold_tr, y_fold_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

            model.fit(X_fold_tr, y_fold_tr)
            preds = model.predict_proba(X_fold_val)[:, 1]
            auc_scores.append(roc_auc_score(y_fold_val, preds))

        mean_auc = np.mean(auc_scores)
        std_auc = np.std(auc_scores)
        logger.info(f"{name} CV ROC-AUC: {mean_auc:.4f} (+/- {std_auc:.4f})")
        comparison_results.append(
            {"Model": name, "CV_AUC": mean_auc, "CV_AUC_Std": std_auc}
        )

    comparison_df = pd.DataFrame(comparison_results)
    comparison_path = os.path.join(
        CONFIG["paths"]["reports_dir"], "model_comparison.csv"
    )
    comparison_df.to_csv(comparison_path, index=False)
    logger.info(f"Saved model comparison table to {comparison_path}")

    # 4. Hyperparameter Optimization on XGBoost (industry-standard for tabular data)
    best_params = run_optuna_study(X_train_trans, y_train, X_val_trans, y_val)
    best_params["scale_pos_weight"] = ratio
    best_params["random_state"] = random_state
    best_params["eval_metric"] = "logloss"

    # Save best parameters
    best_params_path = os.path.join(CONFIG["paths"]["models_dir"], "best_params.json")
    save_json(best_params, best_params_path)

    # 5. Train optimized model on full training split
    logger.info("Training final optimized XGBoost model...")
    best_model = XGBClassifier(**best_params)
    best_model.fit(X_train_trans, y_train)

    # Save the base uncalibrated model
    base_model_path = os.path.join(CONFIG["paths"]["models_dir"], "xgboost_base.pkl")
    save_pkl(best_model, base_model_path)

    # 6. Probability Calibration on validation split
    calibrated_model, _ = calibrate_model(
        best_model, X_train_trans, y_train, X_val_trans, y_val
    )

    # Evaluate calibration curve & probability histogram comparison
    calib_metrics = evaluate_calibration(
        best_model, calibrated_model, X_val_trans, y_val
    )

    # 7. Find Optimal Decision Threshold on validation set (ROI maximization)
    val_probs = calibrated_model.predict_proba(X_val_trans)[:, 1]
    optimal_threshold, val_sim = find_optimal_threshold(
        y_val, val_probs, val_monthly_charges
    )
    logger.info(
        f"Optimal Threshold configured from Validation Set: {optimal_threshold:.2f}"
    )

    # 8. Final Evaluation on Holdout Test Set using optimal threshold
    logger.info("Performing final model evaluation on holdout test set...")
    test_probs = calibrated_model.predict_proba(X_test_trans)[:, 1]

    # Metrics and ROI simulation on test set
    test_metrics = compute_metrics(y_test, test_probs, threshold=optimal_threshold)
    test_sim = simulate_business_roi(
        y_test, test_probs, optimal_threshold, test_monthly_charges
    )

    # Log final performance
    logger.info(f"Test Set ROC-AUC: {test_metrics['roc_auc']:.4f}")
    logger.info(f"Test Set PR-AUC: {test_metrics['pr_auc']:.4f}")
    logger.info(f"Test Set F1-Score: {test_metrics['f1_score']:.4f}")
    logger.info(
        f"Test Set Estimated ROI: {test_sim['financials']['roi_percentage']:.2f}%"
    )
    logger.info(f"Test Set Net Savings: ${test_sim['financials']['net_savings']:,.2f}")

    # Generate curves & reports
    generate_evaluation_plots(
        y_test, test_probs, optimal_threshold, test_monthly_charges
    )
    generate_evaluation_report(test_metrics, test_sim)

    # 9. Global Explainability with SHAP on validation set
    explainer = get_shap_explainer(calibrated_model, X_train_trans)
    generate_global_shap_plots(explainer, X_val_trans, feature_names)

    # Save the SHAP explainer
    explainer_path = os.path.join(CONFIG["paths"]["models_dir"], "shap_explainer.pkl")
    save_pkl(explainer, explainer_path)

    # 10. Save final artifacts
    save_pkl(calibrated_model, os.path.join(CONFIG["paths"]["models_dir"], "model.pkl"))
    save_pkl(pipeline, os.path.join(CONFIG["paths"]["models_dir"], "pipeline.pkl"))

    # Save configuration & names
    feature_names_path = os.path.join(
        CONFIG["paths"]["models_dir"], "feature_names.json"
    )
    save_json({"feature_names": feature_names}, feature_names_path)

    # Save training reference profile for production drift monitoring
    drift_reference = build_drift_reference(X_train)
    drift_reference_path = os.path.join(
        CONFIG["paths"]["models_dir"], "drift_reference.json"
    )
    save_json(drift_reference, drift_reference_path)

    # Save metrics combined
    combined_metrics = {
        "model_comparison": comparison_results,
        "calibration": calib_metrics,
        "test_metrics": test_metrics,
        "test_business_simulation": test_sim,
        "optimal_threshold": optimal_threshold,
    }
    metrics_path = os.path.join(CONFIG["paths"]["models_dir"], "metrics.json")
    save_json(combined_metrics, metrics_path)
    # Save to reports as well
    save_json(
        combined_metrics, os.path.join(CONFIG["paths"]["reports_dir"], "metrics.json")
    )

    logger.info("Pipeline executed successfully and all artifacts saved.")
    return combined_metrics


if __name__ == "__main__":
    train_and_evaluate_pipeline()
