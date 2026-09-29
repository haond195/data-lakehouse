{{ config(
    materialized='table',
    schema='stg_gold' if target.name == 'stg' else 'retail_gold'
) }}

WITH sales_monthly AS (
    SELECT 
        item_id,
        sales_year,
        sales_month,
        SUM(quantity) AS monthly_sold_qty,
        SUM(net_revenue) AS monthly_revenue
    FROM {{ ref('fct_sales_clean') }}
    GROUP BY item_id, sales_year, sales_month
),
inventory_monthly AS (
    SELECT 
        item_id,
        inventory_year,
        inventory_month,
        SUM(quantity_on_hand) AS total_stock_on_hand,
        SUM(inventory_value) AS total_inventory_value,
        COUNT(DISTINCT warehouse_id) AS warehouse_count
    FROM {{ ref('fct_inventory_balance') }}
    GROUP BY item_id, inventory_year, inventory_month
)
SELECT 
    s.sales_year,
    s.sales_month,
    p.category,
    p.brand,
    SUM(s.monthly_sold_qty) AS total_sold_qty,
    SUM(i.total_stock_on_hand) AS total_stock_on_hand,
    ROUND(SUM(s.monthly_revenue), 2) AS monthly_revenue,
    ROUND(SUM(i.total_inventory_value), 2) AS total_inventory_value,
    ROUND(CAST(SUM(i.total_stock_on_hand) AS DOUBLE) / NULLIF(SUM(s.monthly_sold_qty), 0), 2) AS stock_to_sales_ratio,
    ROUND((CAST(SUM(i.total_stock_on_hand) AS DOUBLE) / NULLIF(SUM(s.monthly_sold_qty), 0)) * 30, 1) AS days_of_supply,
    CASE 
        WHEN (CAST(SUM(i.total_stock_on_hand) AS DOUBLE) / NULLIF(SUM(s.monthly_sold_qty), 0)) * 30 < 15 THEN 'CRITICAL_LOW_STOCK'
        WHEN (CAST(SUM(i.total_stock_on_hand) AS DOUBLE) / NULLIF(SUM(s.monthly_sold_qty), 0)) * 30 > 90 THEN 'OVERSTOCKED'
        ELSE 'HEALTHY'
    END AS inventory_health_status,
    CURRENT_TIMESTAMP AS _calculated_at
FROM sales_monthly s
INNER JOIN inventory_monthly i 
    ON s.item_id = i.item_id 
    AND s.sales_year = i.inventory_year 
    AND s.sales_month = i.inventory_month
INNER JOIN {{ ref('dim_products') }} p ON s.item_id = p.item_id
GROUP BY s.sales_year, s.sales_month, p.category, p.brand
