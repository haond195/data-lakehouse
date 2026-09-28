{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    inv_date_sk AS date_id,
    inv_item_sk AS item_id,
    inv_warehouse_sk AS warehouse_id,
    inv_quantity_on_hand AS quantity_on_hand,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'inventory') }}
