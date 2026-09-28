{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    s_store_sk AS store_id,
    s_store_id AS store_code,
    s_store_name AS store_name,
    s_number_employees AS number_employees,
    s_floor_space AS floor_space,
    s_city AS city,
    s_state AS state,
    s_country AS country,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'store') }}
