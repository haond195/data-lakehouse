{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    item_id,
    item_code,
    COALESCE(item_desc, 'Unknown Product') AS product_name,
    COALESCE(brand, 'Unknown Brand') AS brand,
    COALESCE(class, 'Unknown Class') AS class,
    COALESCE(category, 'General') AS category,
    CAST(COALESCE(current_price, 0.0) AS DOUBLE) AS unit_price,
    CAST(COALESCE(wholesale_cost, 0.0) AS DOUBLE) AS wholesale_cost,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_item') }}
