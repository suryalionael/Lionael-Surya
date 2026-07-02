{#
    The official monthly revenue metric layer. total_revenue is a straight
    sum of fct_orders.revenue (price + freight_value) — never recomputed or
    redefined here. Grain: one row per calendar month.
#}

with fct_orders as (

    select * from {{ ref('fct_orders') }}

),

orders_with_month as (

    -- computed once here rather than repeated in both the select list and
    -- group by of the aggregation below
    select
        *,
        date_trunc('month', order_purchase_timestamp)::date as month

    from fct_orders

),

monthly as (

    select
        month,
        sum(revenue) as total_revenue,
        count(distinct order_id) as total_orders,
        count(distinct customer_unique_id) as active_customers

    from orders_with_month
    group by month

)

select * from monthly
order by month
