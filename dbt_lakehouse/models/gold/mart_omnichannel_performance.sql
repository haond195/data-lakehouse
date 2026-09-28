{{ config(
    materialized='table',
    schema='stg_gold' if target.name == 'stg' else 'retail_gold'
) }}

WITH store_summary AS (
    SELECT 
        'Store' AS channel,
        sales_year,
        sales_month,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(net_revenue), 2) AS total_revenue,
        ROUND(SUM(net_profit), 2) AS total_profit
    FROM {{ ref('fct_sales_clean') }}
    GROUP BY sales_year, sales_month
),
web_summary AS (
    SELECT 
        'Web' AS channel,
        sales_year,
        sales_month,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(net_revenue), 2) AS total_revenue,
        ROUND(SUM(net_profit), 2) AS total_profit
    FROM {{ ref('fct_web_sales_clean') }}
    GROUP BY sales_year, sales_month
),
catalog_summary AS (
    SELECT 
        'Catalog' AS channel,
        sales_year,
        sales_month,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(net_revenue), 2) AS total_revenue,
        ROUND(SUM(net_profit), 2) AS total_profit
    FROM {{ ref('fct_catalog_sales_clean') }}
    GROUP BY sales_year, sales_month
),
all_channels AS (
    SELECT * FROM store_summary
    UNION ALL
    SELECT * FROM web_summary
    UNION ALL
    SELECT * FROM catalog_summary
)
SELECT 
    channel,
    sales_year,
    sales_month,
    total_orders,
    total_units_sold,
    total_revenue,
    total_profit,
    ROUND(total_revenue / NULLIF(total_orders, 0), 2) AS average_order_value_aov,
    ROUND((total_profit / NULLIF(total_revenue, 0)) * 100, 2) AS profit_margin_pct,
    CURRENT_TIMESTAMP AS _calculated_at
FROM all_channels
