{{ config(
    materialized='table',
    schema='stg_gold' if target.name == 'stg' else 'retail_gold'
) }}

SELECT 
    s.sales_year,
    s.sales_month,
    p.category,
    p.brand,
    COUNT(DISTINCT s.order_id) AS total_orders,
    SUM(s.quantity) AS units_sold,
    ROUND(SUM(s.net_revenue), 2) AS total_revenue,
    ROUND(SUM(s.net_profit), 2) AS total_profit,
    ROUND((SUM(s.net_profit) / NULLIF(SUM(s.net_revenue), 0)) * 100, 2) AS profit_margin_pct,
    CURRENT_TIMESTAMP AS _calculated_at
FROM {{ ref('fct_sales_clean') }} s
INNER JOIN {{ ref('dim_products') }} p ON s.item_id = p.item_id
GROUP BY s.sales_year, s.sales_month, p.category, p.brand
