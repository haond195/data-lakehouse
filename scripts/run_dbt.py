"""
RUNNER THỰC THI DBT-TRINO TRANSFORMATION & TESTS TRÊN LAKEHOUSE
"""
import subprocess
import sys
import os

def run_dbt():
    dbt_dir = os.path.join(os.path.dirname(__file__), "..", "dbt_lakehouse")
    dbt_dir = os.path.abspath(dbt_dir)

    print("=" * 65)
    print(" BẮT ĐẦU CHẠY DBT-TRINO TRANSFORMATION (MEDALLION)")
    print("=" * 65)

    # 1. Chạy dbt run
    cmd_run = ["dbt", "run", "--profiles-dir", "."]
    res_run = subprocess.run(cmd_run, cwd=dbt_dir)
    if res_run.returncode != 0:
        print("\n[LỖI] dbt run thất bại!")
        sys.exit(1)

    # 2. Chạy dbt test
    print("\n" + "=" * 65)
    print(" BẮT ĐẦU CHẠY KIỂM ĐỊNH CHẤT LƯỢNG DỮ LIỆU (DBT TEST)")
    print("=" * 65)
    cmd_test = ["dbt", "test", "--profiles-dir", "."]
    res_test = subprocess.run(cmd_test, cwd=dbt_dir)
    if res_test.returncode != 0:
        print("\n[LỖI] Một số test dữ liệu bị thất bại!")
        sys.exit(1)

    print("\n[HOÀN TẤT] Toàn bộ models dbt và tests kiểm định đã vượt qua 100%!")

if __name__ == "__main__":
    run_dbt()
