{#
    Business question: how is monthly revenue trending, how fast is it
    changing month over month, and what does the cumulative and short-term
    trend look like?

    Grain: one row per calendar month, inheriting fct_revenue_monthly.

    Metric definitions:
      total_revenue           = the official monthly revenue metric, summed
                                from fct_orders.revenue (price + freight).
      previous_month_revenue  = LAG(total_revenue) one calendar month back.
      mom_growth_rate         = (total_revenue - previous_month_revenue) /
                                previous_month_revenue. NULL when there is
                                no previous month or it was zero.
      running_total_revenue   = SUM() OVER, unbounded through the current month.
      trailing_3m_avg_revenue = AVG() over the current and two prior months.
                                Early months use the months available; it is
                                not annualised or extrapolated.

    Limitations: Olist's 2016 months contain very few orders, so early
    growth rates are unstable. A calendar-month comparison ignores the
    number of trading days in each month.
#}

with monthly as (

    select * from {{ ref('fct_revenue_monthly') }}

),

growth as (

    select
        month,
        total_revenue,
        total_orders,
        active_customers,
        lag(total_revenue) over (order by month) as previous_month_revenue,
        round(
            (total_revenue - lag(total_revenue) over (order by month))
            / nullif(lag(total_revenue) over (order by month), 0),
            4
        ) as mom_growth_rate,
        sum(total_revenue) over (
            order by month
            rows between unbounded preceding and current row
        ) as running_total_revenue,
        round(
            avg(total_revenue) over (
                order by month
                rows between 2 preceding and current row
            ),
            2
        ) as trailing_3m_avg_revenue

    from monthly

)

select * from growth
order by month
