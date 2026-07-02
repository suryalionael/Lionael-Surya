{#
    Regression guard: fct_orders.revenue, summed per order, must exactly match
    price + freight_value summed directly from stg_order_items for that same
    order. Both sides are derived from the same source data with no
    aggregation logic in between, so any drift here means a join in the
    intermediate layer fanned rows out (or dropped them) rather than a real
    data-quality issue - hence error severity.

    Deliberately hardcodes `price + freight_value` instead of calling the
    order_line_revenue() macro: this test exists to catch bugs in the
    pipeline that produces fct_orders.revenue, so it must recompute the
    formula independently rather than reuse the same macro fct_orders
    already calls - otherwise a bug in the macro itself would never surface.
#}

{{ config(severity='error') }}

with fct_check as (

    select
        order_id,
        sum(revenue) as fct_total

    from {{ ref('fct_orders') }}
    group by order_id

),

source_check as (

    select
        order_id,
        sum(price + freight_value) as source_total

    from {{ ref('stg_order_items') }}
    group by order_id

)

select
    fct_check.order_id,
    fct_check.fct_total,
    source_check.source_total

from fct_check
inner join source_check using (order_id)
where abs(fct_check.fct_total - source_check.source_total) > 0.01
