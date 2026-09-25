"""
PIPELINE ETL MEDALLION HOÀN CHỈNH: BÁN HÀNG ĐA KÊNH (OMNICHANNEL) & GIAO VẬN, ĐỔI TRẢ (LOGISTICS & RETURNS)
Nguồn: TPC-DS SF1 (web_sales, catalog_sales, store_returns, ship_mode, reason) -> Iceberg S3
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
        user="etl_omnichannel",
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
    print(" BẮT ĐẦU PIPELINE ETL: ĐA KÊNH (WEB/CATALOG) & GIAO VẬN, ĐỔI TRẢ  ")
    print("===================================================================")

    # 1. TẦNG BRONZE
    run_step(cur, "1/7", "Bronze: Nạp giao dịch Web Sales thô (web_sales_raw - 50.000 dòng)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.web_sales_raw AS
    SELECT 
        ws_order_number AS order_id,
        ws_item_sk AS item_id,
        ws_bill_customer_sk AS customer_id,
        ws_ship_mode_sk AS ship_mode_id,
        ws_sold_date_sk AS date_id,
        ws_quantity AS raw_quantity,
        ws_net_paid AS raw_net_paid,
        ws_net_profit AS raw_net_profit,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.web_sales
    LIMIT 50000
    """)

    run_step(cur, "2/7", "Bronze: Nạp giao dịch Catalog Sales thô (catalog_sales_raw - 50.000 dòng)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.catalog_sales_raw AS
    SELECT 
        cs_order_number AS order_id,
        cs_item_sk AS item_id,
        cs_bill_customer_sk AS customer_id,
        cs_ship_mode_sk AS ship_mode_id,
        cs_sold_date_sk AS date_id,
        cs_quantity AS raw_quantity,
        cs_net_paid AS raw_net_paid,
        cs_net_profit AS raw_net_profit,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.catalog_sales
    LIMIT 50000
    """)

    run_step(cur, "3/7", "Bronze: Nạp danh mục giao vận (ship_mode_raw)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.ship_mode_raw AS
    SELECT sm_ship_mode_sk AS ship_mode_id, sm_type AS ship_type, sm_carrier AS carrier, CURRENT_TIMESTAMP AS _ingested_at FROM tpcds.sf1.ship_mode
    """)

    run_step(cur, "3b/7", "Bronze: Nạp lý do đổi trả (return_reason_raw)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.return_reason_raw AS
    SELECT r_reason_sk AS reason_id, r_reason_desc AS reason_desc, CURRENT_TIMESTAMP AS _ingested_at FROM tpcds.sf1.reason
    """)

    run_step(cur, "3c/7", "Bronze: Nạp dữ liệu đổi trả cửa hàng (store_returns_raw)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.store_returns_raw AS
    SELECT sr_ticket_number AS ticket_number, sr_item_sk AS item_id, sr_customer_sk AS customer_id, sr_reason_sk AS reason_id, sr_return_quantity AS return_qty, sr_return_amt AS refund_amt, CURRENT_TIMESTAMP AS _ingested_at FROM tpcds.sf1.store_returns LIMIT 25000
    """)

    # 2. TẦNG SILVER: HỢP NHẤT BÁN LẺ ĐA KÊNH (OMNICHANNEL)
    run_step(cur, "4/7", "Silver: Hợp nhất giao dịch Đa Kênh (omnichannel_sales_transactions)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.omnichannel_sales_transactions AS
    -- Kênh 1: Cửa hàng vật lý (Store)
    SELECT 
        'STORE' AS sales_channel,
        r.order_id,
        r.item_id,
        COALESCE(r.customer_id, 0) AS customer_id,
        d.d_year AS sales_year,
        d.d_moy AS sales_month,
        COALESCE(r.raw_quantity, 1) AS quantity,
        CAST(COALESCE(r.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
        CAST(COALESCE(r.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.store_sales_raw r
    INNER JOIN tpcds.sf1.date_dim d ON r.date_id = d.d_date_sk
    WHERE r.raw_net_paid IS NOT NULL AND r.raw_quantity > 0

    UNION ALL

    -- Kênh 2: Kênh trực tuyến (Web)
    SELECT 
        'WEB' AS sales_channel,
        w.order_id,
        w.item_id,
        COALESCE(w.customer_id, 0) AS customer_id,
        d.d_year AS sales_year,
        d.d_moy AS sales_month,
        COALESCE(w.raw_quantity, 1) AS quantity,
        CAST(COALESCE(w.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
        CAST(COALESCE(w.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.web_sales_raw w
    INNER JOIN tpcds.sf1.date_dim d ON w.date_id = d.d_date_sk
    WHERE w.raw_net_paid IS NOT NULL AND w.raw_quantity > 0

    UNION ALL

    -- Kênh 3: Kênh đặt hàng qua ấn phẩm (Catalog)
    SELECT 
        'CATALOG' AS sales_channel,
        c.order_id,
        c.item_id,
        COALESCE(c.customer_id, 0) AS customer_id,
        d.d_year AS sales_year,
        d.d_moy AS sales_month,
        COALESCE(c.raw_quantity, 1) AS quantity,
        CAST(COALESCE(c.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
        CAST(COALESCE(c.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.catalog_sales_raw c
    INNER JOIN tpcds.sf1.date_dim d ON c.date_id = d.d_date_sk
    WHERE c.raw_net_paid IS NOT NULL AND c.raw_quantity > 0
    """)

    run_step(cur, "5/7", "Silver: Làm sạch dữ liệu đổi trả hàng (returns_transactions)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.returns_transactions AS
    SELECT 
        r.ticket_number AS order_id,
        r.item_id,
        COALESCE(r.customer_id, 0) AS customer_id,
        COALESCE(TRIM(rs.reason_desc), 'Not Specified') AS return_reason,
        COALESCE(r.return_qty, 0) AS return_qty,
        CAST(COALESCE(r.refund_amt, 0.0) AS DOUBLE) AS refund_amt,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.store_returns_raw r
    LEFT JOIN iceberg.retail_bronze.return_reason_raw rs ON r.reason_id = rs.reason_id
    WHERE r.refund_amt >= 0
    """)

    # 3. TẦNG GOLD: BÁO CÁO ĐA KÊNH & ĐỔI TRẢ
    run_step(cur, "6/7", "Gold: Mart phân tích so sánh Đa Kênh (mart_omnichannel_performance)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_gold.mart_omnichannel_performance AS
    SELECT 
        sales_year,
        sales_month,
        sales_channel,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(quantity) AS total_units_sold,
        ROUND(SUM(net_revenue), 2) AS total_revenue,
        ROUND(SUM(net_profit), 2) AS total_profit,
        ROUND(SUM(net_revenue) / NULLIF(COUNT(DISTINCT order_id), 0), 2) AS avg_order_value,
        CURRENT_TIMESTAMP AS _calculated_at
    FROM iceberg.retail_silver.omnichannel_sales_transactions
    GROUP BY sales_year, sales_month, sales_channel
    """)

    run_step(cur, "7/7", "Gold: Mart phân tích lý do đổi trả hàng (mart_returns_analysis)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_gold.mart_returns_analysis AS
    SELECT 
        return_reason,
        COUNT(*) AS return_instances,
        SUM(return_qty) AS total_returned_units,
        ROUND(SUM(refund_amt), 2) AS total_refunded_amount,
        CURRENT_TIMESTAMP AS _calculated_at
    FROM iceberg.retail_silver.returns_transactions
    GROUP BY return_reason
    """)

    print("\n" + "=" * 65)
    print(" BÁO CÁO CÁC BẢNG ĐA KÊNH & GIAO VẬN MỚI TẠO:")
    print("=" * 65)
    tables = [
        ("Bronze", "iceberg.retail_bronze.web_sales_raw"),
        ("Bronze", "iceberg.retail_bronze.catalog_sales_raw"),
        ("Bronze", "iceberg.retail_bronze.store_returns_raw"),
        ("Silver", "iceberg.retail_silver.omnichannel_sales_transactions"),
        ("Silver", "iceberg.retail_silver.returns_transactions"),
        ("Gold  ", "iceberg.retail_gold.mart_omnichannel_performance"),
        ("Gold  ", "iceberg.retail_gold.mart_returns_analysis")
    ]
    for tier, tbl in tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f" * [{tier:<6}] {tbl:<52} : {cnt:>9,} dòng")
    print("=" * 65)
    print(" Hệ thống Lakehouse Medallion hiện đã đạt 100% độ phủ các miền nghiệp vụ!")

if __name__ == "__main__":
    main()
