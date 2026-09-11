# FraudLens — Financial Transaction Risk Intelligence Platform

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=flat&logo=streamlit)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=flat&logo=scikitlearn)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4479A1?style=flat&logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker)
![AWS](https://img.shields.io/badge/AWS-232F3E?style=flat&logo=amazonaws)
![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=flat&logo=terraform)
![dbt](https://img.shields.io/badge/dbt-FF694B?style=flat&logo=dbt)

Real-time financial transaction risk scoring with explainable ML, leakage-safe feature engineering, and production AWS deployment.

**Status:** ✅ Done and working — all 10 phases complete, 139 tests passing, CI green.

**Standalone repository:** [suryalionael/fraudlens](https://github.com/suryalionael/fraudlens)

---

## What It Does

FraudLens receives an incoming transaction, validates it, generates behavioral features from historical context using only data available **before** the transaction timestamp, scores it with a trained ML model, explains the prediction via SHAP, calculates a risk decision combining ML predictions with deterministic rules, persists the result to PostgreSQL, and returns a structured response — all synchronously.

> **Which transactions should a fraud analyst investigate, and why?**

---

## Architecture

```text
                    INCOMING TRANSACTION
                            │
                            ▼
                         ALB
                            │
                            ▼
                     ECS / FastAPI
                            │
                    ┌───────┴────────┐
                    │                │
                    ▼                ▼
             Input Validation   Historical RDS
                                      │
                                      ▼
                             Feature Preparation
                                      │
                                      ▼
                                  ML Model
                                      │
                               ┌──────┴──────┐
                               │             │
                               ▼             ▼
                             SHAP        Risk Rules
                               │             │
                               └──────┬──────┘
                                      ▼
                                Risk Engine
                                      │
                                      ▼
                             Risk Decision
                                      │
                                      ▼
                           PostgreSQL risk.transaction_scores
                                      │
                          ┌───────────┴───────────┐
                          │                       │
                          ▼                       ▼
                       API Response        Investigation Queue
```

---

## What I Built

| Layer | What | Tech |
|-------|------|------|
| **Data Ingestion** | 5M-row transaction ingestion with schema validation | Python, PostgreSQL, chunked COPY |
| **Data Modeling** | dbt staging → intermediate → marts with 62 tests | dbt, SQL |
| **Feature Engineering** | Leakage-safe behavioral features (velocity, amounts, devices, merchants, locations) | Python, PostgreSQL |
| **Machine Learning** | Random Forest, Logistic Regression, XGBoost with class imbalance handling | scikit-learn, XGBoost |
| **Explainability** | SHAP TreeExplainer with feature contribution explanations | SHAP |
| **Risk Engine** | ML predictions (70%) + deterministic rules (30%) → risk score/level/action | Python |
| **API** | FastAPI with strict validation, idempotent scoring, PostgreSQL persistence | FastAPI, Pydantic |
| **Dashboard** | Streamlit 5-page dashboard: Executive, Risk Monitoring, Investigation Queue, Fraud Analysis, Model Performance | Streamlit |
| **Production** | Docker multi-stage build, non-root containers, CI/CD | Docker, GitHub Actions |
| **Cloud** | AWS ECS Fargate, RDS PostgreSQL, S3, ALB, CloudWatch, Terraform IaC | AWS, Terraform |

---

## Key Engineering Decisions

| Decision | Rationale |
|----------|-----------|
| Server-side feature generation | Prevents training/inference mismatch |
| Strict temporal cutoff (`< T`) | No future data leakage — critical for fraud detection |
| Forbidden precomputed fields | 5 known problematic dataset fields rejected at API validation |
| ML + Rules hybrid | ML provides pattern recognition; rules provide transparency |
| Idempotent scoring | Duplicate transaction_id returns existing result, no duplicate records |
| Persistence before response | API returns 500 if DB write fails — never fake success |
| SHAP explanations | TreeExplainer for tree-based models; feature contributions, not causal claims |

---

## End-to-End Transaction Flow

```
1. POST /score-transaction (raw transaction fields)
2. Historical context from PostgreSQL (strict timestamp < T cutoff)
3. Server-side behavioral feature generation
4. ML model predicts fraud probability
5. SHAP explains which features contributed
6. Risk engine combines ML + rules → risk score, level, action
7. Result persisted to PostgreSQL
8. Structured response returned
```

---

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Language | Python 3.12 |
| Database | PostgreSQL 16 |
| Transformation | dbt |
| ML | scikit-learn, XGBoost, SHAP |
| API | FastAPI, Pydantic |
| Dashboard | Streamlit |
| Container | Docker (multi-stage, non-root) |
| Cloud | AWS ECS Fargate, RDS, S3, ALB, CloudWatch |
| IaC | Terraform |
| CI/CD | GitHub Actions |
| Testing | pytest (139 tests) |

---

## Testing

- **139 Python tests** — unit, integration, API, temporal leakage, idempotency
- **62 dbt tests** — data quality (unique, not_null, accepted_values)
- **Ruff** — lint + format checks
- **Docker** — multi-stage build verified
- **CI/CD** — GitHub Actions with PostgreSQL service, lint, Docker build

---

## Portfolio Location

`machine-learning/fraudlens/`

**Source:** [suryalionael/fraudlens](https://github.com/suryalionael/fraudlens)
