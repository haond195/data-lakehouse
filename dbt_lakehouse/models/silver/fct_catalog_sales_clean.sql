{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    c.order_id,
    c.item_id,
    COALESCE(c.customer_id, 0) AS customer_id,
    COALESCE(c.call_center_id, 0) AS call_center_id,
    d.calendar_year AS sales_year,
    d.month_of_year AS sales_month,
    COALESCE(c.raw_quantity, 1) AS quantity,
    CAST(COALESCE(c.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
    CAST(COALESCE(c.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
    c._ingested_at,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_catalog_sales') }} c
INNER JOIN {{ ref('dim_date') }} d ON c.date_id = d.date_id
WHERE c.raw_net_paid IS NOT NULL AND c.raw_quantity > 0
