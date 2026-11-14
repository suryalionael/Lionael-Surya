{#
    Business question: how concentrated is revenue across products, and which
    products belong in the A (vital few), B (useful many), and C (long tail)
    inventory tiers?

    Grain: one row per product with at least one order line.

    Metric definitions:
      product_revenue    = sum of fct_orders.revenue (price + freight).
      cumulative_revenue = running sum of product revenue, largest product
                           first (SUM() OVER with an ordered frame).
      cumulative_share   = cumulative_revenue / grand_total_revenue.
      abc_class          = A when the running share reaches 80% or less,
                           B through 95%, otherwise C. Classification uses
                           the unrounded shares; the reported share is
                           rounded to 6 dp for readability.

    Limitations: ABC thresholds are conventional, not derived from costs or
    margins. Ties in revenue are broken by product_id, so the boundary
    between classes can move when two products have identical revenue.
#}

with product_revenue as (

    select
        product_id,
        sum(revenue) as product_revenue,
        count(order_item_id) as units_sold

    from {{ ref('fct_orders') }}
    group by product_id

),

totals as (

    select sum(product_revenue) as grand_total_revenue
    from product_revenue

),

running as (

    select
        product_revenue.product_id,
        product_revenue.product_revenue,
        product_revenue.units_sold,
        row_number() over (
            order by product_revenue.product_revenue desc, product_revenue.product_id
        ) as revenue_rank,
        sum(product_revenue.product_revenue) over (
            order by product_revenue.product_revenue desc, product_revenue.product_id
            rows between unbounded preceding and current row
        ) as cumulative_revenue,
        totals.grand_total_revenue

    from product_revenue
    cross join totals

),

classified as (

    select
        *,
        round(product_revenue / nullif(grand_total_revenue, 0), 6) as product_share,
        round(cumulative_revenue / nullif(grand_total_revenue, 0), 6) as cumulative_share,
        case
            when cumulative_revenue / nullif(grand_total_revenue, 0) <= 0.80 then 'A'
            when cumulative_revenue / nullif(grand_total_revenue, 0) <= 0.95 then 'B'
            else 'C'
        end as abc_class

    from running

)

select
    product_id,
    product_revenue,
    units_sold,
    revenue_rank,
    cumulative_revenue,
    grand_total_revenue,
    product_share,
    cumulative_share,
    abc_class

from classified
order by revenue_rank
