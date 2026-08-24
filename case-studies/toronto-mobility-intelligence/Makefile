.PHONY: up down reset psql schema ingest transform warehouse views validate test all status

include .env
export

COMPOSE = docker compose
PSQL    = $(COMPOSE) exec -T db psql -v ON_ERROR_STOP=1 -U $(POSTGRES_USER) -d $(POSTGRES_DB)

up: ## Start PostgreSQL + PostGIS and wait until healthy
	$(COMPOSE) up -d
	@echo "Waiting for database to be healthy..."
	@until [ "$$($(COMPOSE) ps -q db | xargs docker inspect -f '{{.State.Health.Status}}')" = "healthy" ]; do sleep 1; done
	@echo "Database is up."

down: ## Stop containers (data volume preserved)
	$(COMPOSE) down

reset: ## DESTROY the local database volume and start clean (local dev only)
	$(COMPOSE) down -v

psql: ## Open an interactive psql shell against the running database
	$(COMPOSE) exec db psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

schema: ## (Re)apply schema DDL: extensions, staging/clean/analytics tables
	for f in sql/schema/*.sql; do \
		echo "== $$f =="; \
		$(PSQL) -f /sql/schema/$$(basename $$f) || exit 1; \
	done

ingest: ## Download source data from Toronto Open Data and load into staging
	python3 etl/download/download_datasets.py
	python3 etl/ingestion/load_staging.py

transform: ## staging -> clean: typing, dedup, coordinate/date validation
	for f in sql/transformations/*.sql; do \
		echo "== $$f =="; \
		$(PSQL) -f /sql/transformations/$$(basename $$f) || exit 1; \
	done

warehouse: ## clean -> analytics schema: dim_date, dims, facts, spatial matching
	for f in sql/warehouse/*.sql; do \
		echo "== $$f =="; \
		$(PSQL) -f /sql/warehouse/$$(basename $$f) || exit 1; \
	done

views: ## Build the curated analytical query/view layer (sql/analytics/0*_*/*.sql)
	for f in $$(find sql/analytics -mindepth 2 -name '*.sql' | sort); do \
		echo "== $$f =="; \
		$(PSQL) -f /$$f || exit 1; \
	done

validate: ## Run the data-quality validation suite (PASS/WARN/FAIL)
	python3 etl/validation/run_checks.py

test: ## Run automated tests against the running database
	python3 -m pytest tests/ -v

all: up schema ingest transform warehouse views validate ## Full pipeline from scratch

status: ## Row counts across all layers
	$(PSQL) -f /sql/quality/000_row_counts.sql
