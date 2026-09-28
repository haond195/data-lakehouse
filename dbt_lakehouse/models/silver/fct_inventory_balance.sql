{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    inv.date_id,
    d.calendar_date AS inventory_date,
    d.calendar_year AS inventory_year,
    d.month_of_year AS inventory_month,
    inv.item_id,
    inv.warehouse_id,
    w.warehouse_name,
    w.city AS warehouse_city,
    w.state AS warehouse_state,
    p.product_name,
    p.category,
    p.brand,
    p.unit_price,
    inv.quantity_on_hand,
    ROUND(inv.quantity_on_hand * p.unit_price, 2) AS inventory_value,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_inventory') }} inv
INNER JOIN {{ ref('dim_date') }} d ON inv.date_id = d.date_id
LEFT JOIN {{ ref('dim_warehouses') }} w ON inv.warehouse_id = w.warehouse_id
LEFT JOIN {{ ref('dim_products') }} p ON inv.item_id = p.item_id
