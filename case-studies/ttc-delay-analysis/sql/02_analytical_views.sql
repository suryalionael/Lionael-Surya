-- Analytical views. All heavy aggregation lives here; R reads these views
-- instead of re-implementing the same group-bys in dplyr.
--
-- "Delay minutes" is the TTC-reported minutes for an incident. Rankings use
-- a minimum of 100 incidents per group so a single severe event cannot put a
-- tiny line or location at the top.

create or replace view analytics.v_line_delay as
with grouped as (
    select
        mode,
        line,
        count(*) as incidents,
        count(*) filter (where major_delay) as major_incidents,
        sum(delay_minutes) as delay_minutes,
        round(avg(delay_minutes)::numeric, 2) as avg_delay_minutes,
        round(percentile_cont(0.5) within group (order by delay_minutes)::numeric, 2) as median_delay_minutes,
        round(percentile_cont(0.9) within group (order by delay_minutes)::numeric, 2) as p90_delay_minutes
    from analytics.stg_delays
    group by mode, line
    having count(*) >= 100
),
shares as (
    select
        *,
        round(100.0 * delay_minutes / sum(delay_minutes) over (partition by mode), 2)
            as pct_of_mode_delay_minutes,
        rank() over (partition by mode order by delay_minutes desc)
            as delay_rank_in_mode,
        sum(delay_minutes) over (partition by mode order by delay_minutes desc
                                 rows between unbounded preceding and current row)
            as cumulative_delay_minutes,
        round(
            100.0 * sum(delay_minutes) over (
                partition by mode order by delay_minutes desc
                rows between unbounded preceding and current row
            ) / sum(delay_minutes) over (partition by mode),
            2
        ) as cumulative_pct_of_mode
    from grouped
)
select * from shares;

create or replace view analytics.v_location_delay as
with grouped as (
    select
        mode,
        location,
        count(*) as incidents,
        count(*) filter (where major_delay) as major_incidents,
        sum(delay_minutes) as delay_minutes,
        round(avg(delay_minutes)::numeric, 2) as avg_delay_minutes
    from analytics.stg_delays
    where location is not null
    group by mode, location
    having count(*) >= 100
),
shares as (
    select
        *,
        round(100.0 * delay_minutes / sum(delay_minutes) over (partition by mode), 2)
            as pct_of_mode_delay_minutes,
        rank() over (partition by mode order by delay_minutes desc)
            as delay_rank_in_mode
    from grouped
)
select * from shares;

create or replace view analytics.v_daily_mode as
with daily as (
    select
        mode,
        delay_date,
        count(*) as incidents,
        count(*) filter (where major_delay) as major_incidents,
        sum(delay_minutes) as delay_minutes,
        round(avg(delay_minutes)::numeric, 2) as avg_delay_minutes
    from analytics.stg_delays
    group by mode, delay_date
)
select
    *,
    round(
        avg(incidents) over (
            partition by mode order by delay_date
            rows between 27 preceding and current row
        ), 2
    ) as incidents_28d_avg,
    sum(delay_minutes) over (
        partition by mode order by delay_date
        rows between 27 preceding and current row
    ) as delay_minutes_28d_sum,
    round(
        100.0 * delay_minutes
        / nullif(sum(delay_minutes) over (partition by delay_date), 0), 2
    ) as pct_of_day_all_modes
from daily;

create or replace view analytics.v_monthly_mode as
with monthly as (
    select
        mode,
        year,
        month,
        date_trunc('month', min(delay_date))::date as month_start,
        count(*) as incidents,
        count(*) filter (where major_delay) as major_incidents,
        sum(delay_minutes) as delay_minutes
    from analytics.stg_delays
    group by mode, year, month
)
select
    *,
    lag(delay_minutes) over (partition by mode order by year, month)
        as previous_month_delay_minutes,
    lag(delay_minutes, 12) over (partition by mode order by year, month)
        as delay_minutes_same_month_previous_year,
    round(
        100.0 * (delay_minutes - lag(delay_minutes, 12) over (
            partition by mode order by year, month
        )) / nullif(lag(delay_minutes, 12) over (
            partition by mode order by year, month
        ), 0),
        2
    ) as yoy_change_pct
from monthly;

create or replace view analytics.v_hour_weekday as
select
    mode,
    weekday,
    hour,
    count(*) as incidents,
    count(*) filter (where major_delay) as major_incidents,
    sum(delay_minutes) as delay_minutes,
    round(100.0 * count(*) filter (where major_delay) / count(*), 2)
        as major_delay_rate_pct
from analytics.stg_delays
group by mode, weekday, hour;

create or replace view analytics.v_cause_category as
with grouped as (
    select
        mode,
        cause_category,
        count(*) as incidents,
        count(*) filter (where major_delay) as major_incidents,
        sum(delay_minutes) as delay_minutes,
        round(avg(delay_minutes)::numeric, 2) as avg_delay_minutes
    from analytics.stg_delays
    group by mode, cause_category
)
select
    *,
    round(100.0 * incidents / sum(incidents) over (partition by mode), 2)
        as pct_of_mode_incidents,
    round(100.0 * delay_minutes / sum(delay_minutes) over (partition by mode), 2)
        as pct_of_mode_delay_minutes,
    round(100.0 * major_incidents / nullif(incidents, 0), 2)
        as major_delay_rate_pct
from grouped;
