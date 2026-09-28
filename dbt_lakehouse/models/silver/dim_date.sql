{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    date_id,
    date_code,
    calendar_date,
    calendar_year,
    month_of_year,
    quarter_of_year,
    day_name,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_date_dim') }}
