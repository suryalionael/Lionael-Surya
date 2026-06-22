# Machine Learning

Predictive models built and evaluated the way a business actually uses them: with a clear decision they inform, an honest accuracy/cost trade-off, and (where possible) something a non-technical stakeholder can run.

## Focus

- Classification & regression on real-world business problems
- Feature engineering, model comparison, hyperparameter tuning
- Explainability (SHAP) — every model ships with "why did it predict this?"
- Deployment (FastAPI/Streamlit), not just notebooks

## Projects

| Project | Status | Problem | Stack |
|---|---|---|---|
| [Customer Churn Prediction (Telecom)](customer-churn-prediction-telecom/) | 🔜 Planned | Predict churn to target retention spend | scikit-learn, XGBoost, SHAP, FastAPI |
| [Retail Demand Forecasting](retail-demand-forecasting/) | 🔜 Planned | Forecast SKU-level demand for inventory planning | Prophet, XGBoost, pandas |

## Related Work In Progress

- **Stock Signal Scanner** — a separate, actively developed repository (`AI Saham Pro`) building a Python-based stock signal scanner using `yfinance` with a modular architecture. Once it reaches a stable release it will be linked here and/or migrated in as a full project entry.

## Why This Matters for Recruiters

Most student ML portfolios stop at a Jupyter notebook with an accuracy score. Every model here is paired with an explainability step and a deployment path, because that's the difference between "I trained a model" and "I shipped something a stakeholder could use to make a decision."

Back to [main portfolio](../README.md).
