#  Kiến Thức Về dbt (Data Build Tool) Cho Data Lakehouse

## 1. dbt Là Gì?

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

---

## 6. Mã Nguồn Ví Dụ Thực Tế Trong Dự Án

### 6.1. Model Bronze: Đọc Nguồn & Ép Kiểu Dữ Liệu
File: `models/bronze/stg_store_sales.sql`
```sql
{{ config(
    materialized='table',
    schema='stg_bronze' if target.name == 'stg' else 'retail_bronze'
) }}

SELECT 
    ss_ticket_number AS order_id,
    ss_item_sk AS item_id,
    ss_customer_sk AS customer_id,
    ss_store_sk AS store_id,
    ss_sold_date_sk AS date_id,
    ss_quantity AS raw_quantity,
    ss_net_paid AS raw_net_paid,
    ss_net_profit AS raw_net_profit,
    CURRENT_TIMESTAMP AS _ingested_at
FROM {{ source('tpcds_source', 'store_sales') }}
```
* **Đặc điểm**: Dùng `source(...)` để nạp dữ liệu thô, chuẩn hóa tên cột snake_case và thêm dấu mốc thời gian `_ingested_at`.

---

### 6.2. Model Silver: Làm Sạch, Khử NULL & Liên Kết Chiều
File: `models/silver/fct_sales_clean.sql`
```sql
{{ config(
    materialized='table',
    schema='stg_silver' if target.name == 'stg' else 'retail_silver'
) }}

SELECT 
    r.order_id,
    r.item_id,
    COALESCE(r.customer_id, 0) AS customer_id,
    COALESCE(r.store_id, 0) AS store_id,
    COALESCE(s.store_name, 'Online / Non-Store') AS store_name,
    COALESCE(s.state, 'Unknown State') AS store_state,
    d.calendar_year AS sales_year,
    d.month_of_year AS sales_month,
    COALESCE(r.raw_quantity, 1) AS quantity,
    CAST(COALESCE(r.raw_net_paid, 0.0) AS DOUBLE) AS net_revenue,
    CAST(COALESCE(r.raw_net_profit, 0.0) AS DOUBLE) AS net_profit,
    r._ingested_at,
    CURRENT_TIMESTAMP AS _transformed_at
FROM {{ ref('stg_store_sales') }} r
INNER JOIN {{ ref('dim_date') }} d ON r.date_id = d.date_id
LEFT JOIN {{ ref('dim_stores') }} s ON r.store_id = s.store_id
WHERE r.raw_net_paid IS NOT NULL AND r.raw_quantity > 0
```
* **Đặc điểm**: Dùng `{{ ref(...) }}` để kết nối bảng Bronze và Dimension. Dùng `COALESCE` xử lý Missing Values và mệnh đề `WHERE` để loại bỏ dữ liệu rác.

---

### 6.3. Model Gold: Data Mart Tổng Hợp Chỉ Số Đa Bảng (Multi-Table KPIs)
File: `models/gold/mart_product_return_rates.sql`
```sql
{{ config(
    materialized='table',
    schema='stg_gold' if target.name == 'stg' else 'retail_gold'
) }}

WITH sales_monthly AS (
    SELECT 
        s.item_id,
        s.sales_year,
        s.sales_month,
        COUNT(DISTINCT s.order_id) AS total_sales_orders,
        SUM(s.quantity) AS gross_sales_qty,
        SUM(s.net_revenue) AS gross_revenue
    FROM {{ ref('fct_sales_clean') }} s
    GROUP BY s.item_id, s.sales_year, s.sales_month
),
returns_monthly AS (
    SELECT 
        r.item_id,
        d.calendar_year AS return_year,
        d.month_of_year AS return_month,
        SUM(r.return_quantity) AS returned_qty,
        SUM(r.return_amount) AS refund_amount
    FROM {{ ref('fct_returns_unified') }} r
    INNER JOIN {{ ref('dim_date') }} d ON r.return_date_id = d.date_id
    GROUP BY r.item_id, d.calendar_year, d.month_of_year
)
SELECT 
    s.sales_year,
    s.sales_month,
    p.category,
    p.brand,
    SUM(s.gross_sales_qty) AS total_sold_qty,
    SUM(COALESCE(r.returned_qty, 0)) AS total_returned_qty,
    ROUND(CAST(SUM(COALESCE(r.returned_qty, 0)) AS DOUBLE) / NULLIF(SUM(s.gross_sales_qty), 0) * 100, 2) AS return_rate_pct,
    ROUND(SUM(s.gross_revenue) - SUM(COALESCE(r.refund_amount, 0)), 2) AS net_revenue
FROM sales_monthly s
INNER JOIN {{ ref('dim_products') }} p ON s.item_id = p.item_id
LEFT JOIN returns_monthly r 
    ON s.item_id = r.item_id 
    AND s.sales_year = r.return_year 
    AND s.sales_month = r.return_month
GROUP BY s.sales_year, s.sales_month, p.category, p.brand
```
* **Đặc điểm**: Kết nối 4 bảng độc lập qua CTEs: `fct_sales_clean` (Bán hàng), `fct_returns_unified` (Trả hàng), `dim_date` (Thời gian) và `dim_products` (Sản phẩm).

---

### 6.4. Khai Báo Data Tests Chất Lượng Dữ Liệu
File: `models/schema.yml`
```yaml
version: 2

models:
  - name: fct_sales_clean
    description: "Tầng Silver: Dữ liệu bán hàng đã làm sạch và khử null"
    columns:
      - name: order_id
        tests:
          - not_null
      - name: net_revenue
        tests:
          - not_null

  - name: mart_omnichannel_performance
    description: "Tầng Gold: Hiệu suất bán hàng đa kênh Store vs Web vs Catalog"
    columns:
      - name: channel
        tests:
          - not_null
          - accepted_values:
              values: ['Store', 'Web', 'Catalog']
```

---

### 6.5. Kết Quả Mã SQL Sau Khi dbt Biên Dịch (Compiled SQL)
File: `target/run/.../mart_product_return_rates.sql`
```sql
create table "iceberg_stg"."stg_gold"."mart_product_return_rates"
as (
    WITH sales_monthly AS (
        SELECT 
            s.item_id, s.sales_year, s.sales_month,
            SUM(s.quantity) AS gross_sales_qty
        FROM "iceberg_stg"."stg_silver"."fct_sales_clean" s
        GROUP BY s.item_id, s.sales_year, s.sales_month
    )
    ...
)
```
* **Minh chứng**: dbt tự động biên dịch `{{ ref(...) }}` thành đường dẫn bảng vật lý và tự động sinh câu lệnh `CREATE TABLE ... AS` để gửi sang Trino.
