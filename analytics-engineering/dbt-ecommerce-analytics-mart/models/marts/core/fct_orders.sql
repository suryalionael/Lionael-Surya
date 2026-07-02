{#
    Order-line grain: one row per (order_id, order_item_id), i.e. one row per
    unit purchased. This is intentionally NOT deduplicated to order-level —
    an order with 3 items has 3 rows here. See fct_revenue_monthly for the
    order-level and month-level rollups.

    revenue = price + freight_value. This is the only place revenue is
    defined; every downstream metric (dim_customers.lifetime_spend,
    fct_revenue_monthly.total_revenue) is derived from this column so the
    definition never drifts.

    customer_unique_id is included alongside the raw, order-scoped
    customer_id because Olist mints a new customer_id per order — without
    customer_unique_id there would be no way to correctly join this fact to
    dim_customers, which is built at the true (person-level) customer grain.
#}

with order_items as (

    select * from {{ ref('int_order_items_enriched') }}

)

select
    order_id,
    order_item_id,
    customer_id,
    customer_unique_id,
    product_id,
    order_purchase_timestamp,
    price,
    freight_value,
    {{ order_line_revenue() }} as revenue

from order_items
