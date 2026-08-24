-- Collision -> intersection spatial nearest-neighbor match.
--
-- Methodology (approved in docs/DECISION_LOG.md, empirically derived in docs/DATA_MODEL.md S2):
--   1. For each distinct collision with a valid geometry, find the single nearest signalized
--      intersection (by true great-circle distance, using geography, not raw degree distance).
--   2. If that nearest intersection is within 20.00 meters, the collision is 'matched'.
--   3. If a nearest intersection exists but is farther than 20m, the collision is
--      'unmatched_outside_radius' -- this is the expected, majority outcome (~55% of
--      collisions), not a failure: most KSI collisions are midblock or at unsignalized
--      intersections, which the Traffic Signals dataset does not cover.
--   4. If the collision has no usable geometry at all, it is 'unmatched_no_candidate'
--      (distinct from "searched and found nothing nearby").
-- The 20m radius is fixed by the approved decision and is NOT tuned here -- see
-- docs/DECISION_LOG.md for why 20m and not some other value.

TRUNCATE analytics.bridge_collision_intersection;

WITH distinct_collisions AS (
    -- One row per collision event (not per person) -- all person-rows of the same
    -- collision_id share the same location in the source, so DISTINCT ON is exact, not an
    -- approximation.
    SELECT DISTINCT ON (collision_id) collision_id, latitude, longitude, geom
    FROM clean.collisions
    ORDER BY collision_id, id
),
nearest AS (
    SELECT
        dc.collision_id,
        dc.latitude,
        dc.longitude,
        cand.intersection_key,
        cand.px,
        cand.distance_m
    FROM distinct_collisions dc
    LEFT JOIN LATERAL (
        SELECT
            di.intersection_key,
            di.px,
            ST_Distance(di.geom::geography, dc.geom::geography) AS distance_m
        FROM analytics.dim_intersection di
        ORDER BY di.geom::geography <-> dc.geom::geography
        LIMIT 1
    ) cand ON dc.geom IS NOT NULL
)
INSERT INTO analytics.bridge_collision_intersection
    (collision_id, collision_lat, collision_lon, intersection_key, matched_px,
     match_distance_m, match_status, match_radius_m_used)
SELECT
    collision_id,
    latitude,
    longitude,
    CASE WHEN intersection_key IS NOT NULL AND distance_m <= 20.0 THEN intersection_key END,
    CASE WHEN intersection_key IS NOT NULL AND distance_m <= 20.0 THEN px END,
    CASE WHEN intersection_key IS NOT NULL AND distance_m <= 20.0 THEN round(distance_m::numeric, 2) END,
    CASE
        WHEN intersection_key IS NULL THEN 'unmatched_no_candidate'
        WHEN distance_m <= 20.0 THEN 'matched'
        ELSE 'unmatched_outside_radius'
    END,
    20.00
FROM nearest;
