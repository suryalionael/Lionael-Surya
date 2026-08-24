-- =============================================================================
-- [Phase 4 new] Not built in Phase 3 -- season (4 buckets) was, but a finer month-level (12
-- buckets) breakdown was identified as a genuine gap when designing Power BI Page 3, which
-- explicitly asks for a "month" pattern distinct from "season".
--
-- Analytical question (ANALYTICAL_QUESTIONS.md B2, extended to month grain): which calendar
-- months see more or fewer KSI collisions, at a finer resolution than season alone (e.g. to
-- spot holiday-period or back-to-school effects season can't distinguish)?
--
-- Metric definition: ksi_collision_count and fatal_share_pct as defined elsewhere in this
-- project, aggregated across all years 2006-2026 per calendar month (not a year x month
-- trend -- that grain is already available by combining v_annual_ksi's year dimension with
-- dim_date.month in a direct query if ever needed, and wasn't built as a separate view to
-- avoid an unused 21 x 12 = 252-row view with no identified visual consuming it).
--
-- Grain: one row per calendar month (1-12), always 12 rows.
--
-- Limitation: aggregating across all 21 years smooths out any year-specific anomaly but also
-- means a month's total is sensitive to how many years of data exist for partial year 2026
-- (only January-early August 2026 is present) -- September-December show 20 years of data,
-- January-July show 21. month_year_coverage is included so this isn't silently misleading.
-- =============================================================================

CREATE OR REPLACE VIEW analytics.v_collision_monthly_pattern AS
SELECT
    d.month,
    TRIM(d.month_name) AS month_name,
    COUNT(DISTINCT f.collision_id) AS ksi_collision_count,
    COUNT(DISTINCT f.collision_id) FILTER (WHERE f.acclass = 'Fatal Injury') AS fatal_collision_count,
    ROUND(
        100.0 * COUNT(DISTINCT f.collision_id) FILTER (WHERE f.acclass = 'Fatal Injury')
        / NULLIF(COUNT(DISTINCT f.collision_id), 0),
        2
    ) AS fatal_share_pct,
    COUNT(DISTINCT d.year) AS month_year_coverage
FROM analytics.fact_collisions f
JOIN analytics.dim_date d ON d.date_key = f.date_key
WHERE f.acclass IN ('Fatal Injury', 'Non-Fatal Injury')
GROUP BY d.month, d.month_name
ORDER BY d.month;
