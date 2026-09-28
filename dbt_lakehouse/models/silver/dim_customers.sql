{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    c.customer_id,
    c.customer_code,
    COALESCE(c.first_name, '') AS first_name,
    COALESCE(c.last_name, '') AS last_name,
    TRIM(CONCAT(COALESCE(c.first_name, ''), ' ', COALESCE(c.last_name, ''))) AS full_name,
    COALESCE(a.city, 'Unknown City') AS city,
    COALESCE(a.state, 'Unknown State') AS state,
    COALESCE(a.country, 'Unknown Country') AS country,
    COALESCE(d.gender, 'U') AS gender,
    COALESCE(d.education_status, 'Unknown') AS education_status,
    COALESCE(d.credit_rating, 'Unknown') AS credit_rating,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_customer') }} c
LEFT JOIN {{ ref('stg_customer_address') }} a ON c.address_id = a.address_id
LEFT JOIN {{ ref('stg_customer_demographics') }} d ON c.cdemo_id = d.cdemo_id
