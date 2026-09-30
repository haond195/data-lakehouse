# 📚 Cẩm Nang Kiến Thức Về dbt (Data Build Tool) Cho Data Lakehouse

## 1. dbt Là Gì? (Khái Niệm & Triết Lý)

- **dbt (Data Build Tool)** là chuẩn công nghiệp cho chữ **T (Transform)** trong kiến trúc dữ liệu hiện đại **ELT (Extract - Load - Transform)**.
- **Triết lý cốt lõi**: Đưa các chuẩn mực tốt nhất của Kỹ nghệ phần mềm (**Software Engineering Best Practices**) vào Phân tích dữ liệu:
  1. **Quản lý phiên bản (Version Control)**: Toàn bộ mô hình dữ liệu được quản lý qua Git.
  2. **Kiểm thử tự động (Automated Testing)**: Kiểm định chất lượng dữ liệu (`not_null`, `unique`, `relationships`) trước khi đưa vào sản xuất.
  3. **Tài liệu hóa sống (Living Documentation)**: Tự động sinh Data Dictionary và sơ đồ phả hệ (Data Lineage Graph).
  4. **Tính module hóa (Modularity & DRY)**: Tái sử dụng logic qua Jinja Macro và hàm tham chiếu `{{ ref(...) }}`.
  5. **Môi trường độc lập (CI/CD)**: Dễ dàng chuyển đổi giữa `dev`, `staging`, và `prod` qua cấu hình `profiles.yml`.

---

## 2. Cách dbt Hoạt Động (Compile & Orchestrate)

1. **Người dùng viết**: Câu lệnh `SELECT` thuần túy kèm Jinja template trong thư mục `models/` (không cần viết `CREATE TABLE`, `DROP`, hay `INSERT`).
2. **dbt biên dịch (Compile)**: Phân tích cây phụ thuộc (DAG), thay thế `{{ ref(...) }}` thành tên bảng vật lý đầy đủ (`catalog.schema.table`), và bọc câu lệnh `SELECT` thành cú pháp DDL/DML chuẩn của engine đích.
3. **Thực thi trên Engine (Trino)**: dbt **không lưu trữ hay xử lý dữ liệu**. Nó gửi câu lệnh SQL đã biên dịch sang Trino. Trino phân tán tính toán và ghi file nén Parquet lên MinIO Object Storage.

---

## 3. Các Khái Niệm Cốt Lõi Trong dbt

### 3.1. Materializations (Cách lưu trữ dữ liệu)
Cấu hình qua khối `{{ config(materialized='...') }}`:
- **`view`**: Tạo View logic trong database. Tiết kiệm dung lượng lưu trữ, luôn phản ánh dữ liệu mới nhất nhưng tốn chi phí tính toán khi query.
- **`table`**: Tạo bảng vật lý (Iceberg Table). Tối ưu tốc độ truy vấn cho BI/AI, tái tạo lại toàn bộ bảng sau mỗi lần chạy.
- **`incremental`**: Chỉ xử lý và chèn dữ liệu mới hoặc thay đổi từ lần chạy trước (`is_incremental()`), tiết kiệm tài nguyên trên bảng lớn.
- **`ephemeral`**: Tạo khối CTE tạm thời trong câu truy vấn, không sinh bảng hay view trong database.

### 3.2. Hàm tham chiếu Jinja (`ref` và `source`)
- **`{{ source('source_name', 'table_name') }}`**: Tham chiếu bảng dữ liệu thô đầu vào (Raw ingestion).
- **`{{ ref('model_name') }}`**: Tham chiếu đến model dbt khác. dbt sẽ tự động suy ra thứ tự chạy: model được tham chiếu phải chạy xong trước.

### 3.3. Kiểm thử chất lượng dữ liệu (Data Testing)
- **Generic Tests (Khai báo trong file `schema.yml`)**:
  - `unique`: Đảm bảo giá trị cột không bị trùng lặp (khóa chính).
  - `not_null`: Đảm bảo cột không chứa giá trị NULL.
  - `relationships`: Đảm bảo tính toàn vẹn tham chiếu (Foreign Key).
  - `accepted_values`: Giới hạn các giá trị hợp lệ của cột (vd: `['Store', 'Web', 'Catalog']`).
- **Singular Tests**: Viết file `.sql` chứa câu truy vấn tìm bản ghi vi phạm logic nghiệp vụ. Nếu câu truy vấn trả về 0 dòng -> Test PASS.

---

## 4. Kiến Trúc dbt Medallion Trong Dự Án Này

Dự án triển khai **34 dbt models** chia thành 3 tầng:

```
[TPC-DS SF1 Sources]
         │
         ▼
 1. TẦNG BRONZE (17 Staging Models - models/bronze/)
    - Đọc dữ liệu thô từ tpcds.sf1, đổi tên cột chuẩn snake_case, ép kiểu dữ liệu.
    - Materialization: View / Table.
         │
         ▼
 2. TẦNG SILVER (10 Dimensions & Clean Facts - models/silver/)
    - Khử NULL (COALESCE), lọc bản ghi rác, hợp nhất dữ liệu đa kênh (fct_returns_unified).
    - Áp dụng kỹ thuật SCD Type 2 cho dim_customers.
    - Materialization: Table (Apache Iceberg).
         │
         ▼
 3. TẦNG GOLD (7 Data Marts - models/gold/)
    - Tính toán trước các chỉ số kinh doanh phục vụ Superset Dashboard và AI Chatbot.
    - Các mart đa bảng: mart_product_return_rates, mart_inventory_sales_velocity, mart_omnichannel_performance.
    - Materialization: Table (Apache Iceberg).
```

---

## 5. Các Lệnh dbt Cơ Bản Thường Dùng

| Lệnh | Mục đích |
| :--- | :--- |
| `dbt compile` | Kiểm tra cú pháp và dịch Jinja sang SQL thuần trong thư mục `target/` |
| `dbt run` | Thực thi toàn bộ các models trong dự án |
| `dbt run --select mart_product_return_rates` | Chỉ thực thi một model cụ thể |
| `dbt run --select models/gold/` | Thực thi toàn bộ models trong thư mục Gold |
| `dbt run --select +mart_omnichannel_performance` | Thực thi model Gold và toàn bộ các bảng phụ thuộc đi trước nó |
| `dbt test` | Chạy toàn bộ các bài kiểm tra chất lượng dữ liệu |
| `dbt docs generate && dbt docs serve` | Sinh tài liệu tương tác và mở sơ đồ Lineage Graph trên trình duyệt |
