{#
    Business question: which customers are most valuable, and which are at
    risk of never ordering again, so retention work can be prioritised?

    Grain: one row per customer_unique_id (the durable, person-level key -
    not the order-scoped customer_id).

    Metric definitions:
      recency_days  = days between the customer's last order and the last
                      order timestamp in the dataset. Anchored to the data,
                      not CURRENT_DATE, because Olist is a static 2016-2018
                      extract (same convention as dim_customers).
      frequency     = distinct orders.
      monetary      = sum(price + freight_value), the same revenue definition
                      as fct_orders.
      *_score       = NTILE(5); 5 is best. Recency is ordered descending so
                      the shortest gap lands in bucket 5.
      segment       = CASE rule over the three scores (rules below).

    Limitations: NTILE forces equal-sized buckets even when the data is
    skewed. Olist has many one-order customers, so frequency ties are split
    across buckets arbitrarily. Segments describe this historical extract,
    not a live customer state.
#}

with customer_orders as (

    select
        customer_unique_id,
        count(distinct order_id) as frequency,
        sum(revenue) as monetary,
        max(order_purchase_timestamp)::date as last_order_date

    from {{ ref('fct_orders') }}
    group by customer_unique_id

),

dataset_as_of as (

    select max(order_purchase_timestamp)::date as as_of_date
    from {{ ref('fct_orders') }}

),

rfm_raw as (

    select
        customer_orders.customer_unique_id,
        (dataset_as_of.as_of_date - customer_orders.last_order_date) as recency_days,
        customer_orders.frequency,
        customer_orders.monetary,
        customer_orders.last_order_date,
        dataset_as_of.as_of_date

    from customer_orders
    cross join dataset_as_of

),

scored as (

    select
        *,
        ntile(5) over (
            order by recency_days desc, customer_unique_id
        ) as recency_score,
        ntile(5) over (
            order by frequency asc, customer_unique_id
        ) as frequency_score,
        ntile(5) over (
            order by monetary asc, customer_unique_id
        ) as monetary_score

    from rfm_raw

),

segmented as (

    select
        *,
        case
            when recency_score >= 4 and frequency_score >= 4 and monetary_score >= 4
                then 'Champions'
            when recency_score >= 3 and frequency_score >= 3
                then 'Loyal'
            when recency_score >= 4 and frequency_score between 2 and 3
                then 'Potential Loyalist'
            when recency_score >= 4 and frequency_score = 1
                then 'New'
            when recency_score <= 2 and frequency_score >= 3
                then 'At Risk'
            when recency_score <= 2 and frequency_score <= 2
                then 'Lost'
            else 'Needs Attention'
        end as segment

    from scored

)

select
    customer_unique_id,
    last_order_date,
    as_of_date,
    recency_days,
    frequency,
    monetary,
    recency_score,
    frequency_score,
    monetary_score,
    segment

from segmented
