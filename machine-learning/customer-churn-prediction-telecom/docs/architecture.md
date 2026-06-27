# System Architecture Document

This document describes the high-level system design, data flow, and components of the Telecom Customer Churn Prediction and Retention System.

## Architecture Overview

The system is designed following modular software engineering principles, dividing the machine learning pipeline from the serving layer (APIs and Dashboards). The system is fully configuration-driven via `config/config.yaml`.

```
                  ┌──────────────────────┐
                  │ scripts/download_data│
                  └──────────┬───────────┘
                             │
                             ▼
                      ┌──────────────┐
                      │  data/raw/   │
                      └──────┬───────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │   src/validation.py  ├─────────► [reports/data_validation_report.md]
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ src/preprocessing.py │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │src/feature_engine.py │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │    src/train.py      ├─────────► [models/model.pkl, pipeline.pkl]
                  └────┬─────────────┬───┘
                       │             │
                       ▼             ▼
             ┌─────────────────┐ ┌───────────────────┐
             │ app/main.py API │ │dashboard/streamlit│
             └─────────────────┘ └───────────────────┘
```

## System Components

### 1. Ingestion Layer (`scripts/download_data.py`)
Fetches raw data from secure source repositories. It creates local raw folders and saves the dataset without modifying historical records to maintain a single source of truth.

### 2. Validation Layer (`src/validation.py`)
Performs static schema checks and data quality validation (missing values, duplicate rows, out-of-bounds distributions, and negative values). Writes structured summaries into `reports/data_validation_report.md`.

### 3. Preprocessing Layer (`src/preprocessing.py`)
Cleans variables (e.g. converting `TotalCharges` strings containing empty spaces to numeric float) and applies logical fallback filling (tenure * MonthlyCharges). Maps targets into binary numbers.

### 4. Feature Engineering Layer (`src/feature_engineering.py`)
Applies custom feature engineering inside reusable Scikit-Learn transformers (`FeatureEngineer`). Scalers and encoders are bundled within a `ColumnTransformer` to enforce reproducible feature states.

### 5. Training, Calibration, and Optimization Layer (`src/train.py`, `src/calibration.py`, `src/evaluate.py`)
Runs model benchmarking across multiple algorithms, tunes hyperparameters with Optuna, calibrates raw probabilities using Platt scaling, and solves decision boundaries using profit curves.

### 6. Serving Layer (`app/main.py`, `dashboard/streamlit_app.py`)
Exposes predictions to developer applications via a FastAPI backend, and provides interactive retention campaign control to business users through Streamlit dashboards.
