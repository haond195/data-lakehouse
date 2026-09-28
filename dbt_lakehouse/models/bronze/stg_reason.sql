{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    r_reason_sk AS reason_id,
    r_reason_id AS reason_code,
    r_reason_desc AS reason_desc,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'reason') }}
