-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md D1): Which signalized intersections have the
-- highest observed KSI collision counts, fatal counts, and pedestrian/cyclist involvement?
--
-- Metric definition: matched_ksi_collision_count = COUNT(DISTINCT collision_id) from
-- bridge_collision_intersection WHERE match_status = 'matched', joined to the intersection's
-- attributes. "Matched" means the collision's coordinates were within the approved 20m radius
-- of this signal (docs/DATA_MODEL.md S2) -- see the header of
-- 07_quality/010_spatial_match_monitoring.sql for how much of the citywide KSI total this
-- view can even see.
--
-- Grain: one row per intersection (px) that has at least one matched KSI collision.
--
-- Limitation -- read this deliberately as "highest OBSERVED count," not "most dangerous":
-- (1) this view only covers the ~44.7% of KSI collisions that matched a signalized
-- intersection at all -- a busy intersection with heavy midblock/approach collisions just
-- outside the 20m radius will be undercounted here, not because it's safer, but because of
-- the matching methodology's scope. (2) Raw count rewards busy locations; see
-- 06_exposure/010_intersection_relative_exposure.sql for a volume-aware (but cross-sectional,
-- non-trend) alternative. (3) No causal or engineering claim is made about *why* any
-- intersection ranks where it does.
--
-- [Phase 4 addition] latitude/longitude added -- plain double precision, not the PostGIS
-- geometry type, since Power BI's Map/ArcGIS visuals consume lat/long columns directly and
-- do not natively read PostGIS geometry. Added to support Power BI Page 1/2 intersection map
-- layers without requiring Power BI to touch dim_intersection.geom itself.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_intersection_risk AS
WITH matched AS (
    SELECT
        b.intersection_key,
        b.collision_id,
        f.acclass,
        f.pedestrian,
        f.cyclist
    FROM analytics.bridge_collision_intersection b
    JOIN analytics.fact_collisions f ON f.collision_id = b.collision_id
    WHERE b.match_status = 'matched'
    GROUP BY b.intersection_key, b.collision_id, f.acclass, f.pedestrian, f.cyclist
)
SELECT
    di.px,
    di.main_street,
    di.side1_street,
    di.side2_street,
    COUNT(DISTINCT m.collision_id) AS matched_ksi_collision_count,
    COUNT(DISTINCT m.collision_id) FILTER (WHERE m.acclass = 'Fatal Injury') AS fatal_collision_count,
    COUNT(DISTINCT m.collision_id) FILTER (WHERE m.pedestrian) AS pedestrian_involved_count,
    COUNT(DISTINCT m.collision_id) FILTER (WHERE m.cyclist) AS cyclist_involved_count,
    RANK() OVER (ORDER BY COUNT(DISTINCT m.collision_id) DESC) AS rank_by_observed_count,
    ST_Y(di.geom) AS latitude,
    ST_X(di.geom) AS longitude
FROM matched m
JOIN analytics.dim_intersection di ON di.intersection_key = m.intersection_key
GROUP BY di.px, di.main_street, di.side1_street, di.side2_street, di.geom
ORDER BY matched_ksi_collision_count DESC;
