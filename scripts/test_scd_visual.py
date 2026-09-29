"""
TEST TRỰC QUAN CÁC KIỂU SCD (SLOWLY CHANGING DIMENSIONS) TRÊN APACHE ICEBERG LAKEHOUSE
"""
import sys
from trino.dbapi import connect
import pandas as pd

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def print_header(title):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)

def print_step(step, desc):
    print(f"\n[BƯỚC {step}] {desc}")

def run_query(cur, sql, desc=""):
    if desc:
        print(f"-> {desc}...")
    cur.execute(sql)

def fetch_df(cur, sql):
    cur.execute(sql)
    cols = [d[0] for d in cur.description]
    data = cur.fetchall()
    return pd.DataFrame(data, columns=cols)

def main():
    print_header("CHƯƠNG TRÌNH THỰC NGHIỆM TRỰC QUAN CÁC KIỂU SCD TRÊN LAKEHOUSE")
    print("Mục tiêu: Quan sát trực quan sự khác biệt giữa SCD Type 1, Type 2, Type 3")
    print("Kịch bản: Khách hàng C101 (Nguyễn Văn Nam) ban đầu ở Hà Nội (hạng Silver), sau đó chuyển vào TP.HCM (lên hạng Gold).")

    conn = connect(host='localhost', port=8080, user='admin', catalog='iceberg_stg')
    cur = conn.cursor()

    # 0. Tạo schema sandbox
    run_query(cur, "CREATE SCHEMA IF NOT EXISTS iceberg_stg.demo_scd")

    # =========================================================================
    # THỰC NGHIỆM SCD TYPE 1: GHI ĐÈ (OVERWRITE - KHÔNG LƯU LỊCH SỬ)
    # =========================================================================
    print_header("1. THỰC NGHIỆM SCD TYPE 1 (GHI ĐÈ DỮ LIỆU)")
    run_query(cur, "DROP TABLE IF EXISTS iceberg_stg.demo_scd.customer_scd1")
    run_query(cur, """
        CREATE TABLE iceberg_stg.demo_scd.customer_scd1 (
            customer_id VARCHAR,
            customer_name VARCHAR,
            city VARCHAR,
            loyalty_tier VARCHAR,
            updated_at TIMESTAMP(6) WITH TIME ZONE
        )
    """, "Tạo bảng SCD Type 1")

    # Trạng thái T0 (2023)
    run_query(cur, """
        INSERT INTO iceberg_stg.demo_scd.customer_scd1 VALUES 
        ('C101', 'Nguyễn Văn Nam', 'Hà Nội', 'Silver', TIMESTAMP '2023-01-01 08:00:00 UTC')
    """, "Nạp trạng thái ban đầu T0 (Năm 2023)")

    print("\n👉 BẢNG BAN ĐẦU (T0):")
    df1_before = fetch_df(cur, "SELECT customer_id, customer_name, city, loyalty_tier, updated_at FROM iceberg_stg.demo_scd.customer_scd1")
    print(df1_before.to_string(index=False))

    # Sự kiện T1 (2024): Đổi địa chỉ sang TP.HCM, nâng hạng Gold
    run_query(cur, """
        UPDATE iceberg_stg.demo_scd.customer_scd1 
        SET city = 'TP.HCM', loyalty_tier = 'Gold', updated_at = TIMESTAMP '2024-01-01 08:00:00 UTC'
        WHERE customer_id = 'C101'
    """, "Sự kiện T1 (2024): UPDATE ghi đè trực tiếp")

    print("\n👉 BẢNG SAU KHI CẬP NHẬT SCD TYPE 1:")
    df1_after = fetch_df(cur, "SELECT customer_id, customer_name, city, loyalty_tier, updated_at FROM iceberg_stg.demo_scd.customer_scd1")
    print(df1_after.to_string(index=False))
    print("=> NHẬN XÉT TYPE 1: Dữ liệu 'Hà Nội' và 'Silver' bị XÓA HOÀN TOÀN. Mất sạch dấu vết lịch sử!")

    # =========================================================================
    # THỰC NGHIỆM SCD TYPE 2: THÊM DÒNG MỚI (LƯU VẾT TOÀN DIỆN VỚI NGÀY HIỆU LỰC)
    # =========================================================================
    print_header("2. THỰC NGHIỆM SCD TYPE 2 (THÊM DÒNG MỚI / DBT SNAPSHOT)")
    run_query(cur, "DROP TABLE IF EXISTS iceberg_stg.demo_scd.customer_scd2")
    run_query(cur, """
        CREATE TABLE iceberg_stg.demo_scd.customer_scd2 (
            surrogate_key VARCHAR,
            customer_id VARCHAR,
            customer_name VARCHAR,
            city VARCHAR,
            loyalty_tier VARCHAR,
            valid_from DATE,
            valid_to DATE,
            is_current BOOLEAN
        )
    """, "Tạo bảng SCD Type 2")

    # Trạng thái T0 (2023)
    run_query(cur, """
        INSERT INTO iceberg_stg.demo_scd.customer_scd2 VALUES 
        ('SK_001', 'C101', 'Nguyễn Văn Nam', 'Hà Nội', 'Silver', DATE '2023-01-01', DATE '9999-12-31', TRUE)
    """, "Nạp trạng thái ban đầu T0 (Năm 2023)")

    print("\n👉 BẢNG BAN ĐẦU (T0):")
    df2_before = fetch_df(cur, "SELECT surrogate_key, customer_id, customer_name, city, loyalty_tier, valid_from, valid_to, is_current FROM iceberg_stg.demo_scd.customer_scd2")
    print(df2_before.to_string(index=False))

    # Sự kiện T1 (2024): Đóng phiên bản cũ + chèn phiên bản mới
    run_query(cur, """
        UPDATE iceberg_stg.demo_scd.customer_scd2 
        SET valid_to = DATE '2024-01-01', is_current = FALSE
        WHERE customer_id = 'C101' AND is_current = TRUE
    """, "Đóng phiên bản cũ (valid_to = '2024-01-01', is_current = FALSE)")

    run_query(cur, """
        INSERT INTO iceberg_stg.demo_scd.customer_scd2 VALUES 
        ('SK_002', 'C101', 'Nguyễn Văn Nam', 'TP.HCM', 'Gold', DATE '2024-01-01', DATE '9999-12-31', TRUE)
    """, "Chèn phiên bản mới (valid_from = '2024-01-01', is_current = TRUE)")

    print("\n👉 BẢNG SAU KHI CẬP NHẬT SCD TYPE 2:")
    df2_after = fetch_df(cur, "SELECT surrogate_key, customer_id, customer_name, city, loyalty_tier, valid_from, valid_to, is_current FROM iceberg_stg.demo_scd.customer_scd2 ORDER BY valid_from")
    print(df2_after.to_string(index=False))

    print("\n🔍 KIỂM CHỨNG TRUY VẤN THEO ĐIỂM THỜI GIAN (POINT-IN-TIME QUERY):")
    # Query thời điểm tháng 6/2023
    df_2023 = fetch_df(cur, """
        SELECT customer_name, city, loyalty_tier, '2023-06-15' AS query_at
        FROM iceberg_stg.demo_scd.customer_scd2
        WHERE customer_id = 'C101' 
          AND DATE '2023-06-15' >= valid_from AND DATE '2023-06-15' < valid_to
    """)
    print("1. Trạng thái khách hàng khi mua hàng vào 15/06/2023:")
    print(df_2023.to_string(index=False))

    # Query thời điểm hiện tại
    df_current = fetch_df(cur, """
        SELECT customer_name, city, loyalty_tier, 'Hiện tại' AS query_at
        FROM iceberg_stg.demo_scd.customer_scd2
        WHERE customer_id = 'C101' AND is_current = TRUE
    """)
    print("2. Trạng thái khách hàng ở thời điểm hiện tại:")
    print(df_current.to_string(index=False))
    print("=> NHẬN XÉT TYPE 2: Giữ trọn vẹn lịch sử! Báo cáo doanh thu năm 2023 vẫn ghi nhận cho Hà Nội, năm 2024 ghi nhận cho TP.HCM!")

    # =========================================================================
    # THỰC NGHIỆM SCD TYPE 3: THÊM CỘT GIÁ TRỊ CŨ (PREVIOUS COLUMN)
    # =========================================================================
    print_header("3. THỰC NGHIỆM SCD TYPE 3 (THÊM CỘT GIÁ TRỊ CŨ)")
    run_query(cur, "DROP TABLE IF EXISTS iceberg_stg.demo_scd.customer_scd3")
    run_query(cur, """
        CREATE TABLE iceberg_stg.demo_scd.customer_scd3 (
            customer_id VARCHAR,
            customer_name VARCHAR,
            current_city VARCHAR,
            previous_city VARCHAR,
            current_tier VARCHAR,
            previous_tier VARCHAR,
            effective_date DATE
        )
    """, "Tạo bảng SCD Type 3")

    # Trạng thái T0
    run_query(cur, """
        INSERT INTO iceberg_stg.demo_scd.customer_scd3 VALUES 
        ('C101', 'Nguyễn Văn Nam', 'Hà Nội', NULL, 'Silver', NULL, DATE '2023-01-01')
    """, "Nạp trạng thái ban đầu T0")

    print("\n👉 BẢNG BAN ĐẦU (T0):")
    df3_before = fetch_df(cur, "SELECT customer_id, customer_name, current_city, previous_city, current_tier, previous_tier, effective_date FROM iceberg_stg.demo_scd.customer_scd3")
    print(df3_before.to_string(index=False))

    # Sự kiện T1: Cập nhật giá trị mới và đẩy giá trị cũ sang previous_*
    run_query(cur, """
        UPDATE iceberg_stg.demo_scd.customer_scd3
        SET previous_city = current_city,
            current_city = 'TP.HCM',
            previous_tier = current_tier,
            current_tier = 'Gold',
            effective_date = DATE '2024-01-01'
        WHERE customer_id = 'C101'
    """, "Cập nhật SCD Type 3: Đẩy current sang previous")

    print("\n👉 BẢNG SAU KHI CẬP NHẬT SCD TYPE 3:")
    df3_after = fetch_df(cur, "SELECT customer_id, customer_name, current_city, previous_city, current_tier, previous_tier, effective_date FROM iceberg_stg.demo_scd.customer_scd3")
    print(df3_after.to_string(index=False))
    print("=> NHẬN XÉT TYPE 3: Vẫn chỉ 1 dòng, tiện so sánh trực tiếp trước/sau nhưng chỉ nhớ được 1 lần thay đổi gần nhất!")

    print_header("KẾT LUẬN THỰC NGHIỆM")
    print("1. Dùng Type 1 khi: Dữ liệu bị sai chính tả, cần sửa lại mà không quan tâm lịch sử.")
    print("2. Dùng Type 2 khi: Cần phân tích chính xác lịch sử kinh doanh theo mốc thời gian (Chuẩn của dbt snapshot).")
    print("3. Dùng Type 3 khi: Chỉ cần so sánh nhanh trạng thái 'trước và sau' gần nhất trên 1 dòng báo cáo.")

if __name__ == "__main__":
    main()
