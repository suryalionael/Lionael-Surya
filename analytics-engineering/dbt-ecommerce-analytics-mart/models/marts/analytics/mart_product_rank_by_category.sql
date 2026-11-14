{#
    Business question: which products drive the most revenue inside each
    category, so assortment and promotion decisions can focus on the real
    leaders?

    Grain: one row per product that ranks in the top 3 of its category by
    revenue.

    Metric definitions:
      product_revenue        = sum of fct_orders.revenue (price + freight).
      units_sold             = count of order-line rows (Olist's order_items
                               grain is one row per unit).
      revenue_rank_row_number = ROW_NUMBER ordered by revenue descending,
                               with product_id as a deterministic tie-break.
      revenue_rank            = RANK ordered by revenue descending; tied
                               products share a rank.

    The model keeps the top 3 rows per category by ROW_NUMBER. If products
    tie at the boundary, RANK may show the same rank for several rows.

    Limitations: revenue includes freight and is not margin. Categories come
    from dim_products; products with no sales never appear here.
#}

with product_revenue as (

    select
        product_id,
        sum(revenue) as product_revenue,
        count(order_item_id) as units_sold

    from {{ ref('fct_orders') }}
    group by product_id

),

categorized as (

    select
        product_revenue.product_id,
        coalesce(dim_products.category_name, 'unknown') as category_name,
        product_revenue.product_revenue,
        product_revenue.units_sold

    from product_revenue
    left join {{ ref('dim_products') }} as dim_products
        on product_revenue.product_id = dim_products.product_id

),

ranked as (

    select
        *,
        row_number() over (
            partition by category_name
            order by product_revenue desc, product_id
        ) as revenue_rank_row_number,
        rank() over (
            partition by category_name
            order by product_revenue desc
        ) as revenue_rank

    from categorized

)

select
    category_name,
    product_id,
    product_revenue,
    units_sold,
    revenue_rank_row_number,
    revenue_rank

from ranked
where revenue_rank_row_number <= 3
order by category_name, revenue_rank_row_number, product_id
