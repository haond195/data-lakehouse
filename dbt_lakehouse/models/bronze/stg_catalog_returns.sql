{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    cr_order_number AS return_order_id,
    cr_item_sk AS item_id,
    cr_refunded_customer_sk AS customer_id,
    cr_reason_sk AS reason_id,
    cr_returned_date_sk AS return_date_id,
    cr_return_quantity AS return_quantity,
    cr_return_amount AS return_amount,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'catalog_returns') }}
