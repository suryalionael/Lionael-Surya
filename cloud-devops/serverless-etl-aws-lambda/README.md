# Serverless ETL (AWS Lambda)

**Status:** 🔜 Planned

## Business Problem

A small team needs to process daily file drops (e.g., partner data feeds) but doesn't have the budget or need to run an always-on server/Airflow instance for a job that takes two minutes a day.

## Objective

Build a serverless ETL pipeline triggered by an S3 file upload, processed by AWS Lambda, cataloged by AWS Glue, and queryable via Athena — with zero idle infrastructure cost.

## Architecture

```mermaid
flowchart LR
    A[File Upload] --> B[(S3: raw/)]
    B -- S3 Event Trigger --> C[Lambda:<br/>validate + transform]
    C --> D[(S3: processed/<br/>Parquet)]
    D --> E[Glue Crawler]
    E --> F[Glue Data Catalog]
    F --> G[Athena Queries]
```

## Planned Tech Stack

- AWS Lambda (Python, `boto3`)
- AWS S3 (raw + processed buckets)
- AWS Glue (crawler + Data Catalog)
- AWS Athena (SQL querying over S3 data)
- Terraform for full infra provisioning

## Planned Deliverables

- [ ] Lambda function with S3 event trigger
- [ ] Transformation logic (CSV → partitioned Parquet)
- [ ] Glue crawler + catalog setup
- [ ] Sample Athena queries
- [ ] Terraform IaC for the entire stack
- [ ] Cost comparison write-up vs. the always-on Airflow approach in [`cicd-data-pipeline-deployment/`](../cicd-data-pipeline-deployment/)

---
Back to [Cloud & DevOps](../README.md) · [main portfolio](../../README.md).
