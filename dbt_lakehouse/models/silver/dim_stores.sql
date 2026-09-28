{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    store_id,
    store_code,
    COALESCE(store_name, 'Online / Non-Store') AS store_name,
    COALESCE(number_employees, 0) AS number_employees,
    COALESCE(floor_space, 0) AS floor_space,
    COALESCE(city, 'Unknown City') AS city,
    COALESCE(state, 'Unknown State') AS state,
    COALESCE(country, 'United States') AS country,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_store') }}
