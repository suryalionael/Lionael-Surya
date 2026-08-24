-- staging.stg_traffic_signals -> clean.intersections
-- Required: px (the natural key used to join to fact_traffic_volume and the collision
-- spatial match), and geom. Duplicate px (not observed in Phase 1/2 research, but handled
-- defensively) keeps the first occurrence and rejects the rest rather than erroring or
-- silently overwriting.

TRUNCATE clean.intersections;

WITH validated AS (
    SELECT
        src_id,
        clean.safe_int(px) AS px,
        NULLIF(TRIM(main_street), '') AS main_street,
        NULLIF(TRIM(side1_street), '') AS side1_street,
        NULLIF(TRIM(side2_street), '') AS side2_street,
        NULLIF(TRIM(midblock_route), '') AS midblock_route,
        NULLIF(TRIM(signalsystem), '') AS signal_system,
        NULLIF(TRIM(control_mode), '') AS control_mode,
        clean.safe_bool(audiblepedsignal) AS audible_ped_signal,
        clean.safe_bool(transit_preempt) AS transit_preempt,
        clean.safe_bool(fire_preempt) AS fire_preempt,
        clean.safe_bool(rail_preempt) AS rail_preempt,
        clean.safe_bool(led_blankout_sign) AS led_blankout_sign,
        clean.safe_date(activationdate) AS activation_date,
        clean.safe_geom_from_geojson(geometry) AS geom,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_traffic_signals s
),
flagged AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY px ORDER BY src_id) AS px_occurrence,
        CASE
            WHEN px IS NULL THEN 'missing_or_invalid_px'
            WHEN geom IS NULL THEN 'missing_or_unparseable_geometry'
            WHEN NOT clean.point_in_toronto_bounds(ST_SetSRID(geom, 4326)) THEN 'geometry_out_of_bounds'
            ELSE NULL
        END AS reject_reason
    FROM validated
),
final AS (
    SELECT *,
        CASE WHEN reject_reason IS NULL AND px_occurrence > 1 THEN 'duplicate_px' ELSE reject_reason END AS final_reason
    FROM flagged
)
INSERT INTO clean.intersections
    (px, main_street, side1_street, side2_street, midblock_route, signal_system, control_mode,
     audible_ped_signal, transit_preempt, fire_preempt, rail_preempt, led_blankout_sign,
     activation_date, latitude, longitude, geom, _staging_id)
SELECT
    px, main_street, side1_street, side2_street, midblock_route, signal_system, control_mode,
    audible_ped_signal, transit_preempt, fire_preempt, rail_preempt, led_blankout_sign,
    activation_date, ST_Y(geom), ST_X(geom), ST_SetSRID(geom, 4326), src_id
FROM final
WHERE final_reason IS NULL;

WITH validated AS (
    SELECT
        src_id,
        clean.safe_int(px) AS px,
        clean.safe_geom_from_geojson(geometry) AS geom,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_traffic_signals s
),
flagged AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY px ORDER BY src_id) AS px_occurrence,
        CASE
            WHEN px IS NULL THEN 'missing_or_invalid_px'
            WHEN geom IS NULL THEN 'missing_or_unparseable_geometry'
            WHEN NOT clean.point_in_toronto_bounds(ST_SetSRID(geom, 4326)) THEN 'geometry_out_of_bounds'
            ELSE NULL
        END AS reject_reason
    FROM validated
),
final AS (
    SELECT *,
        CASE WHEN reject_reason IS NULL AND px_occurrence > 1 THEN 'duplicate_px' ELSE reject_reason END AS final_reason
    FROM flagged
)
INSERT INTO clean.dq_rejected_rows (source_table, source_staging_id, natural_key, reject_reason, raw_row)
SELECT 'staging.stg_traffic_signals', src_id, px::text, final_reason, raw_row
FROM final
WHERE final_reason IS NOT NULL;
