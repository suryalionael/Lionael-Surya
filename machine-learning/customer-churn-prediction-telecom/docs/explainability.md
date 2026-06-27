# Model Explainability (SHAP) Guide

This document describes how SHAP is used to provide global model transparency and individual customer explanation interfaces.

## 1. SHAP Theory

SHAP (SHapley Additive exPlanations) is a game-theoretic approach to explain machine learning model outputs. It assigns each feature an importance value (a Shapley value) representing how much that feature shifts the model's prediction away from the baseline (the average prediction of the dataset).
* **Positive SHAP value (+):** Increases the probability of churn (risk driver).
* **Negative SHAP value (-):** Decreases the probability of churn (protective/retention factor).

## 2. Global Explanations (Feature Importance)

The pipeline computes global SHAP values using `shap.TreeExplainer` on our optimized XGBoost model. This generates two plots stored in `figures/`:
1. **`shap_summary_plot.png`:** Shows feature importance sorted by overall impact, combined with the direction of the feature values.
2. **`shap_bar_plot.png`:** Shows the mean absolute SHAP value for each feature.

### Global Insights
* **Contract Type:** Customers on Month-to-month contracts have the highest risk impact. Longer contract commitments (1 or 2 years) act as strong protective forces.
* **Tenure:** Higher tenure correlates with lower churn risk, representing customer loyalty.
* **Internet Service:** Fiber optic subscribers show an increased churn risk. This warrants investigation into pricing fatigue or service stability issues.
* **Auto-Pay:** Automatic payment methods (credit card or bank transfer) significantly reduce churn risk compared to manual electronic checks.

## 3. Local Business Translation Engine

For individual customer predictions, raw SHAP values are not user-friendly for business stakeholders. The system implements a translation engine (`src/explain.py`) that parses individual SHAP values and translates them into actionable business descriptions.

### Example Translation
For a customer on a month-to-month contract with high monthly charges:
* **Raw SHAP Feature:** `Contract_Month-to-month` = `1.0` (SHAP score = `+0.354`)
  * **Translated Explanation:** "Being on a Month-to-Month contract is a major risk factor, making it easy for the customer to cancel."
* **Raw SHAP Feature:** `MonthlyCharges` = `95.50` (SHAP score = `+0.125`)
  * **Translated Explanation:** "Higher than average monthly charges create bill shock and make them sensitive to cheaper competitor deals."
* **Raw SHAP Feature:** `OnlineSecurity_Yes` = `1.0` (SHAP score = `-0.092`)
  * **Translated Explanation:** "Subscribing to Online Security is a major protective factor, increasing customer dependency and product stickiness."
