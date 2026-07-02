{#
    Customer grain. Note the customer_id column here is populated from
    customer_unique_id (the durable, cross-order person identifier), not
    the order-scoped customer_id used elsewhere in the raw Olist tables.
    Aggregating on the order-scoped id would make every customer show
    exactly 1 lifetime order, which defeats the purpose of this model. See
    stg_customers and int_customer_lifetime docs for the full explanation.

    Join fct_orders to this model on fct_orders.customer_unique_id =
    dim_customers.customer_id.
#}

with customer_lifetime as (

    select * from {{ ref('int_customer_lifetime') }}

)

select
    customer_unique_id as customer_id,
    first_order_date,
    last_order_date,
    lifetime_orders,
    lifetime_spend,
    recency_days

from customer_lifetime
