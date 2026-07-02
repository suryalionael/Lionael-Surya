{#
    Olist's data is a static historical extract (2016-2018) rather than a live
    feed, so "recency" relative to CURRENT_DATE would just show ~3000 days for
    every customer and carry no signal. Instead we anchor recency to the most
    recent order_purchase_timestamp observed anywhere in the dataset, i.e.
    "days since last order, as of the last day we have data for".
#}

with order_items as (

    select * from {{ ref('int_order_items_enriched') }}

),

dataset_as_of as (

    select max(order_purchase_timestamp) as as_of_date
    from order_items

),

customer_agg as (

    select
        order_items.customer_unique_id,
        min(order_items.order_purchase_timestamp)::date as first_order_date,
        max(order_items.order_purchase_timestamp)::date as last_order_date,
        count(distinct order_items.order_id) as lifetime_orders,
        sum({{ order_line_revenue() }}) as lifetime_spend

    from order_items
    group by order_items.customer_unique_id

)

select
    customer_agg.customer_unique_id,
    customer_agg.first_order_date,
    customer_agg.last_order_date,
    customer_agg.lifetime_orders,
    customer_agg.lifetime_spend,
    (dataset_as_of.as_of_date::date - customer_agg.last_order_date) as recency_days

from customer_agg
cross join dataset_as_of
