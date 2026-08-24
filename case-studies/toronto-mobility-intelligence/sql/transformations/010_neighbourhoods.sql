-- staging.stg_neighbourhoods -> clean.neighbourhoods
-- Required for the row to be usable: area_id, area_name, geometry. Everything else optional.

TRUNCATE clean.neighbourhoods;

WITH validated AS (
    SELECT
        src_id,
        clean.safe_int(area_id) AS area_id,
        NULLIF(TRIM(area_short_code), '') AS area_short_code,
        NULLIF(TRIM(area_name), '') AS area_name,
        NULLIF(TRIM(classification), '') AS classification,
        clean.safe_geom_from_geojson(geometry) AS geom,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_neighbourhoods s
),
flagged AS (
    SELECT *,
        CASE
            WHEN area_id IS NULL THEN 'missing_or_invalid_area_id'
            WHEN area_name IS NULL THEN 'missing_area_name'
            WHEN geom IS NULL THEN 'missing_or_unparseable_geometry'
            ELSE NULL
        END AS reject_reason
    FROM validated
)
INSERT INTO clean.neighbourhoods (area_id, area_short_code, area_name, classification, geom, _staging_id)
SELECT area_id, area_short_code, area_name, classification, ST_Multi(ST_SetSRID(geom, 4326)), src_id
FROM flagged
WHERE reject_reason IS NULL;

WITH validated AS (
    SELECT
        src_id,
        clean.safe_int(area_id) AS area_id,
        NULLIF(TRIM(area_name), '') AS area_name,
        clean.safe_geom_from_geojson(geometry) AS geom,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_neighbourhoods s
),
flagged AS (
    SELECT *,
        CASE
            WHEN area_id IS NULL THEN 'missing_or_invalid_area_id'
            WHEN area_name IS NULL THEN 'missing_area_name'
            WHEN geom IS NULL THEN 'missing_or_unparseable_geometry'
            ELSE NULL
        END AS reject_reason
    FROM validated
)
INSERT INTO clean.dq_rejected_rows (source_table, source_staging_id, natural_key, reject_reason, raw_row)
SELECT 'staging.stg_neighbourhoods', src_id, area_id::text, reject_reason, raw_row
FROM flagged
WHERE reject_reason IS NOT NULL;
