{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    warehouse_id,
    warehouse_code,
    COALESCE(warehouse_name, 'Unknown Warehouse') AS warehouse_name,
    COALESCE(warehouse_sq_ft, 0) AS warehouse_sq_ft,
    COALESCE(city, 'Unknown City') AS city,
    COALESCE(state, 'Unknown State') AS state,
    COALESCE(country, 'United States') AS country,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_warehouse') }}
