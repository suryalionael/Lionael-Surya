with order_items as (

    select * from {{ ref('stg_order_items') }}

),

orders as (

    select * from {{ ref('stg_orders') }}

),

customers as (

    select * from {{ ref('stg_customers') }}

),

products as (

    select * from {{ ref('int_products_enriched') }}

),

joined as (

    select
        order_items.order_id,
        order_items.order_item_id,
        orders.customer_id,
        customers.customer_unique_id,
        order_items.product_id,
        products.category_name,
        order_items.seller_id,
        orders.order_status,
        orders.order_purchase_timestamp,
        order_items.price,
        order_items.freight_value

    from order_items
    inner join orders
        on order_items.order_id = orders.order_id
    inner join customers
        on orders.customer_id = customers.customer_id
    left join products
        on order_items.product_id = products.product_id

)

select * from joined
