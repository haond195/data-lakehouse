{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    ca_address_sk AS address_id,
    ca_street_name AS street_name,
    ca_city AS city,
    ca_state AS state,
    ca_zip AS zip_code,
    ca_country AS country,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'customer_address') }}
LIMIT 20000
