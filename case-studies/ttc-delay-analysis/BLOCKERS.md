# Blockers and workarounds

## Docker daemon not running

The Docker daemon was not running when the pipeline was executed. The
`docker-compose.yml` file is provided and is the intended clean-environment
path (PostgreSQL 16 on port 5434, user `ttc`, database `ttc_delays`).

The pipeline was run against the existing local PostgreSQL 16 instance on
port 5432 as the current OS user. The same R code was used; only the
`TTC_DB_HOST`, `TTC_DB_PORT`, `TTC_DB_USER`, `TTC_DB_PASSWORD`, and
`TTC_DB_NAME` environment variables changed. No model or SQL code differs
between the two paths.

## Quarto not installed

Quarto is not installed on this machine. The stakeholder report is written as
R Markdown and rendered to HTML with `rmarkdown`, as allowed by the brief.
Pandoc was installed to make the HTML render work.

## No other blockers

All raw TTC resources were reachable from the City of Toronto CKAN API. The
Olist data used by the separate dbt repository was already present locally
and loaded in PostgreSQL.
