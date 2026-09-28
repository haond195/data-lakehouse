{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    wr_order_number AS return_order_id,
    wr_item_sk AS item_id,
    wr_refunded_customer_sk AS customer_id,
    wr_reason_sk AS reason_id,
    wr_returned_date_sk AS return_date_id,
    wr_return_quantity AS return_quantity,
    wr_return_amt AS return_amount,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'web_returns') }}
