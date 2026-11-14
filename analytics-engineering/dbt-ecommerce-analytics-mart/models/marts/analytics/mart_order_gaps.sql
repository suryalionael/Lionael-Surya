{#
    Business question: when a customer does come back, how long do they wait
    between orders, and what does the typical (median) and long (p90) gap
    look like?

    Grain: one row per repeat order - every order after a customer's first,
    keyed by (customer_unique_id, order_id).

    Metric definitions:
      order_date          = calendar date of the order (minimum purchase
                            timestamp across its lines).
      previous_order_date = LAG() of order_date within the customer.
      gap_days            = order_date - previous_order_date, in calendar days.
      median_gap_days     = PERCENTILE_CONT(0.5) over all gap_days in the
                            model, repeated on every row.
      p90_gap_days        = PERCENTILE_CONT(0.9), same treatment.

    Average gap is deliberately not reported: a handful of very long gaps
    would pull it away from the typical customer experience.

    Limitations: calendar-day granularity hides same-day repeats (gap = 0).
    Olist's repeat-purchase rate is very low, so these percentiles rest on a
    small subset of customers and should be read as descriptive, not as a
    stable behavioural estimate.
#}

with customer_orders as (

    select
        customer_unique_id,
        order_id,
        min(order_purchase_timestamp)::date as order_date

    from {{ ref('fct_orders') }}
    group by customer_unique_id, order_id

),

with_previous as (

    select
        customer_unique_id,
        order_id,
        order_date,
        lag(order_date) over (
            partition by customer_unique_id
            order by order_date, order_id
        ) as previous_order_date

    from customer_orders

),

gaps as (

    select
        customer_unique_id,
        order_id,
        order_date,
        previous_order_date,
        (order_date - previous_order_date) as gap_days

    from with_previous
    where previous_order_date is not null

),

gap_stats as (

    select
        percentile_cont(0.5) within group (order by gap_days) as median_gap_days,
        percentile_cont(0.9) within group (order by gap_days) as p90_gap_days

    from gaps

)

select
    gaps.customer_unique_id,
    gaps.order_id,
    gaps.order_date,
    gaps.previous_order_date,
    gaps.gap_days,
    round(gap_stats.median_gap_days::numeric, 1) as median_gap_days,
    round(gap_stats.p90_gap_days::numeric, 1) as p90_gap_days

from gaps
cross join gap_stats
order by gaps.customer_unique_id, gaps.order_date, gaps.order_id
