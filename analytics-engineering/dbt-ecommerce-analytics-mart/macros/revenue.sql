{% macro order_line_revenue(price_col='price', freight_col='freight_value') %}
    ({{ price_col }} + {{ freight_col }})
{% endmacro %}
