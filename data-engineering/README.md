# Data Engineering

Pipelines that move data reliably from messy sources into a warehouse a business can query — the foundation everything else in this portfolio is built on.

## Focus

- Batch and streaming ingestion
- Orchestration (Apache Airflow)
- Data quality testing and validation
- Warehouse/lake loading patterns (star schema, partitioning)
- Containerized, reproducible pipelines (Docker)

## Projects

| Project | Status | Problem | Stack |
|---|---|---|---|
| [Retail Sales ETL Pipeline](retail-sales-etl-pipeline/) | 🔜 Planned | Automate ingestion of multi-store retail sales into a warehouse | Python, Airflow, PostgreSQL, Docker |
| [Streaming Clickstream Pipeline](streaming-clickstream-pipeline/) | 🔜 Planned | Real-time e-commerce clickstream ingestion for live dashboards | Kafka, Spark Structured Streaming, AWS S3 |

## Why This Matters for Recruiters

Data Engineer and Data Analyst co-op postings consistently ask for "experience building or maintaining ETL/ELT pipelines." These projects are built to demonstrate orchestration, idempotency, and data quality checks — not just a single `pandas.read_csv()` script.

Back to [main portfolio](../README.md).
