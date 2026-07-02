{#
    Product grain. avg_price and total_units_sold are computed from
    fct_orders (order-line grain, one row per unit sold) so they stay
    consistent with the mart's single revenue/price source of truth.
#}

with fct_orders as (

    select * from {{ ref('fct_orders') }}

),

products as (

    select * from {{ ref('int_products_enriched') }}

),

product_sales as (

    select
        product_id,
        avg(price) as avg_price,
        count(order_item_id) as total_units_sold

    from fct_orders
    group by product_id

)

select
    products.product_id,
    products.category_name,
    coalesce(product_sales.avg_price, 0) as avg_price,
    coalesce(product_sales.total_units_sold, 0) as total_units_sold

from products
left join product_sales
    on products.product_id = product_sales.product_id
