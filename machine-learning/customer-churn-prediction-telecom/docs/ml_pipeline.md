# Machine Learning Pipeline Guide

This guide details the model selection, cross-validation, hyperparameter tuning, and probability calibration procedures used in the training pipeline.

## 1. Benchmarking & Baseline Models

Our pipeline evaluates four classifiers using Stratified 5-Fold Cross-Validation on the training set:
1. **Logistic Regression:** Serves as a baseline linear model. Configured with `class_weight='balanced'` to offset class imbalance.
2. **Random Forest:** Benchmarks a basic bagging ensemble. Evaluates non-linear interactions.
3. **LightGBM:** A fast gradient boosting model.
4. **XGBoost:** Selected for hyperparameter tuning due to its high tabular performance.

Default baseline results (Mean 5-Fold ROC-AUC):
* **Logistic Regression:** `0.8460`
* **Random Forest:** `0.8253`
* **XGBoost:** `0.8199`
* **LightGBM:** `0.8365`

## 2. Hyperparameter Optimization (Optuna)

Optuna is used to tune the XGBoost model. The optimization focuses on the following parameters:
* `n_estimators`: `50` to `300`
* `max_depth`: `3` to `10`
* `learning_rate`: `0.01` to `0.2` (log scale)
* `subsample` & `colsample_bytree`: `0.6` to `1.0` (to reduce overfitting)
* `gamma`: `0.0` to `5.0` (minimum loss reduction required to split)
* L1/L2 regularization (`reg_alpha`/`reg_lambda`): log scale up to `10.0`

Optuna tuned the XGBoost model to achieve a validation AUC of **`0.8385+`** (with `scale_pos_weight` configured to account for target imbalance).

## 3. Probability Calibration

Many classifiers, particularly tree-based boosters, output scores that are not true probabilities (e.g. they push predictions away from 0 and 1). To address this, we apply Platt Scaling (`CalibratedClassifierCV` with `method='sigmoid'`) using a separate validation split.

### Why Calibration Matters
In a business retention campaign, predicting that a customer has an "80% chance of churn" must mean they have exactly an 80% empirical chance. Our ROI model multiplies this probability by the customer's lifetime value to decide whether to target them:
$$\text{Expected Value} = \text{Probability} \times \text{LTV} - \text{Campaign Cost}$$
If the probability is uncalibrated, the thresholding breaks down, and the retention team will target the wrong subscribers.

Calibration results:
* **Uncalibrated Brier Score:** `0.20+`
* **Calibrated Brier Score:** `0.138` (lower Brier score represents higher calibration accuracy)
