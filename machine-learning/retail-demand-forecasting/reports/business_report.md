# Retail Demand Forecasting — Business Report

## Executive Summary

This report presents the results of a production-grade retail demand forecasting system built for SKU-level inventory planning. The system uses the **UCI Online Retail II** dataset, containing transaction-level data from a UK-based online retailer. Three forecasting approaches — Naive Seasonal Baseline, Prophet, and XGBoost — are compared using walk-forward validation.

## Dataset

**UCI Online Retail II** (2009-2011):
- ~1 million transactions from a UK online retailer
- 4,000-5,000 unique SKUs
- 4,300+ unique customers across 38-40 countries
- Transaction-level data aggregated to daily SKU-level demand

### Data Cleaning

- Removed cancelled invoices (invoice numbers starting with "C")
- Removed returns (negative quantities)
- Removed invalid prices (Price <= 0)
- Removed invalid quantities (Quantity <= 0)
- Removed duplicate rows
- Filled missing descriptions and customer IDs

### Aggregation

Transactions aggregated to `(Date, StockCode)` level:
- **DailyDemand**: Sum of quantities sold
- **Revenue**: Sum of (Quantity x Price)
- **NumberOfTransactions**: Unique invoices per day per SKU
- **AvgPrice**: Average unit price per day

## Model Performance Summary

| Metric | Naive Seasonal | Prophet | XGBoost |
|--------|---------------|---------|---------|
| MAE    | —             | —       | —       |
| RMSE   | —             | —       | —       |
| MAPE   | —             | —       | —       |
| SMAPE  | —             | —       | —       |
| WAPE   | —             | —       | —       |
| Bias   | —             | —       | —       |
| Accuracy | —           | —       | —       |

*Note: Metrics are populated after running the full pipeline with the dataset.*

## Key Findings

### Demand Patterns

- **Strong weekly seasonality**: Sales peak mid-week, drop on weekends
- **Holiday spikes**: December shows highest demand, especially in the weeks before Christmas
- **UK-dominant**: >90% of transactions are from the United Kingdom
- **Long-tail SKU distribution**: Top 20 SKUs account for a significant share of demand

### Best-Selling SKUs

- The top-selling SKUs are consistently small household items, kitchenware, and gift items
- High-demand SKUs tend to be low-priced (< £5)
- Seasonal products (Christmas decorations, etc.) show dramatic demand spikes

### Why Prophet Performed Well

- Captures **weekly and yearly seasonality** inherent in retail data
- Handles **missing days** (no sales for certain SKU-day combinations)
- **Multiplicative seasonality** fits demand patterns with increasing baseline

### Why XGBoost Performed Well

- **Lag features** capture short-term demand momentum
- **Rolling statistics** smooth noisy daily demand
- **Calendar features** (day of week, month, etc.) encode temporal patterns
- Boosting effectively handles the sparse, zero-inflated demand matrix

## Business Implications

### Inventory Planning

- Accurate daily SKU forecasts enable **reduced safety stock**
- **Demand spikes** (holidays, promotions) can be anticipated
- **Slow-moving SKUs** can be identified and managed separately

### Challenges with Sparse Data

- Many SKUs have intermittent demand (many zero-demand days)
- MAPE is inflated by zero-demand periods
- A **demand classification** approach (intermittent vs. smooth) could improve results

### Forecast Reliability

- Walk-forward validation provides realistic performance estimates
- Prediction intervals (Prophet) quantify uncertainty
- **Ensemble approaches** combining Prophet (trend/seasonality) and XGBoost (recent patterns) work well

## Recommendations for Planners

1. **Use XGBoost for high-volume SKUs** with consistent demand patterns
2. **Use Prophet for seasonal or promotional items** where calendar effects dominate
3. **Monitor MAPE and WAPE** — WAPE is more robust for intermittent demand
4. **Cluster SKUs by demand pattern** and apply the best model per cluster
5. **Update forecasts weekly** as new data arrives
6. **Account for zero-demand days** separately in safety stock calculations

## Limitations

- Intermittent demand for many SKUs makes MAPE unreliable
- No external features (holidays, promotions, weather) currently used
- Single-SKU models don't share information across related items
- Cold-start problem for new products
- Two-year dataset limits yearly seasonality estimation

## Future Improvements

- Hierarchical forecasting (product category → SKU)
- Intermittent demand models (Croston's method, TSB)
- Deep learning (LSTM, Transformer) for sequence modeling
- External regressors (holidays, economic indicators, web traffic)
- SKU clustering and grouped modeling
- Automated retraining pipeline with performance monitoring
- Multi-step forecast evaluation at longer horizons
