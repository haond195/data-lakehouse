import time
import sys
from trino.dbapi import connect

print("Starting migration from TPC-DS to Apache Iceberg...")

conn = connect(
    host="localhost",
    port=8080,
    user="admin",
    catalog="iceberg",
    schema="retail_gold"
)
cursor = conn.cursor()

tables = [
    ("item", "SELECT * FROM tpcds.sf1.item"),
    ("date_dim", "SELECT * FROM tpcds.sf1.date_dim"),
    ("store", "SELECT * FROM tpcds.sf1.store"),
    ("promotion", "SELECT * FROM tpcds.sf1.promotion"),
    ("store_sales", "SELECT * FROM tpcds.sf1.store_sales LIMIT 50000"),
    ("web_sales", "SELECT * FROM tpcds.sf1.web_sales LIMIT 50000")
]

for table_name, select_query in tables:
    start_time = time.time()
    print(f"Loading table: {table_name} ...", end="", flush=True)
    try:
        cursor.execute(f"DROP TABLE IF EXISTS iceberg.retail_gold.{table_name}")
        cursor.execute(f"""
            CREATE TABLE iceberg.retail_gold.{table_name} AS 
            {select_query}
        """)
        elapsed = round(time.time() - start_time, 2)
        print(f" DONE ({elapsed}s)")
    except Exception as e:
        print(f" ERROR: {e}")

print("Completed migration to Apache Iceberg on MinIO S3!")