-- Generated from the actual collision date range in clean.collisions (2006-01-01 through
-- whatever the most recent load's max(accdate) is) -- not an arbitrary or future-dated range.

TRUNCATE analytics.dim_date CASCADE;

INSERT INTO analytics.dim_date
    (date_key, year, month, month_name, quarter, week, day_of_month, day_of_week, day_name, is_weekend, season)
SELECT
    d::date,
    EXTRACT(YEAR FROM d)::smallint,
    EXTRACT(MONTH FROM d)::smallint,
    TRIM(TO_CHAR(d, 'Month')),
    EXTRACT(QUARTER FROM d)::smallint,
    EXTRACT(WEEK FROM d)::smallint,
    EXTRACT(DAY FROM d)::smallint,
    EXTRACT(DOW FROM d)::smallint,
    TRIM(TO_CHAR(d, 'Day')),
    EXTRACT(DOW FROM d) IN (0, 6),
    CASE
        WHEN (EXTRACT(MONTH FROM d), EXTRACT(DAY FROM d)) >= (12, 21)
          OR (EXTRACT(MONTH FROM d), EXTRACT(DAY FROM d)) < (3, 20) THEN 'Winter'
        WHEN (EXTRACT(MONTH FROM d), EXTRACT(DAY FROM d)) >= (3, 20)
         AND (EXTRACT(MONTH FROM d), EXTRACT(DAY FROM d)) < (6, 21) THEN 'Spring'
        WHEN (EXTRACT(MONTH FROM d), EXTRACT(DAY FROM d)) >= (6, 21)
         AND (EXTRACT(MONTH FROM d), EXTRACT(DAY FROM d)) < (9, 23) THEN 'Summer'
        ELSE 'Fall'
    END
FROM generate_series(
    (SELECT date_trunc('day', min(accdate)) FROM clean.collisions),
    (SELECT date_trunc('day', max(accdate)) FROM clean.collisions),
    interval '1 day'
) AS d;
