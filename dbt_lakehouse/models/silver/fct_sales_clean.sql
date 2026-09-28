{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    r.order_id,
    r.item_id,
    COALESCE(r.customer_id, 0) AS customer_id,
    COALESCE(r.store_id, 0) AS store_id,
    COALESCE(s.store_name, 'Online / Non-Store') AS store_name,
    COALESCE(s.state, 'Unknown State') AS store_state,
    d.calendar_year AS sales_year,
    d.month_of_year AS sales_month,
    COALESCE(r.raw_quantity, 1) AS quantity,
    CAST(COALESCE(r.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
    CAST(COALESCE(r.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
    r._ingested_at,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_store_sales') }} r
INNER JOIN {{ ref('dim_date') }} d ON r.date_id = d.date_id
LEFT JOIN {{ ref('dim_stores') }} s ON r.store_id = s.store_id
WHERE r.raw_net_paid IS NOT NULL AND r.raw_quantity > 0
