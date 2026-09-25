{{ config(
    materialized='table',
    schema='retail_gold'
) }}

SELECT 
    sales_year,
    sales_month,
    store_id,
    COUNT(DISTINCT order_id) AS total_orders,
    SUM(quantity) AS total_units_sold,
    ROUND(SUM(net_revenue), 2) AS total_revenue,
    ROUND(SUM(net_profit), 2) AS total_profit,
    ROUND(SUM(net_revenue) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS average_order_value_aov,
    ROUND((SUM(net_profit) / NULLIF(SUM(net_revenue), 0)) * 100, 2) AS profit_margin_pct,
    CURRENT_TIMESTAMP AS _calculated_at
FROM {{ ref('fct_sales_clean') }}
GROUP BY sales_year, sales_month, store_id
