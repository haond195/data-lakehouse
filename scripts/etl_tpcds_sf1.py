"""
QUY TRÌNH ETL HOÀN CHỈNH BỘ DỮ LIỆU TPC-DS SF1 VÀO APACHE ICEBERG LAKEHOUSE
Mô hình kiến trúc: Medallion Architecture (Bronze -> Silver -> Gold)
"""
import time
from trino.dbapi import connect

def get_connection():
    return connect(
        host="localhost",
        port=8080,
        user="etl_pipeline",
        catalog="iceberg"
    )

def execute_step(cur, step_num, step_name, sql, description):
    print(f"\n[{step_num}/4] {step_name.upper()}...")
    print(f" -> Mục đích: {description}")
    t0 = time.time()
    cur.execute(sql)
    dur = time.time() - t0
    print(f" -> Hoàn thành sau: {dur:.2f}s")

def main():
    conn = get_connection()
    cur = conn.cursor()

    print("===================================================================")
    print(" BẮT ĐẦU CHẠY PIPELINE ETL: TPCDS.SF1 -> LAKEHOUSE (ICEBERG/S3)")
    print("===================================================================")

    # 1. KHỞI TẠO CÁC SCHEMA (NẾU CHƯA CÓ)
    cur.execute("CREATE SCHEMA IF NOT EXISTS iceberg.retail_bronze")
    cur.execute("CREATE SCHEMA IF NOT EXISTS iceberg.retail_silver")
    cur.execute("CREATE SCHEMA IF NOT EXISTS iceberg.retail_gold")

    # BƯỚC 1: EXTRACT NGUỒN TPC-DS & NẠP VÀO BRONZE (RAW)
    # Lưu ý: Lấy mẫu 100,000 dòng từ 2.88 triệu dòng để chạy demo nhanh trong vài giây
    sql_bronze = """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.store_sales_raw AS
    SELECT 
        ss_ticket_number AS order_id,
        ss_item_sk AS item_id,
        ss_customer_sk AS customer_id,
        ss_store_sk AS store_id,
        ss_sold_date_sk AS date_id,
        ss_quantity AS raw_quantity,
        ss_list_price AS raw_unit_price,
        ss_net_paid AS raw_net_paid,
        ss_net_profit AS raw_net_profit,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.store_sales
    LIMIT 100000
    """
    execute_step(cur, 1, "Tầng Bronze (Raw Data Ingestion)", sql_bronze,
                 "Nạp dữ liệu nguyên bản từ tpcds.sf1 vào Iceberg S3, gắn mốc thời gian _ingested_at")

    # BƯỚC 2: TRANSFORM & LÀM SẠCH VÀO SILVER (CLEANED)
    sql_silver = """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.sales_transactions AS
    SELECT 
        r.order_id,
        r.item_id,
        COALESCE(i.i_item_desc, 'Unknown Product') AS product_name,
        COALESCE(i.i_category, 'Uncategorized') AS category,
        COALESCE(i.i_brand, 'No Brand') AS brand,
        COALESCE(r.customer_id, 0) AS customer_id,
        COALESCE(r.store_id, 0) AS store_id,
        COALESCE(s.s_store_name, 'Online / Non-Store') AS store_name,
        COALESCE(s.s_state, 'Unknown State') AS store_state,
        d.d_year AS sales_year,
        d.d_moy AS sales_month,
        d.d_date AS sales_date,
        COALESCE(r.raw_quantity, 1) AS quantity,
        CAST(COALESCE(r.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
        CAST(COALESCE(r.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
        r._ingested_at,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.store_sales_raw r
    INNER JOIN tpcds.sf1.date_dim d ON r.date_id = d.d_date_sk
    LEFT JOIN tpcds.sf1.item i ON r.item_id = i.i_item_sk
    LEFT JOIN tpcds.sf1.store s ON r.store_id = s.s_store_sk
    WHERE r.raw_net_paid IS NOT NULL AND r.raw_quantity > 0
    """
    execute_step(cur, 2, "Tầng Silver (Data Transformation & Cleaning)", sql_silver,
                 "Loại bỏ dữ liệu rác, xử lý NULL bằng COALESCE, liên kết Dimension và chuẩn hóa kiểu dữ liệu")

    # BƯỚC 3: AGGREGATE & NẠP VÀO GOLD (BUSINESS MARTS)
    sql_gold = """
    CREATE TABLE IF NOT EXISTS iceberg.retail_gold.mart_monthly_store_performance AS
    SELECT 
        sales_year,
        sales_month,
        store_id,
        store_name,
        store_state,
        category,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(net_revenue), 2) AS total_revenue,
        ROUND(SUM(net_profit), 2) AS total_profit,
        ROUND((SUM(net_profit) / NULLIF(SUM(net_revenue), 0)) * 100, 2) AS profit_margin_pct,
        CURRENT_TIMESTAMP AS _calculated_at
    FROM iceberg.retail_silver.sales_transactions
    GROUP BY sales_year, sales_month, store_id, store_name, store_state, category
    """
    execute_step(cur, 3, "Tầng Gold (Business KPI Aggregation)", sql_gold,
                 "Tính toán trước các chỉ số KPI theo Tháng/Cửa hàng/Danh mục phục vụ Superset Dashboard và AI")

    # BƯỚC 4: KIỂM TOÁN VÀ BÁO CÁO KẾT QUẢ (AUDIT & VALIDATION)
    print("\n[4/4] BÁO CÁO THỐNG KÊ TOÀN TRÌNH ETL:")
    tables = [
        ("Bronze", "iceberg.retail_bronze.store_sales_raw"),
        ("Silver", "iceberg.retail_silver.sales_transactions"),
        ("Gold", "iceberg.retail_gold.mart_monthly_store_performance")
    ]
    for tier, tbl in tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f" * [{tier:<6}] {tbl:<45} : {cnt:>8,} dòng")

    print("\n[XÁC NHẬN] Quy trình ETL hoàn thành 100%! Dữ liệu đã sẵn sàng trên MinIO & Superset.")

if __name__ == "__main__":
    main()
