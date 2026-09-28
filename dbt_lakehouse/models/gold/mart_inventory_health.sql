{{ config(
    materialized='table',
    schema='stg_gold' if target.name == 'stg' else 'retail_gold'
) }}

SELECT 
    warehouse_name,
    warehouse_city,
    warehouse_state,
    category,
    COUNT(DISTINCT item_id) AS total_distinct_items,
    SUM(quantity_on_hand) AS total_units_in_stock,
    ROUND(SUM(inventory_value), 2) AS total_inventory_value,
    CURRENT_TIMESTAMP AS _calculated_at
FROM {{ ref('fct_inventory_balance') }}
WHERE warehouse_name IS NOT NULL
GROUP BY warehouse_name, warehouse_city, warehouse_state, category
