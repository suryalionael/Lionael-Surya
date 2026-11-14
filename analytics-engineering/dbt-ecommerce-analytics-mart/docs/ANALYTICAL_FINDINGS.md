# Analytical findings

All numbers below were produced by running the models against the real Olist
extract loaded in Postgres (`dbt build`, then SQL queries against
`dbt_marts`). Nothing here is estimated or hand-typed from a mock dataset.
The dataset covers orders placed from 2016-09 through 2018-09 and contains
95,420 unique customers, 98,666 orders, and R$15,843,553.24 of revenue
(price + freight).

**Read the last month with care.** September 2018 contains only R$166.46 of
revenue across the extract, so the -99.98% month-over-month change in
`mart_revenue_growth` is a partial-month artefact, not a collapse in demand.
Revenue through August 2018 is R$15,843,386.78.

## 1. Repeat purchasing is rare

Only 2,913 of 95,420 customers (3.1%) place more than one order. Frequency is
therefore the hard constraint on this business, not average order value.
Source: `mart_customer_rfm`, `mart_order_gaps`.

## 2. The biggest revenue segment is also the one most likely to leave

RFM segmentation puts 22,767 customers (23.9%) in **At Risk** and 27,857
(29.2%) in **Loyal**. At Risk customers still account for R$3,833,766.10
(24.2%) of revenue - slightly more than Loyal's R$3,737,219.29 (23.6%).
**Champions** are only 6,628 customers (6.9%) but contribute 13.2% of revenue.
Source: `models/marts/analytics/mart_customer_rfm.sql`.

## 3. Month-1 retention is under half a percent

Weighted by cohort size, 0.46% of customers return in month 1, 0.34% in month
2, and 0.23% by month 6. Month 0 is 100% by construction and is not evidence
of retention. These rates are consistent with the 3.1% repeat-purchase rate
above. Source: `models/marts/analytics/mart_cohort_retention.sql`.

## 4. Repeat customers wait about a month, but the tail is long

Across 3,246 repeat orders from 2,913 customers, the median gap between
consecutive orders is 29 days and the p90 is 242 days. The longest observed
gap is 609 days. The mean is deliberately not reported because the long tail
would distort it. Source: `models/marts/analytics/mart_order_gaps.sql`.

## 5. Revenue is Pareto-shaped across products

9,252 products (28.1% of products with sales) generate 80.0% of revenue (class
A). The next 11,759 products (35.7%) add 15.0% (class B), and the remaining
11,940 (36.2%) contribute 5.0% (class C). Assortment attention is justified for
the A tier; the C tier is a long tail. Source:
`models/marts/analytics/mart_product_pareto.sql`.

## 6. Health and beauty is the largest category

`health_beauty` leads with R$1,441,248.07 across 8,836 orders, ahead of
`watches_gifts` (R$1,305,541.61) and `bed_bath_table` (R$1,241,681.72). The
top health-and-beauty product alone generated R$67,606.10 from 195 units.
Source: `models/marts/analytics/mart_product_rank_by_category.sql`.

## 7. November 2017 was the strongest month, not Black Friday 2018

November 2017 produced R$1,179,143.77, up 53.3% on October 2017. The next
largest months are April 2018 (R$1,159,698.04) and March 2018
(R$1,155,126.82). The 2018-09 figure is incomplete (R$166.46). Source:
`models/marts/analytics/mart_revenue_growth.sql`.

## 8. Top-3 products per category show uneven unit economics

The highest-revenue product in `health_beauty` earned R$67,606.10 from 195
units, while the leader in `computers` earned R$50,326.18 from just 35 units.
Ranking on revenue alone therefore mixes high-volume and high-price products;
margin data is not in this extract, so the model does not claim which is more
profitable. Source:
`models/marts/analytics/mart_product_rank_by_category.sql`.

## Limitations

- Olist is a static 2016-2018 extract. Recency is anchored to the last order
  in the data, not today.
- Revenue is `price + freight_value`; it is not profit or margin.
- The final month (2018-09) is partial, so its growth rate is not comparable.
- NTILE buckets force equal-sized RFM groups even when the underlying
  distribution is skewed (especially frequency).
- Repeat-purchase cohorts rest on a small number of returning customers, so
  later retention cells are noisy even when the denominator is large.
- Segment and ABC thresholds are conventional business rules, not optimised
  cut-offs fitted to outcomes.
