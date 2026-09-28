{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

WITH store_ret AS (
    SELECT 
        'Store' AS return_channel,
        sr.return_order_id,
        sr.item_id,
        sr.customer_id,
        sr.return_date_id,
        COALESCE(r.reason_desc, 'Not Specified') AS reason_desc,
        sr.return_quantity,
        CAST(COALESCE(sr.return_amount, 0.0) AS DOUBLE) AS return_amount
    FROM {{ ref('stg_store_returns') }} sr
    LEFT JOIN {{ ref('stg_reason') }} r ON sr.reason_id = r.reason_id
),
web_ret AS (
    SELECT 
        'Web' AS return_channel,
        wr.return_order_id,
        wr.item_id,
        wr.customer_id,
        wr.return_date_id,
        COALESCE(r.reason_desc, 'Not Specified') AS reason_desc,
        wr.return_quantity,
        CAST(COALESCE(wr.return_amount, 0.0) AS DOUBLE) AS return_amount
    FROM {{ ref('stg_web_returns') }} wr
    LEFT JOIN {{ ref('stg_reason') }} r ON wr.reason_id = r.reason_id
),
cat_ret AS (
    SELECT 
        'Catalog' AS return_channel,
        cr.return_order_id,
        cr.item_id,
        cr.customer_id,
        cr.return_date_id,
        COALESCE(r.reason_desc, 'Not Specified') AS reason_desc,
        cr.return_quantity,
        CAST(COALESCE(cr.return_amount, 0.0) AS DOUBLE) AS return_amount
    FROM {{ ref('stg_catalog_returns') }} cr
    LEFT JOIN {{ ref('stg_reason') }} r ON cr.reason_id = r.reason_id
),
unified AS (
    SELECT * FROM store_ret
    UNION ALL
    SELECT * FROM web_ret
    UNION ALL
    SELECT * FROM cat_ret
)
SELECT 
    u.*,
    CURRENT_TIMESTAMP AS _transformed_at
FROM unified u
