# FloodCast Jakarta — Hyperlocal Flood Risk Early Warning

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![XGBoost](https://img.shields.io/badge/Model-XGBoost-orange?logo=xgboost)
![Leaflet](https://img.shields.io/badge/Map-Leaflet.js-green?logo=leaflet)
![Status](https://img.shields.io/badge/Status-Phase%201%20MVP-brightgreen)

> XGBoost-based flood risk prediction system for 15 pilot neighborhoods in South & East Jakarta. Generates calibrated flood probability at 6h, 12h, and 24h horizons with SHAP explainability — deployable locally with a single `python -m http.server` command.

**[Try the dashboard locally in under 5 minutes →](#quick-demo)**

---

## Problem Statement

Jakarta floods every rainy season. The Ciliwung corridor (South/East Jakarta) is among the hardest-hit areas, yet early warning for specific neighborhoods is sparse and often too late for effective evacuation. Emergency responders (BPBD) need **neighborhood-level probability forecasts** 6–24 hours ahead, not just district-level alerts.

---

## Solution & Approach

FloodCast combines three real-world data sources into a multi-horizon XGBoost ensemble that:

- Predicts flood risk for **15 pilot kelurahan** along the Ciliwung corridor
- Outputs **calibrated probabilities** at 6h, 12h, and 24h forecast horizons
- Classifies risk into 4 operational levels: Aman / Waspada / Siaga / Awas
- Explains each prediction with **SHAP feature attributions** in Bahasa Indonesia
- Visualizes results on an **interactive map dashboard** that runs fully offline

| Level | Probability | Recommended Action |
|---|---|---|
| **Aman** | < 20% | Normal monitoring |
| **Waspada** | 20–50% | Heightened alert, pre-position teams |
| **Siaga** | 50–80% | Deploy field teams, open evacuation shelters |
| **Awas** | ≥ 80% | Immediate evacuation |

---

## What I Built

- **End-to-end ML pipeline** — from raw BMKG rainfall + floodgate telemetry + DEM terrain data to trained, calibrated XGBoost models for 3 forecast horizons
- **Modular Python package** (`flood_risk/`) with separate layers for data ingestion, feature engineering, model training, evaluation, and SHAP explainability
- **Class imbalance handling** — flood events occur in only ~2–8% of hours; addressed via `scale_pos_weight` + balanced sample weights + threshold calibration (F1-maximizing sweep with minimum 70% recall constraint)
- **Hyperparameter tuning** — Optuna integration with 30–50 trials per horizon and early stopping
- **Interactive dashboard** — dark-themed HTML/JS app with Leaflet.js map, real-time horizon toggle, per-kelurahan detail panel, and audience-specific advisories (residents / BPBD / planners)
- **JSON export pipeline** — `predict.py --save-json` exports live model output directly into the dashboard data layer

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Data Sources                       │
│  BMKG rainfall API  │  Jakarta Open Data  │  DEMNAS  │
│  (3 stations, 1h)   │  (5 floodgates, 1h) │  (8m DEM)│
└────────────┬────────────────┬─────────────────┬─────┘
             │                │                 │
             ▼                ▼                 ▼
┌─────────────────────────────────────────────────────┐
│            flood_risk/data/pipeline.py               │
│   Feature engineering: ~50 features per row          │
│   (rolling rainfall, water level lags, TWI, etc.)    │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│         flood_risk/models/xgb_flood.py               │
│   MultiHorizonFloodModel                             │
│   ├── FloodRiskModel (6h)  — XGBClassifier           │
│   ├── FloodRiskModel (12h) — XGBClassifier           │
│   └── FloodRiskModel (24h) — XGBClassifier           │
│   Each model: threshold-calibrated, SHAP-explainable │
└──────────┬──────────────────────────┬───────────────┘
           │                          │
           ▼                          ▼
┌──────────────────┐      ┌───────────────────────────┐
│   CLI (predict.py)│      │  Dashboard                │
│   Progress bars   │      │  static-web-app/public/   │
│   + JSON export   │      │  Leaflet.js, no API key   │
└──────────────────┘      └───────────────────────────┘

           ── Phase 2 (Next) ──────────────────────────
           Azure Functions API  │  Azure Static Web Apps
           Azure OpenAI advisory│  CI/CD via GitHub Actions
```

---

## Quick Demo

Requires Python 3.11+. All data modules include synthetic fallbacks — **no API credentials needed** to run locally.

### 1. Setup

```bash
git clone https://github.com/suryalionael/Datathon-Dicoding2026-FloodRisk.git
cd Datathon-Dicoding2026-FloodRisk

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 2. Train the model

```bash
# Full training pipeline (uses synthetic data if API credentials are absent)
python train.py

# With Optuna hyperparameter tuning (30 trials per horizon, ~15 min)
python train.py --tune --trials 30

# Generate SHAP summary plots + importance CSVs
python train.py --shap

# Shorter history for faster dev iteration
python train.py --start 2021-01-01
```

Output saved to:
- `models/flood_xgb_{6,12,24}h.joblib` — serialised trained models
- `reports/validation_metrics.csv` — F1, ROC-AUC, PR-AUC per horizon
- `reports/shap/` — feature importance plots (if `--shap`)

### 3. Run predictions via CLI

```bash
# All 15 kelurahan, latest data
python predict.py --all

# Single kelurahan
python predict.py --kelurahan "Kampung Melayu"

# Historical timestamp
python predict.py --kelurahan "Bidara Cina" --timestamp "2024-02-15 18:00"
```

#### Example CLI output

```
==================================================
Kelurahan: Kampung Melayu | Time: 2024-02-15 18:00
   6h: [████████████████░░░░] 81.2%  →  Awas
  12h: [██████████████░░░░░░] 72.4%  →  Siaga
  24h: [████████████░░░░░░░░] 61.8%  →  Siaga

==================================================
Kelurahan: Ragunan | Time: 2024-02-15 18:00
   6h: [██░░░░░░░░░░░░░░░░░░] 11.9%  →  Aman
  12h: [██░░░░░░░░░░░░░░░░░░] 10.5%  →  Aman
  24h: [█░░░░░░░░░░░░░░░░░░░]  8.3%  →  Aman
```

### 4. Export predictions to JSON and launch dashboard

```bash
# Export model output to the dashboard data folder
python predict.py --all --save-json static-web-app/public/data/latest_predictions.json

# Serve dashboard (built-in Python HTTP server — no extra tools needed)
cd static-web-app/public
python -m http.server 8080
```

Open **http://localhost:8080** in your browser. The dashboard loads the JSON file directly — no backend, no Azure account, no API key required.

---

## Dashboard Features

- **Leaflet.js map** with color-coded circle markers (green → red by risk level)
- **Forecast horizon toggle** — switch between 6h, 12h, and 24h predictions
- **Kelurahan sidebar** — all 15 neighborhoods ranked by current risk
- **Summary cards** — count of high-risk kelurahan and estimated affected population
- **Detail panel** — per-kelurahan probability bar, top SHAP factors, and contextual advisory
- **Audience-specific advisories** — different text for: Warga (residents) / BPBD / Perencana Kota
- **API-ready** — seamlessly upgrades from local JSON to live Azure Functions when `floodcast_api` is set in localStorage

---

## Feature Engineering (~50 features)

| Group | Features |
|---|---|
| **Rainfall** | Rolling sums at 1/3/6/12/24/48/72h windows, max across stations, heavy/extreme rainfall flags, antecedent moisture proxy |
| **Water level** | Raw readings, hourly delta, lags 1–24h, rolling max/trend, hours above warning threshold |
| **Terrain (static)** | Elevation (m), slope (°), topographic wetness index, distance to river, log flow accumulation |
| **Calendar** | Sin–cos encoding of hour/month, wet season flag, peak flood months (Jan–Feb), peak storm hours (17–21) |

**Labelling:** `flood_Nh = 1` if any floodgate reaches ≥ 750 cm (Manggarai Siaga-2 threshold) within N hours. Max-pooled across stations — one exceedance anywhere in the network triggers the label.

---

## Model Evaluation

Training: 2018–2023 | Validation: 2024 hold-out (strict time-based split, no shuffling, no leakage)

| Horizon | Target F1 | Min Recall |
|---|---|---|
| 6h | ≥ 0.65 | ≥ 70% |
| 12h | ≥ 0.65 | ≥ 70% |
| 24h | ≥ 0.65 | ≥ 70% |

> Full validation metrics are written to `reports/validation_metrics.csv` after `python train.py` completes. Run with `--shap` to also generate SHAP waterfall plots and global importance CSVs.

**Imbalance strategy:** `scale_pos_weight` (ratio of negatives to positives) + `compute_sample_weight("balanced")` + post-training threshold sweep that maximises F1 subject to recall ≥ 70%. This prioritises catching real floods over minimising false alarms.

---

## Project Structure

```
Datathon-Dicoding2026-FloodRisk/
├── flood_risk/
│   ├── config.py              # kelurahan coordinates, thresholds, train/val split
│   ├── data/
│   │   ├── bmkg.py            # BMKG rainfall API client (synthetic fallback)
│   │   ├── water_level.py     # Jakarta Open Data floodgate loader + label builder
│   │   ├── dem.py             # DEMNAS/SRTM terrain feature extractor
│   │   └── pipeline.py        # master feature engineering pipeline
│   ├── models/
│   │   ├── xgb_flood.py       # FloodRiskModel + MultiHorizonFloodModel
│   │   └── tuner.py           # Optuna HPO (30–50 trials/horizon)
│   └── evaluation/
│       ├── metrics.py         # F1, ROC-AUC, PR-AUC, threshold calibration
│       └── explainability.py  # SHAP TreeExplainer: global + local + alert narrative
├── static-web-app/
│   └── public/
│       ├── index.html         # dashboard UI (dark theme, Leaflet.js)
│       ├── app.js             # dashboard logic (data loading, map, detail panel)
│       └── data/
│           └── predictions.json  # demo data (replaced by --save-json output)
├── azure-function/            # Phase 2: serverless API (predict, advisory, health)
├── train.py                   # training entrypoint
├── predict.py                 # CLI inference + --save-json export
└── requirements.txt
```

---

## 15 Pilot Kelurahan (Ciliwung Corridor)

| Kelurahan | Kecamatan | Elevation |
|---|---|---|
| Kampung Melayu | Jatinegara | 4.5 m |
| Bidara Cina | Jatinegara | 4.1 m |
| Bukit Duri | Tebet | 5.8 m |
| Kebon Baru | Tebet | 6.2 m |
| Pengadegan | Pancoran | 5.2 m |
| Rawajati | Pancoran | 5.5 m |
| Duren Tiga | Pancoran | 6.5 m |
| Cawang | Kramat Jati | 6.8 m |
| Balekambang | Kramat Jati | 7.2 m |
| Batu Ampar | Kramat Jati | 7.5 m |
| Cililitan | Kramat Jati | 7.8 m |
| Cipinang Melayu | Makasar | 8.4 m |
| Pejaten Timur | Pasar Minggu | 9.1 m |
| Halim Perdanakusuma | Makasar | 9.5 m |
| Ragunan | Pasar Minggu | 12.3 m |

---

## Data Sources

| Source | Data | Frequency | Coverage |
|---|---|---|---|
| [BMKG](https://data.bmkg.go.id) | Rainfall (mm) | Hourly | 3 stations covering pilot area |
| [Jakarta Open Data](https://data.jakarta.go.id) | Floodgate water level (cm) | Hourly | 5 gates: Manggarai, Karet, Kampung Melayu, Rawajati, Cawang |
| DEMNAS / SRTM | Elevation, slope, TWI, flow accumulation | Static | Per kelurahan centroid |

All data modules include statistically plausible **synthetic fallbacks** — the full pipeline runs without API credentials for development and demo purposes.

**To connect real data:**
- **BMKG rainfall:** update `_api_fetch` in `flood_risk/data/bmkg.py` with BMKG FTP credentials or Climate Data Portal API key
- **Floodgate levels:** register at [data.jakarta.go.id](https://data.jakarta.go.id) and update `_RESOURCE_IDS` in `flood_risk/data/water_level.py` with the correct Socrata resource IDs
- **DEM:** download DEMNAS tiles from [tanahair.indonesia.go.id](https://tanahair.indonesia.go.id) (8m) or use SRTM 30m fallback; pass GeoTIFF path to `DEMFeatureExtractor(dem_path=...)`

---

## Roadmap — Phase 2

Phase 1 MVP delivers a working local pipeline: CLI predictions, JSON export, and a fully functional offline dashboard. Phase 2 targets cloud deployment:

- [ ] **Azure Functions API** — deploy `azure-function/` (predict, advisory, health endpoints) to Consumption plan; cold start target < 4s
- [ ] **Azure Static Web Apps** — host dashboard with GitHub Actions CI/CD
- [ ] **Azure OpenAI advisory** — wire GPT-4o-mini for live audience-specific flood advisories (fallback templates already implemented)
- [ ] **Automated retraining** — scheduled Azure Function to retrain monthly with new telemetry data
- [ ] **BMKG + Jakarta Open Data integration** — replace synthetic stubs with live API feeds
- [ ] **Coverage expansion** — scale from 15 to 50+ kelurahan across DKI Jakarta

---

## Requirements

```
xgboost>=2.0.0
scikit-learn>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
shap>=0.44.0
optuna>=3.4.0
rasterio>=1.3.0
geopandas>=0.14.0
requests>=2.31.0
pyarrow>=14.0.0
matplotlib>=3.7.0
seaborn>=0.13.0
joblib>=1.3.0
python-dotenv>=1.0.0
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for the Dicoding AI Impact Challenge 2026. Contributions and feedback are welcome.*

---

## Portfolio Context

This project is mirrored here from its live repository: [github.com/suryalionael/Datathon-Dicoding2026-FloodRisk](https://github.com/suryalionael/Datathon-Dicoding2026-FloodRisk).

Back to [Case Studies](../README.md) · [main portfolio](../../README.md).
