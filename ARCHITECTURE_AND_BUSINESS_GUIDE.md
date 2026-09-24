# TÀI LIỆU TOÀN DIỆN: NGHIỆP VỤ & KỸ THUẬT HỆ THỐNG DATA LAKEHOUSE & AI BI PLATFORM

> **Dự án:** Modern Data Lakehouse & BI Platform (Local Enterprise Architecture)  
> **Thư mục dự án:** `D:\local-lakehouse`  
> **Ngày cập nhật:** 21/09/2026  
> **Trạng thái:** Toàn bộ dịch vụ đang hoạt động (Production Ready - Local Mode)

---

## MỤC LỤC
1. [TỔNG QUAN NGHIỆP VỤ (BUSINESS SPECIFICATION)](#1-tổng-quan-nghiệp-vụ-business-specification)
2. [KIẾN TRÚC KỸ THUẬT HỆ THỐNG (TECHNICAL ARCHITECTURE)](#2-kiến-trúc-kỹ-thuật-hệ-thống-technical-architecture)
3. [MÔ HÌNH DỮ LIỆU & QUY TRÌNH ETL MEDALLION](#3-mô-hình-dữ-liệu--quy-trình-etl-medallion)
4. [LỚP NGHIỆP VỤ NGỮ NGHĨA (SEMANTIC LAYER & KPIS)](#4-lớp-nghiệp-vụ-ngữ-nghĩa-semantic-layer--kpis)
5. [HỆ THỐNG AI TEXT-TO-SQL & TRỢ LÝ PHÂN TÍCH](#5-hệ-thống-ai-text-to-sql--trợ-lý-phân-tích)
6. [HƯỚNG DẪN VẬN HÀNH & TRUY CẬP HỆ THỐNG](#6-hướng-dẫn-vận-hành--truy-cập-hệ-thống)

---

## 1. TỔNG QUAN NGHIỆP VỤ (BUSINESS SPECIFICATION)

### 1.1. Bối cảnh & Mục tiêu kinh doanh
Hệ thống giải quyết bài toán quản trị và phân tích dữ liệu bán lẻ đa kênh (Omnichannel Retail) cho doanh nghiệp quy mô lớn:
* **Hợp nhất dữ liệu đa kênh:** Đồng bộ giao dịch bán lẻ tại chuỗi cửa hàng vật lý (`store_sales`) và kênh thương mại điện tử (`web_sales`).
* **Rút ngắn thời gian ra quyết định:** Chuyển đổi từ mô hình báo cáo truyền thống (mất vài ngày viết SQL/Excel) sang **Hỏi - Đáp ngôn ngữ tự nhiên tức thì (AI Data Assistant)** và **Dashboard trực quan tự phục vụ (Self-service BI)**.
* **Chuẩn hóa công thức chỉ số:** Loại bỏ tình trạng mỗi phòng ban tính một kiểu; mọi chỉ số (Doanh thu, Chi phí, Lợi nhuận) đều được khóa cứng tại lớp ngữ nghĩa (**Semantic Layer**).

### 1.2. Định nghĩa các chỉ số đo lường cốt lõi (Business Metrics / KPIs)
1. **Doanh thu thuần (Net Revenue):**
   $$\text{Net Revenue} = \sum (\text{ss\_net\_paid})$$
   *Ý nghĩa:* Số tiền thực tế doanh nghiệp thu về từ khách hàng sau khi đã trừ toàn bộ mã giảm giá, chiết khấu và khuyến mãi.
2. **Doanh thu gộp (Gross Revenue):**
   $$\text{Gross Revenue} = \sum (\text{ss\_list\_price} \times \text{ss\_quantity})$$
   *Ý nghĩa:* Giá trị đơn hàng tính theo giá niêm yết ban đầu trước khi áp dụng chính sách giảm giá.
3. **Lợi nhuận thuần (Net Profit):**
   $$\text{Net Profit} = \sum (\text{ss\_net\_profit})$$
   *Ý nghĩa:* Lợi nhuận còn lại sau khi trừ giá vốn hàng bán (COGS) và chi phí bán hàng trực tiếp.
4. **Tỷ suất lợi nhuận (Profit Margin %):**
   $$\text{Profit Margin (\%)} = \left( \frac{\text{Net Profit}}{\text{Net Revenue}} \right) \times 100$$
   *Ý nghĩa:* Đánh giá hiệu quả sinh lời của từng chi nhánh, danh mục sản phẩm hoặc chiến dịch.
5. **Tổng số đơn hàng thành công (Total Orders):**
   $$\text{Total Orders} = \text{COUNT}(\text{DISTINCT } \text{order\_id})$$
   *Ý nghĩa:* Đo lường lượng giao dịch thực tế phát sinh (loại trừ trùng lặp mã đơn).

### 1.3. Chiều phân tích đa chiều (Dimensions)
* **Thời gian (Time):** Năm (`sales_year`), Tháng (`sales_month`), Ngày (`sales_date`), Ngày cuối tuần (`is_weekend`), Ngày lễ (`is_holiday`).
* **Địa lý & Chi nhánh (Store):** Mã cửa hàng (`store_id`), Tên cửa hàng (`store_name`), Thành phố (`store_city`), Tiểu bang (`store_state`).
* **Sản phẩm (Product):** Mã hàng (`product_id`), Tên hàng (`product_name`), Ngành hàng (`category`), Thương hiệu (`brand`).
* **Khách hàng (Customer):** Mã khách (`customer_id`), Quốc gia (`country`), Điểm tín dụng (`credit_rating`).

---

## 2. KIẾN TRÚC KỸ THUẬT HỆ THỐNG (TECHNICAL ARCHITECTURE)

Hệ thống được đóng gói hoàn toàn bằng Docker Compose, hoạt động khép kín trên ổ đĩa `D:\local-lakehouse`:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TẦNG TRÌNH DIỄN & TƯƠNG TÁC                     │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │   Apache Superset (BI)    │◄────►│   AI Chatbot (Streamlit)    │   │
│   │    (Cổng 8089)            │      │    (Cổng 8501 / Embedded)   │   │
│   └─────────────┬─────────────┘      └──────────────┬──────────────┘   │
└─────────────────┼───────────────────────────────────┼──────────────────┘
                  │ SQL Query                         │ Text-to-SQL
                  ▼                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      TẦNG TÍNH TOÁN (QUERY ENGINE)                     │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │               Trino Distributed SQL Engine 482                 │   │
│   │                         (Cổng 8080)                            │   │
│   └────────────────────────────────┬───────────────────────────────┘   │
└────────────────────────────────────┼───────────────────────────────────┘
                                     │ Quản lý Metadata & Đọc/Ghi Parquet
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      TẦNG LƯU TRỮ & METADATA LAKEHOUSE                 │
│   ┌───────────────────────────┐      ┌─────────────────────────────┐   │
│   │   PostgreSQL JDBC Catalog │      │    MinIO Object Storage     │   │
│   │   + Hive Metastore (HMS)  │      │     (Giả lập AWS S3)        │   │
│   │    (Cổng 5433 / 9083)     │      │     (Cổng 9000 / 9001)      │   │
│   └─────────────┬─────────────┘      └──────────────┬──────────────┘   │
│                 │                                   │                  │
│                 └─────────► Apache Iceberg ◄────────┘                  │
│                              Format Tables                             │
└────────────────────────────────────────────────────────────────────────┘
```

### Chi tiết vai trò từng thành phần:
1. **MinIO (S3 Storage - Cổng 9000/9001):** Lưu trữ đối tượng vật lý (Object Storage). Toàn bộ dữ liệu được lưu dưới dạng file Apache Parquet nén ZSTD/Snappy trong bucket `s3://warehouse/`.
2. **Apache Iceberg Table Format:** Quản lý cấu trúc bảng, ACID Transaction, Time Travel (truy vấn dữ liệu lịch sử theo snapshot), Schema Evolution (thêm/bớt cột không lỗi) và Hidden Partitioning.
3. **PostgreSQL Metastore (Cổng 5433:5432):** Lưu trữ bảng danh mục metadata của Iceberg JDBC Catalog (`iceberg_tables`, `iceberg_namespace_properties`).
4. **Trino Query Engine (Cổng 8080):** Phân tán truy vấn SQL cực nhanh bằng bộ nhớ RAM (In-Memory Vectorized Engine). Trino đóng vai trò điều phối chính giữa các Catalog: `iceberg`, `lakehouse`, `tpcds`.
5. **Apache Superset 3.1.0 (Cổng 8089):** Nền tảng trực quan hóa dữ liệu (Dashboard/Charts), tích hợp sẵn thanh AI Chatbot trượt (Sidebar Drawer) trên toàn bộ ứng dụng.
6. **AI Chatbot Streamlit (Cổng 8501):** Ứng dụng Text-to-SQL hai chế độ: LLM Cloud (DeepSeek/Gemini) và Bộ phân tích quy tắc thông minh (Smart Rule Parser).

---

## 3. MÔ HÌNH DỮ LIỆU & QUY TRÌNH ETL MEDALLION

Dữ liệu được xử lý qua 3 tầng chuẩn công nghiệp **Medallion Architecture**:

```
[Nguồn: TPC-DS SF1] 
       │ 
       ▼ (1. Extract thô nguyên bản)
[TẦNG BRONZE: retail_bronze] ── Lưu thô, bổ sung audit timestamp (_ingested_at)
       │ 
       ▼ (2. Clean, Type cast, COALESCE NULLs)
[TẦNG SILVER: retail_silver] ── Làm sạch, lọc giao dịch lỗi, khử giá trị NULL
       │ 
       ▼ (3. Pre-aggregate Business KPIs)
[TẦNG GOLD:   retail_gold]   ── Bảng Data Marts tính sẵn phục vụ Superset & AI
```

### 3.1. Tầng Bronze: `iceberg.retail_bronze`
* **Bảng chính:** `store_sales_raw` (100.000 dòng).
* **Nhiệm vụ:** Nạp dữ liệu thô nguyên bản từ nguồn, không can thiệp logic nghiệp vụ.
* **Cột Audit:** `_ingested_at TIMESTAMP` (thời điểm dữ liệu được nạp vào Lakehouse).

### 3.2. Tầng Silver: `iceberg.retail_silver`
* **Bảng chính:** `sales_transactions` (92.276 dòng).
* **Nhiệm vụ:** 
  * Lọc dữ liệu lỗi: `WHERE raw_net_paid IS NOT NULL AND raw_quantity > 0` (loại bỏ 7.724 dòng đơn hàng rác/âm).
  * Chuẩn hóa kiểu dữ liệu: Ép kiểu số thực `DOUBLE`, định dạng ngày `DATE`.
  * Khử `NULL` bằng nhãn có nghĩa: `COALESCE(store_name, 'Online / Non-Store')`, `COALESCE(category, 'Uncategorized')`.
* **Cột Audit:** `_transformed_at TIMESTAMP`.

### 3.3. Tầng Gold: `iceberg.retail_gold`
* **Bảng tổng hợp:** `mart_monthly_store_performance` (4.133 dòng).
* **Bảng tổng hợp ngày:** `store_performance_daily` (7 dòng).
* **Nhiệm vụ:** Gom nhóm sẵn theo Năm, Tháng, Chi nhánh, Ngành hàng; tính sẵn `total_orders`, `total_revenue`, `total_profit`, `profit_margin_pct`. Giúp Dashboard tải tức thì trong 0,1s.

---

## 4. LỚP NGHIỆP VỤ NGỮ NGHĨA (SEMANTIC LAYER & KPIS)

Lớp ngữ nghĩa được cài đặt bằng View phân quyền bảo mật trong Trino:
`iceberg.retail_gold.semantic_sales_mart`

### Mã nguồn định nghĩa Semantic View:
```sql
CREATE OR REPLACE VIEW iceberg.retail_gold.semantic_sales_mart AS
SELECT
  d.d_year AS sales_year,
  d.d_moy AS sales_month,
  d.d_date AS sales_date,
  d.d_day_name AS day_of_week,
  d.d_holiday AS is_holiday,
  i.i_item_sk AS product_id,
  COALESCE(i.i_item_desc, 'Unknown Product') AS product_name,
  COALESCE(i.i_category, 'Uncategorized') AS category,
  COALESCE(i.i_brand, 'No Brand') AS brand,
  s.ss_customer_sk AS customer_id,
  COALESCE(st.s_store_name, 'Online / Non-Store') AS store_name,
  COALESCE(st.s_city, 'Unknown City') AS store_city,
  COALESCE(st.s_state, 'Unknown State') AS store_state,
  s.ss_ticket_number AS order_id,
  COALESCE(s.ss_quantity, 0) AS quantity_sold,
  ROUND(COALESCE(s.ss_list_price * s.ss_quantity, 0.0), 2) AS gross_revenue,
  ROUND(COALESCE(s.ss_net_paid, 0.0), 2) AS net_revenue,
  ROUND(COALESCE(s.ss_net_paid - s.ss_net_profit, 0.0), 2) AS total_cost,
  ROUND(COALESCE(s.ss_net_profit, 0.0), 2) AS net_profit
FROM iceberg.retail_gold.store_sales s
INNER JOIN iceberg.retail_gold.item i ON (s.ss_item_sk = i.i_item_sk)
INNER JOIN iceberg.retail_gold.date_dim d ON (s.ss_sold_date_sk = d.d_date_sk)
LEFT JOIN iceberg.retail_gold.store st ON (s.ss_store_sk = st.s_store_sk);
```

---

## 5. HỆ THỐNG AI TEXT-TO-SQL & TRỢ LÝ PHÂN TÍCH

Hệ thống AI Chatbot hoạt động theo cơ chế **Dual Engine (Động cơ kép)**:

```
[Câu hỏi người dùng (Tiếng Việt / English)]
                     │
                     ▼
        ┌─────────────────────────┐
        │  Có API Key LLM không?  │
        └────────────┬────────────┘
          Có         │          Không
          ┌──────────┴──────────┐
          ▼                     ▼
┌───────────────────┐ ┌────────────────────────┐
│  Cloud LLM Engine │ │   Smart Rule Parser    │
│ (DeepSeek/Gemini) │ │ (Regex & Pattern Rule) │
└─────────┬─────────┘ └───────────┬────────────┘
          │                       │
          └───────────┬───────────┘
                      ▼
    [Bộ làm sạch câu lệnh: clean_generated_sql]
      * Trích xuất khối SELECT
      * Bỏ markdown & giải thích thừa
      * Xóa dấu chấm phẩy ; cuối dòng
                      ▼
    [Thực thi qua Trino DBAPI (iceberg.retail_gold)]
                      ▼
    [Hiển thị Bảng kết quả (Dataframe) + Biểu đồ tự động]
```

### Hai chế độ vận hành:
1. **Chế độ LLM Cao cấp (FPT AI Marketplace / DeepSeek-V4-Flash & Gemini):**
   * Tự động đọc lược đồ `semantic_sales_mart` và `customer_gold`.
   * Hỗ trợ mọi câu hỏi mở phức tạp (so sánh tháng, tính tỷ trọng %, lọc theo điều kiện ghép).
   * Đã tối ưu `timeout=75s` và giới hạn suy luận để phản hồi nhanh chóng (12–15s).
2. **Chế độ Smart Rule Parser (Dự phòng nội bộ):**
   * Không phụ thuộc internet hay API Key bên thứ ba.
   * Sử dụng thuật toán nhận diện từ khóa (Metrics: doanh thu, lợi nhuận, số lượng; Dimensions: cửa hàng, danh mục, thời gian; Sắp xếp: top, cao nhất, thấp nhất).

---

## 6. HƯỚNG DẪN VẬN HÀNH & TRUY CẬP HỆ THỐNG

### 6.1. Danh mục Cổng truy cập & Tài khoản

| Ứng dụng | Địa chỉ Web (URL) | Tài khoản / Thông tin | Chức năng |
| :--- | :--- | :--- | :--- |
| **Apache Superset** | `http://localhost:8089` | `admin` / `admin` | Dashboard BI & SQL Lab |
| **AI Chatbot** | `http://localhost:8501` | Trực tiếp không cần mật khẩu | Hỏi đáp Text-to-SQL |
| **Trino Web UI** | `http://localhost:8080` | User: `admin` | Theo dõi truy vấn & hiệu năng cụm |
| **MinIO Console** | `http://localhost:9001` | `admin` / `password123` | Quản lý S3 Object Storage |
| **PostgreSQL** | `localhost:5433` | User: `postgres`, DB: `metastore` | Lưu trữ siêu dữ liệu Catalog |

### 6.2. Các lệnh vận hành thường dùng (CLI PowerShell)

1. **Khởi động toàn bộ hệ thống:**
   ```powershell
   cd D:\local-lakehouse
   docker compose up -d
   ```
2. **Kiểm tra trạng thái các container:**
   ```powershell
   docker compose ps
   ```
3. **Chạy lại toàn trình ETL Medallion (TPC-DS SF1):**
   ```powershell
   python -X utf8 D:\local-lakehouse\scripts\etl_tpcds_sf1.py
   ```
4. **Khởi động lại riêng AI Chatbot:**
   ```powershell
   docker compose restart chatbot
   ```
5. **Dừng toàn bộ hệ thống:**
   ```powershell
   docker compose down
   ```
