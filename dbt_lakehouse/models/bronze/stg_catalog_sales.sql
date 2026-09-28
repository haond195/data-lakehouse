{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    cs_order_number AS order_id,
    cs_item_sk AS item_id,
    cs_bill_customer_sk AS customer_id,
    cs_call_center_sk AS call_center_id,
    cs_sold_date_sk AS date_id,
    cs_quantity AS raw_quantity,
    cs_net_paid AS raw_net_paid,
    cs_net_profit AS raw_net_profit,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'catalog_sales') }}
LIMIT 50000
