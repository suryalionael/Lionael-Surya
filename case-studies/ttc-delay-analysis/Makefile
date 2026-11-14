# TTC delay analysis - reproducible pipeline
# The database defaults below match docker-compose.yml. Override with
# TTC_DB_HOST / TTC_DB_PORT / TTC_DB_NAME / TTC_DB_USER / TTC_DB_PASSWORD.

RSCRIPT ?= Rscript
DB_HOST ?= localhost
DB_PORT ?= 5434
DB_NAME ?= ttc_delays
DB_USER ?= ttc

.PHONY: all deps db-up db-create ingest clean load eda model diagnostics robustness findings test report pipeline clean-outputs

all: pipeline

deps:
	$(RSCRIPT) -e 'renv::restore(prompt = FALSE)'

db-up:
	docker compose up -d postgres

db-create:
	$(RSCRIPT) -e 'source("R/00_config.R"); ensure_database()'

ingest:
	$(RSCRIPT) R/01_ingestion.R

clean:
	$(RSCRIPT) R/02_cleaning.R

load:
	$(RSCRIPT) R/03_load_postgres.R

eda:
	$(RSCRIPT) R/04_eda.R

model:
	$(RSCRIPT) R/05_modeling.R

diagnostics:
	$(RSCRIPT) R/06_diagnostics.R

robustness:
	$(RSCRIPT) R/07_robustness.R

findings:
	$(RSCRIPT) R/08_findings.R

test:
	$(RSCRIPT) -e 'testthat::test_dir("tests/testthat")'

report:
	$(RSCRIPT) -e 'rmarkdown::render("reports/ttc_delay_report.Rmd", output_format = "html_document", output_file = "ttc_delay_report.html")'

pipeline: ingest clean load eda model diagnostics robustness findings test report

clean-outputs:
	rm -rf outputs/figures/*.png outputs/tables/*.csv outputs/models/*.rds
