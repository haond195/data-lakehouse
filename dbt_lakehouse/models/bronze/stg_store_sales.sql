{{ config(
    materialized='table',
    schema='retail_bronze'
) }}

SELECT 
    ss_ticket_number AS order_id,
    ss_item_sk AS item_id,
    ss_customer_sk AS customer_id,
    ss_store_sk AS store_id,
    ss_sold_date_sk AS date_id,
    ss_quantity AS raw_quantity,
    ss_net_paid AS raw_net_paid,
    ss_net_profit AS raw_net_profit,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'store_sales') }}
LIMIT 10000
