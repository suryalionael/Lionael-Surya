# Retail Demand Forecasting

**Status:** 🔜 Planned

## Business Problem

A retailer's inventory planning team currently orders stock based on last year's same-month sales plus gut feel, leading to frequent overstock (markdowns) and understock (lost sales) on fast-moving SKUs.

## Objective

Build a SKU-level demand forecasting model that beats the naive "same period last year" baseline, with a backtesting framework that proves it on historical hold-out periods before anyone trusts it for real ordering decisions.

## Planned Tech Stack

- **Forecasting:** Facebook Prophet (seasonality/trend baseline), XGBoost with lag/rolling features (challenger model)
- **Backtesting:** Rolling-origin cross-validation (walk-forward), not a single train/test split
- **Language:** Python (pandas, statsmodels)
- **Evaluation:** MAPE / WAPE against the naive baseline, reported per SKU category

## Planned Deliverables

- [ ] Baseline model: naive seasonal forecast
- [ ] Prophet model with holiday/promotion regressors
- [ ] XGBoost model with engineered lag/rolling-window features
- [ ] Walk-forward backtest comparing all three across multiple time windows
- [ ] Business write-up: which SKU categories the model improves forecasting for, and which it doesn't (and why)

---
Back to [Machine Learning](../README.md) · [main portfolio](../../README.md).
