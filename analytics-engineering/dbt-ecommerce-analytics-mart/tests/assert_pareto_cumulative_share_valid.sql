{#
    Guard: the Pareto running share must stay in [0, 1] up to a tiny numeric
    tolerance, must be non-decreasing down the revenue ranking, and must end
    at exactly 1.0 (every product's revenue is counted once).
#}

with ordered as (

    select
        product_id,
        revenue_rank,
        cumulative_share,
        lag(cumulative_share) over (order by revenue_rank) as previous_share
    from {{ ref('mart_product_pareto') }}

),

final_row as (

    select cumulative_share
    from ordered
    order by revenue_rank desc
    limit 1

)

select *
from ordered
where cumulative_share < 0
   or cumulative_share > 1.000001
   or (previous_share is not null and cumulative_share < previous_share - 0.000001)

union all

select
    null::text as product_id,
    null::bigint as revenue_rank,
    cumulative_share,
    null::numeric as previous_share
from final_row
where abs(cumulative_share - 1.0) > 0.000001
