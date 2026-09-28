{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    p_promo_sk AS promo_id,
    p_promo_id AS promo_code,
    p_promo_name AS promo_name,
    p_cost AS cost,
    p_channel_dmail AS channel_dmail,
    p_channel_email AS channel_email,
    p_channel_tv AS channel_tv,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'promotion') }}
