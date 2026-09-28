{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    c_customer_sk AS customer_id,
    c_customer_id AS customer_code,
    c_first_name AS first_name,
    c_last_name AS last_name,
    c_current_addr_sk AS address_id,
    c_current_cdemo_sk AS cdemo_id,
    c_email_address AS email,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'customer') }}
