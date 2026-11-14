-- Schemas used by the pipeline. R loads the cleaned incident table into
-- raw.ttc_delays; everything downstream is a versioned view in analytics.

create schema if not exists raw;
create schema if not exists analytics;
