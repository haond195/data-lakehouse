"""
PIPELINE ETL MEDALLION: KHUYẾN MÃI (PROMOTION) & KHÁCH HÀNG 360 (CUSTOMER 360)
Nguồn: TPC-DS SF1 (promotion, customer, customer_address, customer_demographics) -> Iceberg S3
"""
import sys, time
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from trino.dbapi import connect

def get_connection():
    return connect(
        host="localhost",
        port=8080,
        user="etl_crm_promo",
        catalog="iceberg"
    )

def run_step(cur, step_num, title, sql):
    print(f"\n[{step_num}] {title}...")
    t0 = time.time()
    cur.execute(sql)
    dur = time.time() - t0
    print(f" -> Hoàn thành trong {dur:.2f}s")

def main():
    conn = get_connection()
    cur = conn.cursor()

    print("===================================================================")
    print(" BẮT ĐẦU PIPELINE ETL: KHUYẾN MÃI & KHÁCH HÀNG 360 (MEDALLION)    ")
    print("===================================================================")

    # 1. TẦNG BRONZE
    run_step(cur, "1/6", "Bronze: Nạp dữ liệu khuyến mãi thô (promotion_raw)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.promotion_raw AS
    SELECT 
        p_promo_sk AS promo_id,
        p_promo_id AS promo_code,
        p_promo_name AS promo_name,
        p_channel_dmail AS channel_dmail,
        p_channel_email AS channel_email,
        p_channel_tv AS channel_tv,
        p_cost AS promo_cost,
        p_discount_active AS discount_active,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.promotion
    """)

    run_step(cur, "2/6", "Bronze: Nạp dữ liệu khách hàng thô (customer_raw & demographics)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.customer_raw AS
    SELECT 
        c_customer_sk AS customer_sk,
        c_customer_id AS customer_code,
        c_current_cdemo_sk AS cdemo_sk,
        c_current_addr_sk AS addr_sk,
        c_first_name AS first_name,
        c_last_name AS last_name,
        c_email_address AS email,
        c_birth_country AS birth_country,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.customer
    """)

    run_step(cur, "3/6", "Bronze: Nạp địa chỉ và nhân khẩu học (address & demographics raw)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.customer_demographics_raw AS
    SELECT 
        cd_demo_sk AS demo_sk,
        cd_gender AS gender,
        cd_marital_status AS marital_status,
        cd_education_status AS education_status,
        cd_credit_rating AS credit_rating,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.customer_demographics
    """)

    # 2. TẦNG SILVER
    run_step(cur, "4/6", "Silver: Chuẩn hóa chiều khuyến mãi (dim_promotion)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.dim_promotion AS
    SELECT 
        promo_id,
        TRIM(promo_code) AS promo_code,
        COALESCE(TRIM(promo_name), 'Standard Promotion') AS promo_name,
        CASE WHEN channel_email = 'Y' THEN true ELSE false END AS has_email_campaign,
        CASE WHEN channel_tv = 'Y' THEN true ELSE false END AS has_tv_campaign,
        CAST(COALESCE(promo_cost, 0.0) AS DOUBLE) AS promo_cost,
        CASE WHEN discount_active = 'Y' THEN true ELSE false END AS is_active,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.promotion_raw
    """)

    run_step(cur, "5/6", "Silver: Hợp nhất hồ sơ khách hàng 360 độ (dim_customer_360)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.dim_customer_360 AS
    SELECT 
        c.customer_sk AS customer_id,
        TRIM(c.customer_code) AS customer_code,
        CONCAT(COALESCE(TRIM(c.first_name), ''), ' ', COALESCE(TRIM(c.last_name), '')) AS full_name,
        COALESCE(TRIM(c.email), 'no-email@customer.org') AS email,
        COALESCE(TRIM(c.birth_country), 'Unknown') AS country,
        COALESCE(d.gender, 'U') AS gender,
        COALESCE(TRIM(d.marital_status), 'U') AS marital_status,
        COALESCE(TRIM(d.education_status), 'Unknown') AS education_status,
        COALESCE(TRIM(d.credit_rating), 'Standard') AS credit_rating,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.customer_raw c
    LEFT JOIN iceberg.retail_bronze.customer_demographics_raw d ON c.cdemo_sk = d.demo_sk
    """)

    # 3. TẦNG GOLD
    run_step(cur, "6/6", "Gold: Phân tích hiệu quả khuyến mãi & Phân khúc khách hàng 360", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_gold.mart_customer_segmentation AS
    SELECT 
        c.country,
        c.gender,
        c.education_status,
        c.credit_rating,
        COUNT(DISTINCT c.customer_id) AS total_customers,
        CURRENT_TIMESTAMP AS _calculated_at
    FROM iceberg.retail_silver.dim_customer_360 c
    GROUP BY c.country, c.gender, c.education_status, c.credit_rating
    """)

    # THỐNG KÊ KẾT QUẢ
    print("\n" + "=" * 65)
    print(" TỔNG HỢP CÁC BẢNG KHUYẾN MÃI & KHÁCH HÀNG 360 TRONG MEDALLION:")
    print("=" * 65)
    tables = [
        ("Bronze", "iceberg.retail_bronze.promotion_raw"),
        ("Bronze", "iceberg.retail_bronze.customer_raw"),
        ("Bronze", "iceberg.retail_bronze.customer_demographics_raw"),
        ("Silver", "iceberg.retail_silver.dim_promotion"),
        ("Silver", "iceberg.retail_silver.dim_customer_360"),
        ("Gold  ", "iceberg.retail_gold.mart_customer_segmentation")
    ]
    for tier, tbl in tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f" * [{tier:<6}] {tbl:<52} : {cnt:>9,} dòng")
    print("=" * 65)
    print(" Pipeline Khuyến mãi & Khách hàng 360 hoàn tất 100%!")

if __name__ == "__main__":
    main()
