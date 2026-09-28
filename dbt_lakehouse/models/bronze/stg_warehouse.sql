{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    w_warehouse_sk AS warehouse_id,
    w_warehouse_id AS warehouse_code,
    w_warehouse_name AS warehouse_name,
    w_warehouse_sq_ft AS warehouse_sq_ft,
    w_city AS city,
    w_state AS state,
    w_country AS country,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'warehouse') }}
