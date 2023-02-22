select *,{{ dbt.dateadd(month, 1, dbt.current_timestamp()) }}
from {{ metrics.calculate(
        [metric('rolling_new_customers'), metric('test_update')],
        grain='week',
        dimensions=['name']
    ) }}