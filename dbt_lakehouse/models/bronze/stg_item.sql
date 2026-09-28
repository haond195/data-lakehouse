{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    i_item_sk AS item_id,
    i_item_id AS item_code,
    i_item_desc AS item_desc,
    i_current_price AS current_price,
    i_wholesale_cost AS wholesale_cost,
    i_brand AS brand,
    i_class AS class,
    i_category AS category,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'item') }}
