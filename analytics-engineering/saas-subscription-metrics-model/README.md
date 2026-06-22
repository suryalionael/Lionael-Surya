# SaaS Subscription Metrics Model

**Status:** 🔜 Planned

## Business Problem

A SaaS company's finance and growth teams need consistent, trusted definitions for MRR, churn rate, LTV, and cohort retention — metrics that are notoriously easy to calculate inconsistently (e.g., does a downgrade count as partial churn?).

## Objective

Build a dbt model layer that codifies subscription-metric definitions once, with tests guaranteeing internal consistency (e.g., `starting_mrr + new_mrr - churned_mrr = ending_mrr` for every period), and expose them through a Power BI cohort-retention dashboard.

## Planned Tech Stack

- dbt-core, SQL window functions for cohort logic
- PostgreSQL/Snowflake
- Power BI (cohort heatmap, MRR waterfall chart)

## Planned Deliverables

- [ ] `fct_subscription_events` (signup, upgrade, downgrade, cancellation)
- [ ] `mrr_movement` model (new/expansion/contraction/churned MRR bridge)
- [ ] Cohort retention model (% of cohort active at month N)
- [ ] dbt tests asserting the MRR bridge reconciles to zero
- [ ] Power BI MRR waterfall + cohort retention heatmap

---
Back to [Analytics Engineering](../README.md) · [main portfolio](../../README.md).
