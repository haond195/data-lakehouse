{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    sr_ticket_number AS return_order_id,
    sr_item_sk AS item_id,
    sr_customer_sk AS customer_id,
    sr_store_sk AS store_id,
    sr_reason_sk AS reason_id,
    sr_returned_date_sk AS return_date_id,
    sr_return_quantity AS return_quantity,
    sr_return_amt AS return_amount,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'store_returns') }}
