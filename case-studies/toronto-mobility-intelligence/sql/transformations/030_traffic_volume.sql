-- staging.stg_tmc_counts -> clean.traffic_volume
-- Required: count_date (grain-defining, NOT NULL in clean.traffic_volume). px is legitimately
-- NULL for ~22% of rows (midblock/segment counts, per docs/DATA_MODEL.md S1.1) -- that is
-- kept as-is here, not rejected; the analytics layer is what restricts fact_traffic_volume
-- to px-identified rows, and that scoping decision is documented there, not silently baked
-- into cleaning.

TRUNCATE clean.traffic_volume;

WITH validated AS (
    SELECT
        src_id,
        clean.safe_int(px) AS px,
        clean.safe_date(count_date) AS count_date,
        NULLIF(TRIM(location_name), '') AS location_name,
        NULLIF(TRIM(centreline_type), '') AS centreline_type,
        clean.safe_bigint(centreline_id) AS centreline_id,
        NULLIF(TRIM(count_duration), '') AS count_duration,
        clean.safe_int(total_vehicle) AS total_vehicle,
        clean.safe_int(total_bike) AS total_bike,
        clean.safe_int(total_pedestrian) AS total_pedestrian,
        clean.safe_numeric(total_heavy_pct) AS total_heavy_pct,
        clean.safe_timestamp(am_peak_start) AS am_peak_start,
        clean.safe_int(am_peak_vehicle) AS am_peak_vehicle,
        clean.safe_int(am_peak_bike) AS am_peak_bike,
        clean.safe_numeric(am_peak_heavy_pct) AS am_peak_heavy_pct,
        clean.safe_timestamp(pm_peak_start) AS pm_peak_start,
        clean.safe_int(pm_peak_vehicle) AS pm_peak_vehicle,
        clean.safe_int(pm_peak_bike) AS pm_peak_bike,
        clean.safe_numeric(pm_peak_heavy_pct) AS pm_peak_heavy_pct,
        clean.safe_int(n_appr_vehicle) AS n_appr_vehicle,
        clean.safe_int(n_appr_bike) AS n_appr_bike,
        clean.safe_numeric(n_appr_heavy_pct) AS n_appr_heavy_pct,
        clean.safe_int(e_appr_vehicle) AS e_appr_vehicle,
        clean.safe_int(e_appr_bike) AS e_appr_bike,
        clean.safe_numeric(e_appr_heavy_pct) AS e_appr_heavy_pct,
        clean.safe_int(s_appr_vehicle) AS s_appr_vehicle,
        clean.safe_int(s_appr_bike) AS s_appr_bike,
        clean.safe_numeric(s_appr_heavy_pct) AS s_appr_heavy_pct,
        clean.safe_int(w_appr_vehicle) AS w_appr_vehicle,
        clean.safe_int(w_appr_bike) AS w_appr_bike,
        clean.safe_numeric(w_appr_heavy_pct) AS w_appr_heavy_pct,
        clean.safe_double(longitude) AS longitude,
        clean.safe_double(latitude) AS latitude,
        clean.safe_toronto_point(longitude, latitude) AS geom,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_tmc_counts s
),
flagged AS (
    SELECT *,
        CASE WHEN count_date IS NULL THEN 'missing_or_invalid_count_date' ELSE NULL END AS reject_reason
    FROM validated
)
INSERT INTO clean.traffic_volume
    (px, count_date, location_name, centreline_type, centreline_id, count_duration,
     total_vehicle, total_bike, total_pedestrian, total_heavy_pct,
     am_peak_start, am_peak_vehicle, am_peak_bike, am_peak_heavy_pct,
     pm_peak_start, pm_peak_vehicle, pm_peak_bike, pm_peak_heavy_pct,
     n_appr_vehicle, n_appr_bike, n_appr_heavy_pct,
     e_appr_vehicle, e_appr_bike, e_appr_heavy_pct,
     s_appr_vehicle, s_appr_bike, s_appr_heavy_pct,
     w_appr_vehicle, w_appr_bike, w_appr_heavy_pct,
     latitude, longitude, geom, _staging_id)
SELECT
    px, count_date, location_name, centreline_type, centreline_id, count_duration,
    total_vehicle, total_bike, total_pedestrian, total_heavy_pct,
    am_peak_start, am_peak_vehicle, am_peak_bike, am_peak_heavy_pct,
    pm_peak_start, pm_peak_vehicle, pm_peak_bike, pm_peak_heavy_pct,
    n_appr_vehicle, n_appr_bike, n_appr_heavy_pct,
    e_appr_vehicle, e_appr_bike, e_appr_heavy_pct,
    s_appr_vehicle, s_appr_bike, s_appr_heavy_pct,
    w_appr_vehicle, w_appr_bike, w_appr_heavy_pct,
    latitude, longitude, geom, src_id
FROM flagged
WHERE reject_reason IS NULL;

WITH validated AS (
    SELECT
        src_id,
        clean.safe_int(px) AS px,
        clean.safe_date(count_date) AS count_date,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_tmc_counts s
),
flagged AS (
    SELECT *,
        CASE WHEN count_date IS NULL THEN 'missing_or_invalid_count_date' ELSE NULL END AS reject_reason
    FROM validated
)
INSERT INTO clean.dq_rejected_rows (source_table, source_staging_id, natural_key, reject_reason, raw_row)
SELECT 'staging.stg_tmc_counts', src_id, COALESCE(px::text, '<null>') || '|' || COALESCE(count_date::text, '<null>'), reject_reason, raw_row
FROM flagged
WHERE reject_reason IS NOT NULL;

-- Non-destructive flags: coordinates present in source but unusable (unparseable or outside
-- the Toronto bounding box) -- row is kept, geom is simply NULL.
INSERT INTO clean.dq_flags (target_table, target_id, flag_type, detail)
SELECT 'clean.traffic_volume', tv.id, 'coordinate_missing_or_out_of_bounds',
       'source longitude/latitude: ' || COALESCE(s.longitude, '<null>') || ', ' || COALESCE(s.latitude, '<null>')
FROM clean.traffic_volume tv
JOIN staging.stg_tmc_counts s ON s.src_id = tv._staging_id
WHERE tv.geom IS NULL AND (NULLIF(TRIM(s.longitude), '') IS NOT NULL OR NULLIF(TRIM(s.latitude), '') IS NOT NULL);
