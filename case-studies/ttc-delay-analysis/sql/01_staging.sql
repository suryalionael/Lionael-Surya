-- Staging view over the R-cleaned table. R supplies the harmonised columns;
-- this view exists so downstream SQL has one stable name and does not need
-- to know which source file a row came from.

create or replace view analytics.stg_delays as
select
    mode,
    delay_date,
    delay_time,
    hour,
    weekday,
    month,
    month_name,
    year,
    line,
    location,
    delay_code,
    cause_category,
    delay_minutes::numeric as delay_minutes,
    gap_minutes::numeric as gap_minutes,
    direction,
    major_delay,
    source_file
from raw.ttc_delays;

create index if not exists ttc_delays_date_idx on raw.ttc_delays (delay_date);
create index if not exists ttc_delays_mode_date_idx on raw.ttc_delays (mode, delay_date);
create index if not exists ttc_delays_line_idx on raw.ttc_delays (mode, line);
create index if not exists ttc_delays_major_idx on raw.ttc_delays (major_delay);
