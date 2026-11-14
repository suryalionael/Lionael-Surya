-- Data-quality checks. Each row is one expectation; failing_rows must be 0.
-- R runs these after loading and fails loudly if a hard check breaks.

create or replace view analytics.v_data_quality_checks as
select 'negative delay minutes' as check_name, 0 as expected,
       count(*) as failing_rows
from analytics.stg_delays
where delay_minutes < 0

union all

select 'delay minutes above 24 hours', 0,
       count(*)
from analytics.stg_delays
where delay_minutes > 1440

union all

select 'missing delay date', 0,
       count(*)
from analytics.stg_delays
where delay_date is null

union all

select 'dates outside 2014-2026', 0,
       count(*)
from analytics.stg_delays
where delay_date < date '2014-01-01' or delay_date > date '2026-12-31'

union all

select 'invalid mode', 0,
       count(*)
from analytics.stg_delays
where mode not in ('subway', 'bus', 'streetcar')

union all

select 'exact duplicate incidents', 0,
       count(*)
from (
    select mode, delay_date, delay_time, line, location, delay_code,
           delay_minutes, count(*) as n
    from analytics.stg_delays
    group by mode, delay_date, delay_time, line, location, delay_code,
             delay_minutes
    having count(*) > 1
) duplicates

union all

select 'lines with no usable line value', 0,
       count(*)
from analytics.stg_delays
where line is null or line = 'UNKNOWN'

union all

select 'unknown cause category', 0,
       count(*)
from analytics.stg_delays
where cause_category = 'Unknown';

create or replace view analytics.v_data_quality_summary as
select
    count(*) as total_incidents,
    min(delay_date) as first_date,
    max(delay_date) as last_date,
    round(100.0 * count(*) filter (where major_delay) / count(*), 2)
        as major_delay_rate_pct,
    round(100.0 * count(*) filter (where location is null) / count(*), 2)
        as missing_location_pct,
    round(100.0 * count(*) filter (where cause_category = 'Unknown') / count(*), 2)
        as unknown_cause_pct
from analytics.stg_delays;
