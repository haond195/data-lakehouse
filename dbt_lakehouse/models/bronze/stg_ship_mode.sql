{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    sm_ship_mode_sk AS ship_mode_id,
    sm_ship_mode_id AS ship_mode_code,
    sm_type AS ship_type,
    sm_carrier AS carrier,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'ship_mode') }}
