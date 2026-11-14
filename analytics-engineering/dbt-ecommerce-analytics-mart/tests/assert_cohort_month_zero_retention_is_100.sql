{#
    Guard: every cohort's acquisition month (month_index = 0) must retain
    exactly 100% of the cohort, and retention must never exceed 1.0.
#}

select *
from {{ ref('mart_cohort_retention') }}
where (month_index = 0 and retention_rate <> 1.0)
   or retention_rate > 1.0
   or retention_rate < 0
