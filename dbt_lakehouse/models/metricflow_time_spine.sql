{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    CAST(calendar_date AS DATE) AS date_day
FROM {{ ref('dim_date') }}
WHERE calendar_date IS NOT NULL
