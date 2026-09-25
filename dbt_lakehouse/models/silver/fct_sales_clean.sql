{{ config(
    materialized='table',
    schema='retail_silver'
) }}

SELECT 
    r.order_id,
    r.item_id,
    COALESCE(r.customer_id, 0) AS customer_id,
    COALESCE(r.store_id, 0) AS store_id,
    d.d_year AS sales_year,
    d.d_moy AS sales_month,
    COALESCE(r.raw_quantity, 1) AS quantity,
    CAST(COALESCE(r.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
    CAST(COALESCE(r.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
    r._ingested_at,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_store_sales') }} r
INNER JOIN {{ source('tpcds_source', 'date_dim') }} d ON r.date_id = d.d_date_sk
WHERE r.raw_net_paid IS NOT NULL AND r.raw_quantity > 0
