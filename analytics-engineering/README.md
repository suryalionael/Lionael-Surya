# Analytics Engineering

The layer between raw warehouse data and business trust: transformation, testing, and documentation so that "revenue" means the same thing to every team that queries it.

## Focus

- Dimensional modeling (star schema: facts, dimensions, slowly changing dimensions)
- dbt transformation layers (staging → intermediate → marts)
- Data testing (`dbt test`, schema/uniqueness/referential checks)
- Documentation as a first-class deliverable (`dbt docs`)
- BI semantic layer feeding Power BI directly

## Projects

| Project | Status | Problem | Stack |
|---|---|---|---|
| [dbt E-Commerce Analytics Mart](dbt-ecommerce-analytics-mart/) | 🔜 Planned | Turn raw order/customer data into trusted, tested metrics | dbt, SQL, Power BI |
| [SaaS Subscription Metrics Model](saas-subscription-metrics-model/) | 🔜 Planned | Model MRR, churn, LTV for a subscription business | dbt, SQL, Power BI |

## Why This Matters for Recruiters

dbt is the single most-requested tool in current Analytics Engineer postings. These projects are built to show I understand *why* a staging/intermediate/marts layering exists — not just that I can write a `SELECT *`.

Back to [main portfolio](../README.md).
