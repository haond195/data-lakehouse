"""
RUNNER THỰC THI DBT-TRINO TRANSFORMATION & TESTS TRÊN LAKEHOUSE (ROOT SHORTCUT)
"""
import subprocess
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def run_dbt():
    dbt_dir = os.path.join(os.path.dirname(__file__), "dbt_lakehouse")
    dbt_dir = os.path.abspath(dbt_dir)

    target = "stg"
    if len(sys.argv) > 1 and sys.argv[1].strip() in ["stg", "dev"]:
        target = sys.argv[1].strip()

    print("=" * 65)
    print(f" BẮT ĐẦU CHẠY DBT-TRINO TRANSFORMATION (TARGET: {target.upper()})")
    print("=" * 65)

    # 1. Chạy dbt run
    cmd_run = ["dbt", "run", "--target", target, "--profiles-dir", "."]
    res_run = subprocess.run(cmd_run, cwd=dbt_dir)
    if res_run.returncode != 0:
        print("\n[LỖI] dbt run thất bại!")
        sys.exit(1)

    # 2. Chạy dbt test
    print("\n" + "=" * 65)
    print(f" BẮT ĐẦU CHẠY KIỂM ĐỊNH CHẤT LƯỢNG DỮ LIỆU (DBT TEST - {target.upper()})")
    print("=" * 65)
    cmd_test = ["dbt", "test", "--target", target, "--profiles-dir", "."]
    res_test = subprocess.run(cmd_test, cwd=dbt_dir)
    if res_test.returncode != 0:
        print("\n[LỖI] Một số test dữ liệu bị thất bại!")
        sys.exit(1)

    print(f"\n[HOÀN TẤT] Toàn bộ models dbt và tests kiểm định target '{target}' đã vượt qua 100%!")

if __name__ == "__main__":
    run_dbt()
