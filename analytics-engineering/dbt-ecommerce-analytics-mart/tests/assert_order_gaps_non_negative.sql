{#
    Guard: a repeat order cannot precede the customer's previous order, so
    every gap must be zero or positive.
#}

select *
from {{ ref('mart_order_gaps') }}
where gap_days < 0
   or previous_order_date > order_date
