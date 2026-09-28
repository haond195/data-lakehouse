{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    w.order_id,
    w.item_id,
    COALESCE(w.customer_id, 0) AS customer_id,
    COALESCE(w.web_site_id, 0) AS web_site_id,
    d.calendar_year AS sales_year,
    d.month_of_year AS sales_month,
    COALESCE(w.raw_quantity, 1) AS quantity,
    CAST(COALESCE(w.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
    CAST(COALESCE(w.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
    w._ingested_at,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_web_sales') }} w
INNER JOIN {{ ref('dim_date') }} d ON w.date_id = d.date_id
WHERE w.raw_net_paid IS NOT NULL AND w.raw_quantity > 0
