-- staging.stg_ksi_collisions -> clean.collisions
-- Grain: person-per-collision, matching the source. Required for the row to be usable at
-- all: collision_id and accdate (both NOT NULL on clean.collisions, since accdate drives
-- the mandatory dim_date FK downstream). Coordinates are optional -- a missing/out-of-bounds
-- lat/long nulls the geom but keeps the person record (a collision's non-spatial attributes
-- are still analytically valid without a point on the map).
--
-- Deduplication: the natural key is (collision_id, veh_no, per_no). Duplicates (not expected
-- in this curated police dataset, but checked for defensively) keep the lowest source row id
-- and reject the rest, rather than silently double-counting a person in every rollup.

TRUNCATE clean.collisions;

WITH validated AS (
    SELECT
        src_id,
        NULLIF(TRIM(collision_id), '') AS collision_id,
        clean.safe_int(veh_no) AS veh_no,
        clean.safe_int(per_no) AS per_no,
        clean.safe_timestamp(accdate) AS accdate,
        NULLIF(TRIM(stname1), '') AS stname1,
        NULLIF(TRIM(stname2), '') AS stname2,
        NULLIF(TRIM(stname3), '') AS stname3,
        NULLIF(TRIM(acclass), '') AS acclass,
        NULLIF(TRIM(accloc), '') AS accloc,
        NULLIF(TRIM(traffictl), '') AS traffictl,
        NULLIF(TRIM(impactype), '') AS impactype,
        NULLIF(TRIM(visible), '') AS visible,
        NULLIF(TRIM(light), '') AS light,
        NULLIF(TRIM(rdsfcond), '') AS rdsfcond,
        NULLIF(TRIM(road_class), '') AS road_class,
        NULLIF(TRIM(vehtype), '') AS vehtype,
        clean.safe_int(invage) AS invage,
        NULLIF(TRIM(injury), '') AS injury,
        NULLIF(TRIM(drivact), '') AS drivact,
        NULLIF(TRIM(drivcond), '') AS drivcond,
        NULLIF(TRIM(pedact), '') AS pedact,
        NULLIF(TRIM(pedcond), '') AS pedcond,
        NULLIF(TRIM(manoeuvre), '') AS manoeuvre,
        NULLIF(TRIM(cyclistype), '') AS cyclistype,
        NULLIF(TRIM(road_user), '') AS road_user,
        clean.safe_int(fatal_no) AS fatal_no,
        clean.safe_bool(aggressive) AS aggressive,
        clean.safe_bool(distracted) AS distracted,
        clean.safe_bool(cyclist) AS cyclist,
        clean.safe_bool(motorcyclist) AS motorcyclist,
        clean.safe_bool(other_micromobility) AS other_micromobility,
        clean.safe_bool(older_adult) AS older_adult,
        clean.safe_bool(pedestrian) AS pedestrian,
        clean.safe_bool(red_light) AS red_light,
        clean.safe_bool(school_child) AS school_child,
        clean.safe_bool(heavy_truck) AS heavy_truck,
        NULLIF(TRIM(wardname), '') AS wardname,
        NULLIF(TRIM(division), '') AS division,
        NULLIF(TRIM(neighbourhood), '') AS neighbourhood_name,
        clean.safe_double(longitude) AS longitude,
        clean.safe_double(latitude) AS latitude,
        clean.safe_toronto_point(longitude, latitude) AS geom,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_ksi_collisions s
),
flagged AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY collision_id, veh_no, per_no ORDER BY src_id) AS natural_key_occurrence,
        CASE
            WHEN collision_id IS NULL THEN 'missing_collision_id'
            WHEN accdate IS NULL THEN 'missing_or_invalid_accdate'
            ELSE NULL
        END AS reject_reason
    FROM validated
),
final AS (
    SELECT *,
        CASE WHEN reject_reason IS NULL AND natural_key_occurrence > 1 THEN 'duplicate_natural_key' ELSE reject_reason END AS final_reason
    FROM flagged
)
INSERT INTO clean.collisions
    (collision_id, veh_no, per_no, accdate, stname1, stname2, stname3, acclass, accloc,
     traffictl, impactype, visible, light, rdsfcond, road_class, vehtype, invage, injury,
     drivact, drivcond, pedact, pedcond, manoeuvre, cyclistype, road_user, fatal_no,
     aggressive, distracted, cyclist, motorcyclist, other_micromobility, older_adult,
     pedestrian, red_light, school_child, heavy_truck, wardname, division,
     neighbourhood_name, latitude, longitude, geom, _staging_id)
SELECT
    collision_id, veh_no, per_no, accdate, stname1, stname2, stname3, acclass, accloc,
    traffictl, impactype, visible, light, rdsfcond, road_class, vehtype, invage, injury,
    drivact, drivcond, pedact, pedcond, manoeuvre, cyclistype, road_user, fatal_no,
    aggressive, distracted, cyclist, motorcyclist, other_micromobility, older_adult,
    pedestrian, red_light, school_child, heavy_truck, wardname, division,
    neighbourhood_name, latitude, longitude, geom, src_id
FROM final
WHERE final_reason IS NULL;

WITH validated AS (
    SELECT
        src_id,
        NULLIF(TRIM(collision_id), '') AS collision_id,
        clean.safe_int(veh_no) AS veh_no,
        clean.safe_int(per_no) AS per_no,
        clean.safe_timestamp(accdate) AS accdate,
        to_jsonb(s.*) AS raw_row
    FROM staging.stg_ksi_collisions s
),
flagged AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY collision_id, veh_no, per_no ORDER BY src_id) AS natural_key_occurrence,
        CASE
            WHEN collision_id IS NULL THEN 'missing_collision_id'
            WHEN accdate IS NULL THEN 'missing_or_invalid_accdate'
            ELSE NULL
        END AS reject_reason
    FROM validated
),
final AS (
    SELECT *,
        CASE WHEN reject_reason IS NULL AND natural_key_occurrence > 1 THEN 'duplicate_natural_key' ELSE reject_reason END AS final_reason
    FROM flagged
)
INSERT INTO clean.dq_rejected_rows (source_table, source_staging_id, natural_key, reject_reason, raw_row)
SELECT 'staging.stg_ksi_collisions', src_id,
       COALESCE(collision_id, '<null>') || '|' || COALESCE(veh_no::text, '<null>') || '|' || COALESCE(per_no::text, '<null>'),
       final_reason, raw_row
FROM final
WHERE final_reason IS NOT NULL;

-- Non-destructive flags: coordinates present in source but unusable -- row is kept, geom
-- is simply NULL. Only 1 of 7,587 distinct collisions was found to lack coordinates
-- entirely during Phase 1 research, so this is expected to be a very small set.
INSERT INTO clean.dq_flags (target_table, target_id, flag_type, detail)
SELECT 'clean.collisions', c.id, 'coordinate_missing_or_out_of_bounds',
       'source longitude/latitude: ' || COALESCE(s.longitude, '<null>') || ', ' || COALESCE(s.latitude, '<null>')
FROM clean.collisions c
JOIN staging.stg_ksi_collisions s ON s.src_id = c._staging_id
WHERE c.geom IS NULL AND (NULLIF(TRIM(s.longitude), '') IS NOT NULL OR NULLIF(TRIM(s.latitude), '') IS NOT NULL);
