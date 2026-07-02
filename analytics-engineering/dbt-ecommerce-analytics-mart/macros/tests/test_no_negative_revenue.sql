{% test no_negative_revenue(model, column_name) %}

select *
from {{ model }}
where {{ column_name }} < 0

{% endtest %}
