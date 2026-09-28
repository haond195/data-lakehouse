{{ config(
    materialized='table',
    schema='stg_gold' if target.name == 'stg' else 'retail_gold'
) }}

SELECT 
    c.state,
    c.gender,
    c.education_status,
    c.credit_rating,
    COUNT(DISTINCT c.customer_id) AS total_customers,
    COUNT(DISTINCT s.order_id) AS total_orders,
    ROUND(COALESCE(SUM(s.net_revenue), 0.0), 2) AS total_spend,
    CURRENT_TIMESTAMP AS _calculated_at
FROM {{ ref('dim_customers') }} c
LEFT JOIN {{ ref('fct_sales_clean') }} s ON c.customer_id = s.customer_id
GROUP BY c.state, c.gender, c.education_status, c.credit_rating
