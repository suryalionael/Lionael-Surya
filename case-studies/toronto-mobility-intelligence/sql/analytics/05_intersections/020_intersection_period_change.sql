-- =============================================================================
-- Analytical question (ANALYTICAL_QUESTIONS.md D1 extended): Which matched intersections show
-- persistent KSI activity across many years (as opposed to one unlucky year), and which have
-- seen the largest recent change?
--
-- Metric definition:
--   distinct_years_with_ksi = COUNT(DISTINCT year) a matched KSI collision occurred at this
--       intersection, out of 21 possible years (2006-2026) -- the "persistence" signal: an
--       intersection with 8 collisions spread across 8 different years is a more consistent
--       pattern than 8 collisions clustered in a single year.
--   prior_5yr_count / recent_5yr_count / count_change -- same two-period comparison as
--       04_neighbourhoods/020_neighbourhood_period_change.sql (2016-2020 vs 2021-2025),
--       applied here at the matched-intersection grain instead of neighbourhood grain.
--
-- Grain: one row per intersection with >=1 matched KSI collision in EITHER window.
--
-- Limitation: this uses collision COUNTS only, deliberately -- not a traffic-volume-normalized
-- rate, per the approved Phase 1 decision that a same-year volume denominator does not exist
-- for most intersection-years (docs/DATA_MODEL.md S1). At the single-intersection grain, counts
-- are small (most intersections see 0-2 KSI collisions per 5-year window), so count_change is
-- shown as a raw integer, not a percentage -- a percentage on a base of 1 or 2 is not
-- meaningful. Same COVID-year caveat as the neighbourhood period-change query applies.
-- =============================================================================

WITH matched AS (
    SELECT DISTINCT b.intersection_key, b.collision_id, d.year
    FROM analytics.bridge_collision_intersection b
    JOIN analytics.fact_collisions f ON f.collision_id = b.collision_id
    JOIN analytics.dim_date d ON d.date_key = f.date_key
    WHERE b.match_status = 'matched'
),
per_intersection AS (
    SELECT
        intersection_key,
        COUNT(DISTINCT year) AS distinct_years_with_ksi,
        COUNT(DISTINCT collision_id) FILTER (WHERE year BETWEEN 2016 AND 2020) AS prior_5yr_count,
        COUNT(DISTINCT collision_id) FILTER (WHERE year BETWEEN 2021 AND 2025) AS recent_5yr_count,
        COUNT(DISTINCT collision_id) AS all_time_count
    FROM matched
    GROUP BY intersection_key
)
SELECT
    di.px,
    di.main_street,
    di.side1_street,
    p.all_time_count,
    p.distinct_years_with_ksi,
    p.prior_5yr_count,
    p.recent_5yr_count,
    (p.recent_5yr_count - p.prior_5yr_count) AS count_change
FROM per_intersection p
JOIN analytics.dim_intersection di ON di.intersection_key = p.intersection_key
WHERE p.prior_5yr_count > 0 OR p.recent_5yr_count > 0
ORDER BY p.distinct_years_with_ksi DESC, p.all_time_count DESC
LIMIT 25;
