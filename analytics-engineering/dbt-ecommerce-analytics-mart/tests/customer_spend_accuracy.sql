{#
    Reconciliation check: dim_customers.lifetime_spend (built from order-item
    price + freight_value) is compared against what the customer actually
    paid, per olist_order_payments. Unlike order_revenue_consistency, these
    two are NOT expected to match exactly in real Olist data - payment_value
    can include installment interest, vouchers, or gift cards that don't map
    1:1 onto item price/freight. Warn severity flags customers whose paid
    total diverges from their item-based spend by more than 5% (or R$1,
    whichever is larger) as a genuine data-quality signal worth reviewing,
    not a broken pipeline.
#}

{{ config(severity='warn') }}

with paid as (

    select
        orders.customer_unique_id,
        sum(payments.payment_value) as total_paid

    from {{ ref('stg_order_payments') }} as payments
    inner join {{ ref('int_orders_enriched') }} as orders
        on payments.order_id = orders.order_id
    group by orders.customer_unique_id

),

item_based as (

    select
        customer_id as customer_unique_id,
        lifetime_spend

    from {{ ref('dim_customers') }}

)

select
    item_based.customer_unique_id,
    item_based.lifetime_spend,
    paid.total_paid,
    abs(item_based.lifetime_spend - paid.total_paid) as diff

from item_based
inner join paid on item_based.customer_unique_id = paid.customer_unique_id
where abs(item_based.lifetime_spend - paid.total_paid) > greatest(item_based.lifetime_spend * 0.05, 1.00)
