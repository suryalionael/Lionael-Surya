# Feature Engineering Guide

This document describes the engineered features and how they are computed from the raw dataset.

## Engineered Features

The engineered variables are derived from the raw telecom customer records to improve prediction accuracy without fabricating synthetic metrics.

| Feature Name | Type | Description | Formula / Logic |
| :--- | :--- | :--- | :--- |
| `tenure_group` | Categorical | Bins customer tenure into duration cohorts. | `0-12m`, `12-24m`, `24-48m`, `48-60m`, `60m+` |
| `tenure_group_12` | Numerical | Bins customer tenure in increments of 12. | `tenure // 12` |
| `service_count` | Numerical | Sum of all services subscribed to. | Sum of indicators for Phone, MultipleLines, Internet, Security, Backup, Protection, TechSupport, TV, Movies. |
| `streaming_count` | Numerical | Number of streaming features. | `StreamingTV` (Yes) + `StreamingMovies` (Yes). |
| `security_count` | Numerical | Number of support/security features. | `OnlineSecurity` (Yes) + `OnlineBackup` (Yes) + `DeviceProtection` (Yes) + `TechSupport` (Yes). |
| `avg_monthly_revenue` | Numerical | Estimated average bill per month of tenure. | `TotalCharges / tenure`. If tenure is 0, equals `MonthlyCharges`. |
| `high_value_customer` | Binary | Customer value indicator. | `1` if `MonthlyCharges` > 80th training percentile (approx. $80.00), else `0`. |
| `tenure_monthly_interaction` | Numerical | Cumulative charge potential interaction. | `tenure * MonthlyCharges`. |

## Preprocessing Pipeline

The pipeline uses a Scikit-Learn `ColumnTransformer` to process numerical and categorical features:
1. **Numerical Features:** Processed using `StandardScaler` to normalize features (zero mean, unit variance).
2. **Categorical Features:** Processed using `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` to convert categorical strings to binary arrays.

The entire workflow is bundled inside a single Scikit-Learn pipeline to ensure that no data leakage occurs from training to validation splits:
```python
main_pipeline = Pipeline(steps=[
    ("feature_engineer", FeatureEngineer()),
    ("preprocessor", preprocessor)
])
```
This design guarantees that any record passed to the inference endpoint undergoes identical engineering and scaling transforms.
