{{ config(
    materialized='table',
    schema='stg_gold' if target.name == 'stg' else 'retail_gold'
) }}

WITH sales_monthly AS (
    SELECT 
        s.item_id,
        s.sales_year,
        s.sales_month,
        COUNT(DISTINCT s.order_id) AS total_sales_orders,
        SUM(s.quantity) AS gross_sales_qty,
        SUM(s.net_revenue) AS gross_revenue,
        SUM(s.net_profit) AS gross_profit
    FROM {{ ref('fct_sales_clean') }} s
    GROUP BY s.item_id, s.sales_year, s.sales_month
),
returns_monthly AS (
    SELECT 
        r.item_id,
        d.calendar_year AS return_year,
        d.month_of_year AS return_month,
        COUNT(DISTINCT r.return_order_id) AS total_return_orders,
        SUM(r.return_quantity) AS returned_qty,
        SUM(r.return_amount) AS refund_amount
    FROM {{ ref('fct_returns_unified') }} r
    INNER JOIN {{ ref('dim_date') }} d ON r.return_date_id = d.date_id
    GROUP BY r.item_id, d.calendar_year, d.month_of_year
)
SELECT 
    s.sales_year,
    s.sales_month,
    p.category,
    p.brand,
    SUM(s.total_sales_orders) AS total_orders,
    SUM(s.gross_sales_qty) AS total_sold_qty,
    SUM(COALESCE(r.returned_qty, 0)) AS total_returned_qty,
    ROUND(CAST(SUM(COALESCE(r.returned_qty, 0)) AS DOUBLE) / NULLIF(SUM(s.gross_sales_qty), 0) * 100, 2) AS return_rate_pct,
    ROUND(SUM(s.gross_revenue), 2) AS gross_revenue,
    ROUND(SUM(COALESCE(r.refund_amount, 0)), 2) AS refund_amount,
    ROUND(SUM(s.gross_revenue) - SUM(COALESCE(r.refund_amount, 0)), 2) AS net_revenue,
    ROUND((SUM(COALESCE(r.refund_amount, 0)) / NULLIF(SUM(s.gross_revenue), 0)) * 100, 2) AS return_loss_pct,
    CURRENT_TIMESTAMP AS _calculated_at
FROM sales_monthly s
INNER JOIN {{ ref('dim_products') }} p ON s.item_id = p.item_id
LEFT JOIN returns_monthly r 
    ON s.item_id = r.item_id 
    AND s.sales_year = r.return_year 
    AND s.sales_month = r.return_month
GROUP BY s.sales_year, s.sales_month, p.category, p.brand
