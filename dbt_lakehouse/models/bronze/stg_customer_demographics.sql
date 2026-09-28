{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    cd_demo_sk AS cdemo_id,
    cd_gender AS gender,
    cd_marital_status AS marital_status,
    cd_education_status AS education_status,
    cd_credit_rating AS credit_rating,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'customer_demographics') }}
