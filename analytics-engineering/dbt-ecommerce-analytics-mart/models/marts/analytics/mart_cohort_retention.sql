{#
    Business question: once a customer makes their first purchase, how often
    do they come back in later months, and how does that vary by acquisition
    cohort?

    Grain: one row per (first-purchase month cohort, months since first
    purchase).

    Metric definitions:
      cohort_month      = calendar month of the customer's first order
                          (DATE_TRUNC).
      month_index       = whole calendar months between the activity month
                          and cohort_month; 0 is the acquisition month.
      cohort_size       = distinct customers whose first order was in that
                          cohort month. Repeated on every row for that cohort.
      active_customers  = distinct cohort customers with at least one order
                          in that activity month. An order line counts once
                          per customer per month, regardless of status.
      retention_rate    = active_customers / cohort_size, rounded to 4 dp.

    Limitations: Olist's repeat-purchase rate is low, so most later cells are
    small and noisy; a monthly cohort view cannot separate seasonality from
    retention. Month 0 is 100% by construction (the first order defines the
    cohort), not evidence of retention.
#}

with orders as (

    select distinct
        customer_unique_id,
        order_id,
        date_trunc('month', order_purchase_timestamp)::date as activity_month

    from {{ ref('fct_orders') }}

),

first_orders as (

    select
        customer_unique_id,
        min(activity_month) as cohort_month

    from orders
    group by customer_unique_id

),

activity as (

    select
        orders.customer_unique_id,
        first_orders.cohort_month,
        orders.activity_month,
        (
            (extract(year from orders.activity_month) * 12
                + extract(month from orders.activity_month))
            - (extract(year from first_orders.cohort_month) * 12
                + extract(month from first_orders.cohort_month))
        )::int as month_index

    from orders
    inner join first_orders
        on orders.customer_unique_id = first_orders.customer_unique_id

),

cohort_sizes as (

    select
        cohort_month,
        count(distinct customer_unique_id) as cohort_size

    from first_orders
    group by cohort_month

),

cohort_activity as (

    select
        cohort_month,
        month_index,
        count(distinct customer_unique_id) as active_customers

    from activity
    group by cohort_month, month_index

)

select
    cohort_activity.cohort_month,
    cohort_activity.month_index,
    cohort_sizes.cohort_size,
    cohort_activity.active_customers,
    round(
        cohort_activity.active_customers::numeric
        / nullif(cohort_sizes.cohort_size, 0),
        4
    ) as retention_rate

from cohort_activity
inner join cohort_sizes
    on cohort_activity.cohort_month = cohort_sizes.cohort_month
order by cohort_activity.cohort_month, cohort_activity.month_index
