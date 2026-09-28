{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    ws_order_number AS order_id,
    ws_item_sk AS item_id,
    ws_bill_customer_sk AS customer_id,
    ws_web_site_sk AS web_site_id,
    ws_sold_date_sk AS date_id,
    ws_quantity AS raw_quantity,
    ws_net_paid AS raw_net_paid,
    ws_net_profit AS raw_net_profit,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'web_sales') }}
