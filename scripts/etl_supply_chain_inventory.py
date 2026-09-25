"""
PIPELINE ETL MEDALLION: TỒN KHO & HÀNG HÓA TRÊN KỆ (SUPPLY CHAIN & INVENTORY)
Nguồn: TPC-DS SF1 (inventory, warehouse, store_returns) -> Iceberg S3
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
        user="etl_inventory",
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
    print(" BẮT ĐẦU PIPELINE ETL: TỒN KHO & ĐỐI SOÁT KHO - KỆ (MEDALLION)     ")
    print("===================================================================")

    # 1. TẦNG BRONZE
    run_step(cur, "1/6", "Bronze: Nạp danh mục kho hàng (warehouse_raw)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.warehouse_raw AS
    SELECT 
        w_warehouse_sk AS warehouse_id,
        w_warehouse_id AS warehouse_code,
        w_warehouse_name AS warehouse_name,
        w_warehouse_sq_ft AS sq_ft,
        w_city AS city,
        w_state AS state,
        w_country AS country,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.warehouse
    """)

    run_step(cur, "2/6", "Bronze: Nạp số liệu kiểm kê tồn kho (inventory_raw - 150.000 dòng)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_bronze.inventory_raw AS
    SELECT 
        inv_date_sk AS date_id,
        inv_item_sk AS item_id,
        inv_warehouse_sk AS warehouse_id,
        inv_quantity_on_hand AS raw_qty_on_hand,
        CURRENT_TIMESTAMP AS _ingested_at
    FROM tpcds.sf1.inventory
    LIMIT 150000
    """)

    # 2. TẦNG SILVER
    run_step(cur, "3/6", "Silver: Chuẩn hóa danh mục kho (dim_warehouse)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.dim_warehouse AS
    SELECT 
        warehouse_id,
        TRIM(warehouse_code) AS warehouse_code,
        COALESCE(TRIM(warehouse_name), 'Unknown Warehouse') AS warehouse_name,
        COALESCE(sq_ft, 0) AS total_sq_ft,
        COALESCE(city, 'Unknown') AS city,
        COALESCE(state, 'Unknown') AS state,
        COALESCE(country, 'Unknown') AS country,
        _ingested_at,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.warehouse_raw
    """)

    run_step(cur, "4/6", "Silver: Làm sạch & bổ sung thông tin tồn kho (inventory_snapshot)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_silver.inventory_snapshot AS
    SELECT 
        inv.date_id,
        d.d_date AS snapshot_date,
        d.d_year AS inventory_year,
        d.d_moy AS inventory_month,
        inv.warehouse_id,
        w.warehouse_name,
        inv.item_id,
        COALESCE(i.i_item_desc, 'Unknown Product') AS product_name,
        COALESCE(i.i_category, 'Uncategorized') AS category,
        COALESCE(i.i_brand, 'No Brand') AS brand,
        CAST(COALESCE(i.i_current_price, 0.0) AS DOUBLE) AS unit_price,
        inv.raw_qty_on_hand AS qty_on_hand,
        ROUND(inv.raw_qty_on_hand * CAST(COALESCE(i.i_current_price, 0.0) AS DOUBLE), 2) AS inventory_value,
        CURRENT_TIMESTAMP AS _transformed_at
    FROM iceberg.retail_bronze.inventory_raw inv
    INNER JOIN tpcds.sf1.date_dim d ON inv.date_id = d.d_date_sk
    LEFT JOIN tpcds.sf1.item i ON inv.item_id = i.i_item_sk
    LEFT JOIN iceberg.retail_silver.dim_warehouse w ON inv.warehouse_id = w.warehouse_id
    WHERE inv.raw_qty_on_hand >= 0
    """)

    # 3. TẦNG GOLD (KPIs KHO & KỆ)
    run_step(cur, "5/6", "Gold: Mart phân tích vòng quay kho & kệ (mart_inventory_turnover)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_gold.mart_inventory_turnover AS
    WITH sales_summary AS (
        SELECT 
            sales_year,
            sales_month,
            category,
            SUM(quantity) AS units_sold_on_shelf,
            ROUND(SUM(net_revenue), 2) AS shelf_revenue
        FROM iceberg.retail_silver.sales_transactions
        GROUP BY sales_year, sales_month, category
    ),
    inventory_summary AS (
        SELECT 
            inventory_year,
            inventory_month,
            category,
            SUM(qty_on_hand) AS total_warehouse_stock,
            ROUND(SUM(inventory_value), 2) AS total_inventory_valuation
        FROM iceberg.retail_silver.inventory_snapshot
        GROUP BY inventory_year, inventory_month, category
    )
    SELECT 
        COALESCE(i.inventory_year, s.sales_year) AS report_year,
        COALESCE(i.inventory_month, s.sales_month) AS report_month,
        COALESCE(i.category, s.category) AS category,
        COALESCE(i.total_warehouse_stock, 0) AS total_warehouse_stock,
        COALESCE(i.total_inventory_valuation, 0.0) AS total_inventory_valuation,
        COALESCE(s.units_sold_on_shelf, 0) AS units_sold_on_shelf,
        COALESCE(s.shelf_revenue, 0.0) AS shelf_revenue,
        ROUND(
            CAST(COALESCE(s.units_sold_on_shelf, 0) AS DOUBLE) / 
            NULLIF(CAST(COALESCE(i.total_warehouse_stock, 0) AS DOUBLE), 0.0), 
            4
        ) AS shelf_to_warehouse_ratio,
        CURRENT_TIMESTAMP AS _calculated_at
    FROM inventory_summary i
    FULL OUTER JOIN sales_summary s 
        ON i.inventory_year = s.sales_year 
        AND i.inventory_month = s.sales_month 
        AND i.category = s.category
    """)

    run_step(cur, "6/6", "Gold: Mart hiệu suất kho hàng (mart_warehouse_utilization)", """
    CREATE TABLE IF NOT EXISTS iceberg.retail_gold.mart_warehouse_utilization AS
    SELECT 
        w.warehouse_id,
        w.warehouse_name,
        w.city,
        w.state,
        w.total_sq_ft,
        COUNT(DISTINCT inv.item_id) AS total_unique_skus,
        SUM(inv.qty_on_hand) AS total_units_stored,
        ROUND(SUM(inv.inventory_value), 2) AS total_stored_value,
        ROUND(CAST(SUM(inv.qty_on_hand) AS DOUBLE) / NULLIF(w.total_sq_ft, 0), 2) AS density_units_per_sq_ft,
        CURRENT_TIMESTAMP AS _calculated_at
    FROM iceberg.retail_silver.dim_warehouse w
    LEFT JOIN iceberg.retail_silver.inventory_snapshot inv ON w.warehouse_id = inv.warehouse_id
    GROUP BY w.warehouse_id, w.warehouse_name, w.city, w.state, w.total_sq_ft
    """)

    # KIỂM TRA THỐNG KÊ TOÀN BỘ
    print("\n" + "=" * 65)
    print(" TỔNG HỢP CÁC BẢNG KHO - KỆ TRONG MEDALLION:")
    print("=" * 65)
    all_tables = [
        ("Bronze", "iceberg.retail_bronze.warehouse_raw"),
        ("Bronze", "iceberg.retail_bronze.inventory_raw"),
        ("Silver", "iceberg.retail_silver.dim_warehouse"),
        ("Silver", "iceberg.retail_silver.inventory_snapshot"),
        ("Gold",   "iceberg.retail_gold.mart_inventory_turnover"),
        ("Gold",   "iceberg.retail_gold.mart_warehouse_utilization"),
    ]
    for tier, tbl in all_tables:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f" * [{tier:<6}] {tbl:<50} : {cnt:>9,} dòng")
    print("=" * 65)
    print(" Pipeline Medallion Kho & Kệ hoàn thành xuất sắc!")

if __name__ == "__main__":
    main()
