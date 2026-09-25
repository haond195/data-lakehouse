"""
GENERIC CONFIG-DRIVEN ETL RUNNER FOR TRINO & APACHE ICEBERG
Đọc cấu hình từ file YAML bất kỳ và tự động sinh SQL chạy Bronze -> Silver -> Gold.
"""
import sys
import os
import time
import yaml

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from trino.dbapi import connect

def get_connection():
    return connect(
        host=os.getenv("TRINO_HOST", "localhost"),
        port=int(os.getenv("TRINO_PORT", 8080)),
        user="config_etl_engine",
        catalog="iceberg"
    )

def execute_sql(cur, title, sql):
    print(f"\n[THỰC THI] {title}...")
    t0 = time.time()
    cur.execute(sql)
    dur = time.time() - t0
    print(f" -> Xong sau {dur:.2f}s")

def run_pipeline(config_path: str):
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    print("=" * 65)
    print(f" KHỞI CHẠY PIPELINE: {cfg.get('pipeline_name', 'Unnamed')} (v{cfg.get('version', '1.0')})")
    print("=" * 65)

    conn = get_connection()
    cur = conn.cursor()

    # 1. Tự động tạo schemas nếu chưa tồn tại
    for tier in ["bronze", "silver", "gold"]:
        if tier in cfg and "schema" in cfg[tier]:
            cat = cfg[tier].get("catalog", "iceberg")
            sch = cfg[tier]["schema"]
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {cat}.{sch}")

    # 2. Xử lý Bronze
    b = cfg["bronze"]
    src = cfg["source"]
    b_table = f"{b.get('catalog', 'iceberg')}.{b['schema']}.{b['table']}"
    src_table = f"{src.get('catalog', 'tpcds')}.{src['schema']}.{src['table']}"
    
    b_cols = [f"{col['source']} AS {col['target']}" for col in b["columns"]]
    b_cols.append("CURRENT_TIMESTAMP AS _ingested_at")
    limit_clause = f"LIMIT {src['limit']}" if "limit" in src else ""
    
    sql_bronze = f"""
    CREATE TABLE IF NOT EXISTS {b_table} AS
    SELECT {', '.join(b_cols)}
    FROM {src_table}
    {limit_clause}
    """
    execute_sql(cur, f"Tạo tầng Bronze: {b_table}", sql_bronze)

    # 3. Xử lý Silver
    s = cfg["silver"]
    s_table = f"{s.get('catalog', 'iceberg')}.{s['schema']}.{s['table']}"
    s_cols = [f"{col['expr']} AS {col['target']}" for col in s["transformations"]]
    s_cols.append("_ingested_at")
    s_cols.append("CURRENT_TIMESTAMP AS _transformed_at")
    where_clause = f"WHERE {' AND '.join(s['filters'])}" if s.get("filters") else ""

    sql_silver = f"""
    CREATE TABLE IF NOT EXISTS {s_table} AS
    SELECT {', '.join(s_cols)}
    FROM {b_table}
    {where_clause}
    """
    execute_sql(cur, f"Tạo tầng Silver: {s_table}", sql_silver)

    # 4. Xử lý Gold
    g = cfg["gold"]
    g_table = f"{g.get('catalog', 'iceberg')}.{g['schema']}.{g['table']}"
    group_cols = g.get("group_by", [])
    metric_cols = [f"{m['expr']} AS {m['target']}" for m in g["metrics"]]
    g_all_cols = group_cols + metric_cols + ["CURRENT_TIMESTAMP AS _calculated_at"]
    group_clause = f"GROUP BY {', '.join(group_cols)}" if group_cols else ""

    sql_gold = f"""
    CREATE TABLE IF NOT EXISTS {g_table} AS
    SELECT {', '.join(g_all_cols)}
    FROM {s_table}
    {group_clause}
    """
    execute_sql(cur, f"Tạo tầng Gold: {g_table}", sql_gold)

    # 5. Kiểm tra kết quả
    print("\n" + "=" * 65)
    print(" KẾT QUẢ SỐ LƯỢNG BẢN GHI:")
    print("=" * 65)
    for name, tbl in [("Bronze", b_table), ("Silver", s_table), ("Gold", g_table)]:
        cur.execute(f"SELECT COUNT(*) FROM {tbl}")
        cnt = cur.fetchone()[0]
        print(f" - [{name:<6}] {tbl:<45} : {cnt:,} dòng")
    print("=" * 65)
    print(" Pipeline hoàn tất thành công 100%!")

if __name__ == "__main__":
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config/etl_pipeline.yaml"
    run_pipeline(config_file)
