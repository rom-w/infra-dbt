/*
    Welcome to your first dbt model!
    Did you know that you can also configure models directly within SQL files?
    This will override configurations stated in dbt_project.yml

    Try changing "table" to "view" below
*/



with source_data as (

    select 1 as id,'alexey' as name, '1991-01-01' as date_id, 97 score
    union all
    select 1 as id,'alexey' as name, '1991-01-02' as date_id, 66 score
    union all
    select 2 as id,'sergey' as name, '1991-01-03' as date_id, 50 score

)

select *
from source_data

/*
    Uncomment the line below to remove records with null `id` values
*/

-- where id is not null