{#
    Guard: every RFM score must be an NTILE bucket between 1 and 5, and every
    customer must land in exactly one non-null segment.
#}

select *
from {{ ref('mart_customer_rfm') }}
where recency_score not between 1 and 5
   or frequency_score not between 1 and 5
   or monetary_score not between 1 and 5
   or segment is null
