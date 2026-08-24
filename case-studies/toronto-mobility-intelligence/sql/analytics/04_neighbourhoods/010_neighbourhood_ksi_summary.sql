-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md C1/F1): Where in the city is the KSI burden
-- concentrated, and does that concentration hold up once normalized by neighbourhood area?
--
-- Metric definition:
--   ksi_collision_count  = COUNT(DISTINCT collision_id), all years 2006-2026
--   fatal_share_pct      = as defined in 01_temporal/010_annual_ksi_trend.sql
--   area_km2             = ST_Area(geom::geography) / 1,000,000 (geography cast for a true
--                           great-circle area, not a degree^2 approximation)
--   ksi_density_per_km2  = ksi_collision_count / area_km2
--
-- Grain: one row per neighbourhood (158 total; only neighbourhoods with >=1 KSI collision
-- appear, since this is an inner join).
--
-- Limitation (important, per project scope): this is a LAND-AREA density, not a per-capita
-- rate. A neighbourhood with high daytime foot/vehicle traffic but low resident population
-- (e.g. a commercial/downtown core) will show high density here for reasons unrelated to how
-- risky it is per resident or per trip. Neighbourhood Profiles (population/demographic data)
-- was identified in Phase 0 research but is explicitly NOT one of the four approved datasets
-- for this project -- a true per-capita or per-trip rate is a documented Phase 2/future
-- enhancement, not calculated here. Do not describe results from this view as "risk per
-- resident."
--
-- [Phase 4 addition] pedestrian_collision_count / cyclist_collision_count added -- same
-- collision-level-flag semantics as everywhere else in this project (see
-- docs/DATA_MODEL.md's fact_collisions column reference): COUNT(DISTINCT collision_id) WHERE
-- <flag>, i.e. "collisions involving a pedestrian/cyclist in this neighbourhood," not a count
-- of pedestrians/cyclists themselves. Added to support Power BI Page 2's "pedestrian/cyclist
-- concentration by geography" requirement without pushing that logic into Power BI.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_neighbourhood_ksi AS
WITH ksi AS (
    SELECT
        neighbourhood_key,
        COUNT(DISTINCT collision_id) AS ksi_collision_count,
        COUNT(DISTINCT collision_id) FILTER (WHERE acclass = 'Fatal Injury') AS fatal_collision_count,
        COUNT(DISTINCT collision_id) FILTER (WHERE pedestrian) AS pedestrian_collision_count,
        COUNT(DISTINCT collision_id) FILTER (WHERE cyclist) AS cyclist_collision_count
    FROM analytics.fact_collisions
    WHERE acclass IN ('Fatal Injury', 'Non-Fatal Injury')
      AND neighbourhood_key IS NOT NULL
    GROUP BY neighbourhood_key
)
SELECT
    n.area_name,
    n.area_id,
    k.ksi_collision_count,
    k.fatal_collision_count,
    ROUND(100.0 * k.fatal_collision_count / NULLIF(k.ksi_collision_count, 0), 2) AS fatal_share_pct,
    ROUND((ST_Area(n.geom::geography) / 1000000)::numeric, 3) AS area_km2,
    ROUND(k.ksi_collision_count / NULLIF(ST_Area(n.geom::geography) / 1000000, 0)::numeric, 2) AS ksi_density_per_km2,
    RANK() OVER (ORDER BY k.ksi_collision_count DESC) AS rank_by_raw_count,
    RANK() OVER (ORDER BY k.ksi_collision_count / NULLIF(ST_Area(n.geom::geography) / 1000000, 0) DESC) AS rank_by_density,
    k.pedestrian_collision_count,
    k.cyclist_collision_count
FROM ksi k
JOIN analytics.dim_neighbourhood n ON n.neighbourhood_key = k.neighbourhood_key
ORDER BY k.ksi_collision_count DESC;
