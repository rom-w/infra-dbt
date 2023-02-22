select *,

    now() + ((interval '1 ') * (1))


from -- depends on: "test_dbt"."public"."dbt_metrics_default_calendar"

(

with calendar as (
    select 
        * 
    from "test_dbt"."public"."dbt_metrics_default_calendar"
     
)

, model_51758de9e889a72967b82e35fea7902f__aggregate as (
    
    select
        date_week,
        name,
        bool_or(metric_date_day is not null) as has_data,
        sum(property_to_aggregate__rolling_new_customers) as rolling_new_customers,
        max(property_to_aggregate__test_update) as test_update
    from (
        select 
            cast(base_model.date_id as date) as metric_date_day,
            calendar.date_week as date_week,
            calendar.date_day as window_filter_date,
            base_model.name,
            (score) as property_to_aggregate__rolling_new_customers,
            (score) as property_to_aggregate__test_update
        from "test_dbt"."public"."my_first_dbt_model" base_model 
        
        left join calendar
            on cast(base_model.date_id as date) = calendar.date_day
        
        where 1=1
        
    ) as base_query

    where 1=1
    group by 1, 2

), model_51758de9e889a72967b82e35fea7902f__final as (
    
    select
        parent_metric_cte.date_week,
        parent_metric_cte.name,
        coalesce(rolling_new_customers, 0) as rolling_new_customers,
        coalesce(test_update, 0) as test_update
    from model_51758de9e889a72967b82e35fea7902f__aggregate as parent_metric_cte
)

select
    date_week ,
    name,
    rolling_new_customers,
    test_update  
    
from model_51758de9e889a72967b82e35fea7902f__final
    
order by 1 desc
    
) metric_subq