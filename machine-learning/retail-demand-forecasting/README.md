# Retail Demand Forecasting

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue?logo=python)](https://python.org)
[![Tests](https://github.com/suryalionael/Retail-Demand-Forecasting/actions/workflows/ci.yml/badge.svg)](https://github.com/suryalionael/Retail-Demand-Forecasting/actions)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000)](https://github.com/astral-sh/ruff)
[![Black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](Dockerfile)

Production-ready SKU-level demand forecasting system that improves inventory planning by outperforming naive seasonal forecasting baselines. Uses UCI Online Retail II dataset with walk-forward validation across Prophet, XGBoost, and Naive Seasonal models.

---

## Results (Top SKU — walk-forward validation)

| Model | MAE | RMSE | MAPE | SMAPE | WAPE | Bias | Accuracy |
|-------|-----|------|------|-------|------|------|----------|
| Naive Seasonal | 701.79 | — | — | — | — | — | — |
| Prophet | 181.14 | — | — | — | — | — | — |
| **XGBoost** | **88.62** | — | — | — | — | — | — |

> XGBoost achieves ~87% error reduction over the naive baseline on top-selling SKUs.

---

## Business Problem

Retail inventory planners currently estimate demand using:
- Manual adjustments
- Historical averages
- Human intuition

This causes overstocking, understocking, lost sales, and high markdown costs.

This system builds forecasting models that consistently outperform the naive seasonal approach using rigorous walk-forward validation.

---

## Dataset

### UCI Online Retail II

Transaction-level retail data from a UK-based online retailer (2009–2011):
- **~1M transactions** across two sheets
- **4,000–5,000 unique SKUs**
- **4,300+ unique customers** across 38–40 countries
- Columns: Invoice, StockCode, Description, Quantity, InvoiceDate, Price, CustomerID, Country

> Download from [UCI ML Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii) and place `online_retail_II.xlsx` in `data/raw/`.

### Cleaning

1. Remove cancelled invoices (prefix "C")
2. Remove returns (negative quantities)
3. Remove invalid prices (≤ 0) and quantities (≤ 0)
4. Drop exact duplicate rows
5. Fill missing descriptions and customer IDs as "unknown"

### Aggregation

Transactions → daily SKU-level demand:

| Column | Description |
|--------|-------------|
| `date` | Calendar date |
| `stockcode` | SKU identifier |
| `daily_demand` | Sum of quantity sold |
| `revenue` | Sum of quantity × price |
| `num_transactions` | Unique invoices per day |
| `avg_price` | Mean unit price |

---

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Data       │────▶│  Feature     │────▶│  Forecasting│
│  Ingestion  │     │  Engineering │     │  Models     │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                 │
┌─────────────┐     ┌──────────────┐     ┌──────▼──────┐
│  Reporting   │◀────│  Evaluation  │◀────│  Walk-Forward│
│  & Viz      │     │  & Metrics   │     │  Validation  │
└─────────────┘     └──────────────┘     └─────────────┘
```

### Pipeline

```
online_retail_II.xlsx
  │
  ▼
Data Ingestion ──► Data Cleaning ──► Daily Aggregation
                                          │
                                          ▼
                              Feature Engineering
                              (lags, rolling stats,
                               calendar, EMA)
                                          │
                    ┌─────────────────────┼─────────────────────┐
                    ▼                     ▼                     ▼
           Naive Seasonal           Prophet              XGBoost
                    │                     │                     │
                    └─────────────────────┼─────────────────────┘
                                          ▼
                              Walk-Forward Validation
                                          │
                                          ▼
                              Metrics & Model Comparison
                                          │
                                          ▼
                              Reports & Visualizations
```

---

## Project Structure

```
retail-demand-forecasting/
├── README.md
├── LICENSE
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── requirements.txt
├── configs/
│   └── default.yaml              # YAML configuration
├── data/
│   ├── raw/                      # online_retail_II.xlsx
│   ├── interim/
│   └── processed/
├── models/                       # Saved model artifacts
├── notebooks/
│   └── eda.ipynb                 # Exploratory data analysis
├── reports/
│   ├── figures/                  # Generated visualizations
│   └── business_report.md        # Business insights report
├── src/
│   ├── data/                     # Ingestion, cleaning, validation, aggregation
│   │   ├── ingestion.py
│   │   ├── cleaning.py
│   │   ├── validation.py
│   │   └── aggregation.py
│   ├── features/
│   │   └── engineering.py        # Lag, rolling, calendar, EMA features
│   ├── forecasting/
│   │   ├── naive_model.py        # Naive seasonal baseline
│   │   ├── prophet_model.py      # Prophet with seasonality
│   │   └── xgboost_model.py      # XGBoost with feature importance
│   ├── evaluation/
│   │   ├── metrics.py            # MAE, RMSE, MAPE, SMAPE, WAPE, bias
│   │   └── backtesting.py        # Walk-forward validator
│   ├── visualization/
│   │   └── plots.py              # Matplotlib/Seaborn plotting
│   ├── pipelines/
│   │   └── training.py           # Full training pipeline
│   └── utils/
│       ├── config.py             # YAML config loader
│       └── logger.py             # Logging setup
├── tests/
│   ├── test_cleaning.py
│   ├── test_validation.py
│   ├── test_features.py
│   ├── test_metrics.py
│   ├── test_backtesting.py
│   └── test_naive.py
└── .github/workflows/
    └── ci.yml                    # GitHub Actions CI
```

---

## Quick Start

```bash
# Install
pip install -r requirements.txt
pip install -e .

# Place dataset
cp /path/to/online_retail_II.xlsx data/raw/

# Run pipeline
python -c "from src.pipelines.training import main; main()"

# Run tests
pytest tests/ -v

# Run EDA
jupyter notebook notebooks/eda.ipynb
```

---

## Docker

```bash
# Full pipeline
docker compose up forecasting

# MLflow tracking
docker compose --profile mlflow up

# Jupyter
docker compose --profile jupyter up
```

---

## Feature Engineering

For each SKU, the system generates (using only historical data):

| Feature Group | Details |
|--------------|---------|
| **Lags** | Demand at t−1, t−7, t−14, t−28, t−56 |
| **Rolling stats** | Mean, median, std, min, max over 7/14/28/56 day windows |
| **EMA** | Exponential moving averages at 7/14/28 day spans |
| **Calendar** | Day of week, week of year, month, quarter, year, weekend flag |

---

## Models

### Naive Seasonal
- Same-day-last-period forecast (configurable period)
- Serves as minimum performance threshold

### Prophet
- Automatic changepoint detection
- Weekly/monthly/yearly multiplicative seasonality
- Optional hyperparameter tuning via Optuna

### XGBoost
- Trained on engineered lag/rolling/calendar features
- Early stopping to prevent overfitting
- Feature importance analysis
- Optional hyperparameter tuning via Optuna

---

## Evaluation

**Walk-forward validation** with rolling-origin:
- N folds with configurable initial window, horizon, and step
- Each fold trains on expanding window, tests on next horizon
- Prevents time-series leakage from single train/test split

**Metrics**: MAE, RMSE, MAPE, SMAPE, WAPE, Bias, Forecast Accuracy (100 − MAPE)

---

## MLflow

Experiment tracking with automatic metric logging:

```bash
mlflow ui
# or docker compose --profile mlflow up
# → http://localhost:5001
```

---

## Generated Reports

After pipeline run, `reports/figures/` contains:
- Daily sales trend, distribution, weekly/monthly seasonality
- Top 20 SKUs by total demand
- Country distribution (top 20 countries)
- Actual vs forecast scatter + residual histograms (per model)
- Feature correlation heatmap
- Feature importance (XGBoost)

---

## CI/CD

GitHub Actions automatically runs on push/PR:
1. Ruff linting
2. Black formatting check
3. Pytest (37+ tests)
4. Import verification

---

## Limitations

- Intermittent demand inflates MAPE for many SKUs
- No external regressors (holidays, promotions, weather)
- Two-year dataset limits yearly seasonality estimation
- Cold-start problem for new products

---

## Roadmap

- [x] Data ingestion & cleaning (UCI Online Retail II)
- [x] Feature engineering (lags, rolling stats, calendar)
- [x] Forecasting models (Naive, Prophet, XGBoost)
- [x] Walk-forward validation & evaluation
- [x] 37 unit tests
- [x] Docker support
- [ ] CLI (`python -m src.predict --sku 85123A --days 30`)
- [ ] Streamlit dashboard
- [ ] Best-model-per-SKU selection
- [ ] SHAP explanations & confidence intervals
- [ ] 50+ tests

---

## License

MIT
