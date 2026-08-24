-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md G4/D3, monitoring framing): has geocoding
-- coverage or the spatial match rate drifted across the 2006-2026 history -- e.g. do older
-- records geocode or match differently than recent ones, which would be a red flag for
-- comparing early years to recent years?
--
-- Metric definition:
--   geocoded_pct = 100 * (collisions with a non-null geom) / total_ksi_collisions
--   match_rate_pct = 100 * (collisions with bridge match_status = 'matched') / total_ksi_collisions
--
-- Grain: one row per year, plus a final ALL-YEARS summary row.
--
-- Limitation: this reports geocoding/matching COVERAGE, not accuracy -- a collision can have
-- valid-looking coordinates that are still imprecise. The 20m radius and its ~44.7% citywide
-- match rate were derived once, empirically, in Phase 1 (docs/DATA_MODEL.md S2) -- this query
-- exists to confirm that rate holds reasonably steady per year rather than being an artifact
-- of one unusual year dominating the citywide average.
-- =============================================================================

WITH by_year AS (
    SELECT
        d.year::text AS year,
        COUNT(DISTINCT f.collision_id) AS total_ksi_collisions,
        COUNT(DISTINCT f.collision_id) FILTER (WHERE f.geom IS NOT NULL) AS geocoded_collisions,
        COUNT(DISTINCT b.collision_id) FILTER (WHERE b.match_status = 'matched') AS matched_collisions
    FROM analytics.fact_collisions f
    JOIN analytics.dim_date d ON d.date_key = f.date_key
    LEFT JOIN analytics.bridge_collision_intersection b ON b.collision_id = f.collision_id
    WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
    GROUP BY d.year

    UNION ALL

    SELECT
        'ALL YEARS',
        COUNT(DISTINCT f.collision_id),
        COUNT(DISTINCT f.collision_id) FILTER (WHERE f.geom IS NOT NULL),
        COUNT(DISTINCT b.collision_id) FILTER (WHERE b.match_status = 'matched')
    FROM analytics.fact_collisions f
    LEFT JOIN analytics.bridge_collision_intersection b ON b.collision_id = f.collision_id
    WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
)
SELECT
    year,
    total_ksi_collisions,
    geocoded_collisions,
    ROUND(100.0 * geocoded_collisions / NULLIF(total_ksi_collisions, 0), 2) AS geocoded_pct,
    matched_collisions,
    ROUND(100.0 * matched_collisions / NULLIF(total_ksi_collisions, 0), 2) AS match_rate_pct,
    CASE
        WHEN ROUND(100.0 * matched_collisions / NULLIF(total_ksi_collisions, 0), 2) NOT BETWEEN 30 AND 60
        THEN 'REVIEW -- outside the 30-60% band seen in every other year'
        ELSE 'within normal range'
    END AS monitoring_flag
FROM by_year
ORDER BY (year = 'ALL YEARS'), year;
