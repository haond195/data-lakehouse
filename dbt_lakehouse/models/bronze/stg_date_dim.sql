{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    d_date_sk AS date_id,
    d_date_id AS date_code,
    d_date AS calendar_date,
    d_month_seq AS month_seq,
    d_year AS calendar_year,
    d_moy AS month_of_year,
    d_qoy AS quarter_of_year,
    d_day_name AS day_name,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'date_dim') }}
