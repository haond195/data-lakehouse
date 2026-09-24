"""
QUY TRÌNH ETL CHUẨN TRÊN LAKEHOUSE (MEDALLION ARCHITECTURE)
Bronze (Raw) -> Silver (Cleaned) -> Gold (Aggregated Business Marts)
"""
import os, time
from trino.dbapi import connect

def get_connection():
    return connect(
        host="localhost",
        port=8080,
        user="etl_engineer",
        catalog="iceberg"
    )

def run_step(cursor, title, sql):
    print(f"\n[BƯỚC] {title}...")
    t0 = time.time()
    cursor.execute(sql)
    dur = time.time() - t0
    print(f" -> Hoàn thành trong {dur:.2f}s")

def main():
    conn = get_connection()
    cur = conn.cursor()

    print("=========================================================")
    print(" BẮT ĐẦU CHẠY QUY TRÌNH ETL (BRONZE -> SILVER -> GOLD)  ")
    print("=========================================================")

    # 1. KHỞI TẠO CÁC SCHEMA (TẦNG LƯU TRỮ)
    run_step(cur, "Tạo Schema Bronze (Dữ liệu thô)", 
             "CREATE SCHEMA IF NOT EXISTS iceberg.retail_bronze")
    
    run_step(cur, "Tạo Schema Silver (Dữ liệu làm sạch)", 
             "CREATE SCHEMA IF NOT EXISTS iceberg.retail_silver")

    # 2. BƯỚC 1: EXTRACT & LOAD TO BRONZE (TẦNG DỮ LIỆU THÔ)
    run_step(cur, "Nạp dữ liệu vào Bronze: retail_bronze.raw_transactions", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.raw_transactions AS
    SELECT 
        ss_ticket_number AS raw_order_id,
        ss_item_sk AS raw_item_id,
        ss_customer_sk AS raw_customer_id,
        ss_store_sk AS raw_store_id,
        ss_quantity AS raw_quantity,
        ss_list_price AS raw_unit_price,
        ss_net_paid AS raw_amount_paid,
        ss_net_profit AS raw_profit,
        ss_sold_date_sk AS raw_date_id,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM iceberg.retail_gold.store_sales
    LIMIT 20000
    """)

    # 3. BƯỚC 2: TRANSFORM & LOAD TO SILVER (TẦNG DỮ LIỆU SẠCH)
    run_step(cur, "Làm sạch và nạp vào Silver: retail_silver.clean_transactions", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.clean_transactions AS
    SELECT 
        raw_order_id AS order_id,
        raw_item_id AS item_id,
        COALESCE(raw_customer_id, 0) AS customer_id,
        COALESCE(raw_store_id, 0) AS store_id,
        COALESCE(raw_quantity, 1) AS quantity,
        CAST(COALESCE(raw_amount_paid, 0.0) AS DOUBLE) AS net_revenue,
        CAST(COALESCE(raw_profit, 0.0) AS DOUBLE) AS net_profit,
        _ingested_at,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.raw_transactions
    WHERE raw_amount_paid IS NOT NULL AND raw_quantity > 0
    """)

    # 4. BƯỚC 3: AGGREGATE & LOAD TO GOLD (TẦNG PHÂN TÍCH & BI)
    run_step(cur, "Tổng hợp chỉ số KPI vào Gold: retail_gold.store_performance_daily", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_gold.store_performance_daily AS
    SELECT 
        t.store_id,
        COALESCE(s.s_store_name, 'Online / Unknown') AS store_name,
        COALESCE(s.s_state, 'Unknown') AS store_state,
        COUNT(DISTINCT t.order_id) AS total_orders,
        SUM(t.quantity) AS total_units_sold,
        ROUND(SUM(t.net_revenue), 2) AS total_net_revenue,
        ROUND(SUM(t.net_profit), 2) AS total_net_profit,
        CURRENT_TIMESTAMP AS _calculated_at
    FROM iceberg.retail_silver.clean_transactions t
    LEFT JOIN iceberg.retail_gold.store s ON t.store_id = s.s_store_sk
    GROUP BY t.store_id, s.s_store_name, s.s_state
    """)

    # 5. XÁC THỰC KẾT QUẢ ETL
    print("\n=========================================================")
    print(" KIỂM TRA SỐ DÒNG SAU KHI CHẠY ETL:")
    print("=========================================================")
    for tbl in [
        "iceberg.retail_bronze.raw_transactions",
        "iceberg.retail_silver.clean_transactions",
        "iceberg.retail_gold.store_performance_daily"
    ]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        count = cur.fetchone()[0]
        print(f" * {tbl}: {count:,} dòng")

    print("\n[THÀNH CÔNG] Toàn bộ quy trình ETL Medallion đã hoàn tất 100%!")

if __name__ == "__main__":
    main()
