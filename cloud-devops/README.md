# Cloud & DevOps

The operational layer underneath every other project in this portfolio: how pipelines and models actually get deployed, tested automatically, and run at low cost in the cloud.

## Focus

- CI/CD for data pipelines (not just application code)
- Infrastructure as Code basics (Terraform)
- Serverless data processing (AWS Lambda, Glue, Athena)
- Containerization (Docker) as the deployment unit across this whole repo

## Projects

| Project | Status | Problem | Stack |
|---|---|---|---|
| [CI/CD for Data Pipeline Deployment](cicd-data-pipeline-deployment/) | 🔜 Planned | Automatically lint, test, and deploy a dbt+Airflow pipeline | GitHub Actions, Docker, AWS |
| [Serverless ETL (AWS Lambda)](serverless-etl-aws-lambda/) | 🔜 Planned | Cost-efficient batch ETL without managing servers | AWS Lambda, S3, Glue, Athena |

## Why This Matters for Recruiters

A pipeline that only runs on my laptop isn't production engineering. These projects show I understand the difference between "it works" and "it's deployed, tested automatically on every change, and someone else could run it."

Back to [main portfolio](../README.md).
