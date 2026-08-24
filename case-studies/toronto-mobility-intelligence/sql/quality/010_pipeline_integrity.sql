-- Core pipeline integrity checks. Each branch returns exactly one row:
-- (check_name, status ['PASS'|'WARN'|'FAIL'], detail). Read by etl/validation/run_checks.py.

-- No silent row loss: every staging row either made it to clean, or was logged as rejected.
SELECT 'no_silent_loss__ksi_collisions' AS check_name,
       CASE WHEN (SELECT count(*) FROM clean.collisions) + (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_ksi_collisions')
            = (SELECT count(*) FROM staging.stg_ksi_collisions)
       THEN 'PASS' ELSE 'FAIL' END AS status,
       format('staging=%s clean=%s rejected=%s',
              (SELECT count(*) FROM staging.stg_ksi_collisions),
              (SELECT count(*) FROM clean.collisions),
              (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_ksi_collisions')) AS detail

UNION ALL
SELECT 'no_silent_loss__tmc_counts',
       CASE WHEN (SELECT count(*) FROM clean.traffic_volume) + (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_tmc_counts')
            = (SELECT count(*) FROM staging.stg_tmc_counts)
       THEN 'PASS' ELSE 'FAIL' END,
       format('staging=%s clean=%s rejected=%s',
              (SELECT count(*) FROM staging.stg_tmc_counts),
              (SELECT count(*) FROM clean.traffic_volume),
              (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_tmc_counts'))

UNION ALL
SELECT 'no_silent_loss__traffic_signals',
       CASE WHEN (SELECT count(*) FROM clean.intersections) + (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_traffic_signals')
            = (SELECT count(*) FROM staging.stg_traffic_signals)
       THEN 'PASS' ELSE 'FAIL' END,
       format('staging=%s clean=%s rejected=%s',
              (SELECT count(*) FROM staging.stg_traffic_signals),
              (SELECT count(*) FROM clean.intersections),
              (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_traffic_signals'))

UNION ALL
SELECT 'no_silent_loss__neighbourhoods',
       CASE WHEN (SELECT count(*) FROM clean.neighbourhoods) + (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_neighbourhoods')
            = (SELECT count(*) FROM staging.stg_neighbourhoods)
       THEN 'PASS' ELSE 'FAIL' END,
       format('staging=%s clean=%s rejected=%s',
              (SELECT count(*) FROM staging.stg_neighbourhoods),
              (SELECT count(*) FROM clean.neighbourhoods),
              (SELECT count(*) FROM clean.dq_rejected_rows WHERE source_table = 'staging.stg_neighbourhoods'))

-- Duplicate natural keys
UNION ALL
SELECT 'duplicate_natural_key__fact_collisions',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s duplicate (collision_id, veh_no, per_no) groups', count(*))
FROM (SELECT collision_id, veh_no, per_no FROM analytics.fact_collisions GROUP BY 1,2,3 HAVING count(*) > 1) d

UNION ALL
SELECT 'duplicate_px_count_date__fact_traffic_volume',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s duplicate (px, count_date) groups', count(*))
FROM (SELECT px, count_date FROM analytics.fact_traffic_volume GROUP BY 1,2 HAVING count(*) > 1) d

UNION ALL
SELECT 'duplicate_px__dim_intersection',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s duplicate px values', count(*))
FROM (SELECT px FROM analytics.dim_intersection GROUP BY 1 HAVING count(*) > 1) d

-- Null natural/primary keys
UNION ALL
SELECT 'null_collision_id__fact_collisions',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s rows with NULL collision_id', count(*))
FROM analytics.fact_collisions WHERE collision_id IS NULL

UNION ALL
SELECT 'null_px__fact_traffic_volume',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s rows with NULL px (should be impossible -- fact_traffic_volume is scoped to px IS NOT NULL)', count(*))
FROM analytics.fact_traffic_volume WHERE px IS NULL

-- Invalid coordinates: anything that reached analytics with a non-null but invalid/out-of-bounds geometry
UNION ALL
SELECT 'invalid_geometry__fact_collisions',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s rows with a non-null geometry that fails ST_IsValid', count(*))
FROM analytics.fact_collisions WHERE geom IS NOT NULL AND NOT ST_IsValid(geom)

UNION ALL
SELECT 'invalid_geometry__fact_traffic_volume',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s rows with a non-null geometry that fails ST_IsValid', count(*))
FROM analytics.fact_traffic_volume WHERE geom IS NOT NULL AND NOT ST_IsValid(geom)

UNION ALL
SELECT 'invalid_geometry__dim_intersection',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s rows with an invalid geometry', count(*))
FROM analytics.dim_intersection WHERE NOT ST_IsValid(geom)

UNION ALL
SELECT 'invalid_geometry__dim_neighbourhood',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s rows with an invalid geometry', count(*))
FROM analytics.dim_neighbourhood WHERE NOT ST_IsValid(geom)

-- Invalid dates: collisions dated before the source's documented start (2006) or in the future
UNION ALL
SELECT 'invalid_dates__fact_collisions',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'WARN' END,
       format('%s rows with accdate before 2006-01-01 or after the current date', count(*))
FROM analytics.fact_collisions WHERE accdate < '2006-01-01' OR accdate > now()

-- Referential integrity (belt-and-suspenders on top of the FK constraints themselves)
UNION ALL
SELECT 'referential_integrity__date_key',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s fact_collisions rows whose date_key is missing from dim_date', count(*))
FROM analytics.fact_collisions f LEFT JOIN analytics.dim_date d ON f.date_key = d.date_key WHERE d.date_key IS NULL

UNION ALL
SELECT 'referential_integrity__intersection_key_traffic_volume',
       CASE WHEN count(*) = 0 THEN 'PASS' ELSE 'FAIL' END,
       format('%s fact_traffic_volume rows whose intersection_key does not resolve in dim_intersection', count(*))
FROM analytics.fact_traffic_volume f
LEFT JOIN analytics.dim_intersection di ON f.intersection_key = di.intersection_key
WHERE f.intersection_key IS NOT NULL AND di.intersection_key IS NULL

-- Neighbourhood-name join coverage (informational: flags if the free-text match degrades)
UNION ALL
SELECT 'neighbourhood_name_match_rate__fact_collisions',
       CASE WHEN unmatched_pct <= 5 THEN 'PASS' WHEN unmatched_pct <= 15 THEN 'WARN' ELSE 'FAIL' END,
       format('%s%% of collisions with a non-blank source neighbourhood failed to match dim_neighbourhood (%s of %s)',
              unmatched_pct, unmatched_with_name, total_with_name)
FROM (
    SELECT
        count(*) FILTER (WHERE c.neighbourhood_name IS NOT NULL AND n.neighbourhood_key IS NULL) AS unmatched_with_name,
        count(*) FILTER (WHERE c.neighbourhood_name IS NOT NULL) AS total_with_name,
        round(100.0 * count(*) FILTER (WHERE c.neighbourhood_name IS NOT NULL AND n.neighbourhood_key IS NULL)
              / NULLIF(count(*) FILTER (WHERE c.neighbourhood_name IS NOT NULL), 0), 2) AS unmatched_pct
    FROM clean.collisions c
    LEFT JOIN analytics.dim_neighbourhood n ON lower(TRIM(n.area_name)) = lower(TRIM(c.neighbourhood_name))
) x

ORDER BY 1;
