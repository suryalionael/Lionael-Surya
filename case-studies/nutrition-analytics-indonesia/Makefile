.PHONY: install fetch validate inventory test missing-report merge clean-data rankings fetch-boundaries spatial

install:
	pip install -r requirements.txt

fetch:
	python -m src.ingestion.run_all

validate:
	python -m src.validation.run_validation

inventory:
	python -m src.ingestion.build_inventory

test:
	pytest -v

missing-report:
	python -m src.cleaning.profile_missing

merge:
	python -m src.cleaning.merge

clean-data: missing-report merge

rankings:
	python -m src.scoring.build_rankings

fetch-boundaries:
	python -m src.ingestion.fetch_geo_boundaries --source big_mirror

spatial:
	python -m src.geospatial.build_spatial_outputs
