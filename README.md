# 🏛️ MODERN DATA LAKEHOUSE & AI BUSINESS INTELLIGENCE PLATFORM
### *Đồ án / Dự án Nền tảng Dữ liệu Lớn & Trợ lý Phân tích AI Doanh nghiệp*

[![Docker](https://img.shields.io/badge/Docker-Containerized-blue?logo=docker)](https://www.docker.com/)
[![Trino](https://img.shields.io/badge/Trino-482_Distributed_SQL-orange?logo=trino)](https://trino.io/)
[![Apache Iceberg](https://img.shields.io/badge/Apache_Iceberg-v2_Table_Format-blue?logo=apache)](https://iceberg.apache.org/)
[![MinIO](https://img.shields.io/badge/MinIO-S3_Object_Storage-red?logo=minio)](https://min.io/)
[![Apache Superset](https://img.shields.io/badge/Apache_Superset-3.1.0_BI-brightgreen?logo=apache-superset)](https://superset.apache.org/)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek--V4--Flash-purple)](https://fptcloud.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-AI_Assistant-ff4b4b?logo=streamlit)](https://streamlit.io/)

---

## 📖 1. Giới thiệu dự án (Introduction)

Dự án này được thiết kế và triển khai nhằm xây dựng một hệ thống **Modern Data Lakehouse** hoàn chỉnh phục vụ bài toán quản trị và phân tích dữ liệu bán lẻ đa kênh (**Omnichannel Retail**). Hệ thống kết hợp giữa tính linh hoạt, chi phí thấp của **Data Lake** và khả năng quản lý giao dịch ACID, hiệu năng cao của **Data Warehouse**, đồng thời tích hợp trực tiếp **Trợ lý AI Text-to-SQL thế hệ mới (GenAI)** để tự động hóa phân tích dữ liệu kinh doanh.

* **MinIO:** Đóng vai trò là hệ thống lưu trữ đối tượng phân tán (Object Storage giả lập AWS S3), lưu trữ dữ liệu dưới định dạng Apache Parquet nén tối ưu.
* **Apache Iceberg:** Cung cấp định dạng bảng hiện đại (Table Format) hỗ trợ đầy đủ ACID transactions, Time Travel, Schema Evolution và tối ưu hiệu năng phân vùng ẩn (Hidden Partitioning).
* **Trino Engine:** Động cơ xử lý phân tán trong bộ nhớ (Distributed In-Memory SQL Engine), thực thi các truy vấn tương tác cực nhanh (< 0.3s) trên hàng triệu bản ghi.
* **Apache Superset:** Nền tảng BI trực quan hóa biểu đồ (Data Visualization & Dashboards), tích hợp sẵn thanh trượt AI Chatbot Drawer toàn cục.
* **AI Text-to-SQL Assistant:** Ứng dụng Streamlit sử dụng mô hình ngôn ngữ lớn (**DeepSeek-V4-Flash / Google Gemini**) cùng cơ chế động cơ kép (Dual Engine) cho phép người dùng hỏi đáp dữ liệu bằng tiếng Việt tự nhiên và tự động vẽ biểu đồ trực tiếp.

---

## 🏛️ 2. Sơ đồ Kiến trúc Hệ thống (Lakehouse Architecture)

Hệ thống được thiết kế theo mô hình 4 tầng phân tách độc lập (Decoupled Compute & Storage Architecture):

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

> 🌐 **Xem sơ đồ giao diện tương tác trực tiếp:** Mở file [`ARCHITECTURE_DIAGRAM.html`](./ARCHITECTURE_DIAGRAM.html) bằng trình duyệt web.

---

## 🧱 3. Kiến trúc Dữ liệu Medallion & Chiến lược Ghi (Write Strategy)

Hệ thống tổ chức dữ liệu theo chuẩn công nghiệp **Medallion Architecture (Bronze ➔ Silver ➔ Gold)**:

```
[Nguồn: TPC-DS SF1] 
       │ 
       ▼ (1. Ingestion thô)
[TẦNG BRONZE: retail_bronze] ── Chiến lược: APPEND (Lưu nguyên trạng + _ingested_at)
       │ 
       ▼ (2. Clean & Deduplicate)
[TẦNG SILVER: retail_silver] ── Chiến lược: OVERWRITE / CLEAN (Khử NULL bằng COALESCE)
       │ 
       ▼ (3. Pre-aggregate KPIs)
[TẦNG GOLD:   retail_gold]   ── Chiến lược: UPSERT / AGGREGATION (Data Marts cho BI/AI)
```

### 3.1. Phân tầng Medallion hoàn chỉnh 4 phân hệ nghiệp vụ

1. **🛍️ Phân hệ Bán hàng & Doanh thu (Retail Sales):**
   * **Bronze:** `store_sales_raw` (100.000 dòng).
   * **Silver:** `sales_transactions` (92.276 dòng) — Lọc dữ liệu rác, khử NULL bằng `COALESCE`, liên kết Dimension.
   * **Gold:** `mart_monthly_store_performance` (4.133 dòng), `store_performance_daily` (7 dòng).

2. **📦 Phân hệ Chuỗi cung ứng & Kho - Kệ (Supply Chain & Inventory):**
   * **Bronze:** `inventory_raw` (150.000 dòng), `warehouse_raw` (5 dòng).
   * **Silver:** `inventory_snapshot` (142.546 dòng), `dim_warehouse` (5 dòng).
   * **Gold:** `mart_inventory_turnover` (Vòng quay kho so với kệ), `mart_warehouse_utilization` (Mật độ lưu trữ).

3. **🌐 Phân hệ Bán lẻ Đa kênh (Omnichannel: Store + Web + Catalog):**
   * **Bronze:** `web_sales_raw` (50.000 dòng), `catalog_sales_raw` (50.000 dòng), `store_returns_raw` (25.000 dòng).
   * **Silver:** `omnichannel_sales_transactions` (**191.790 dòng** hợp nhất cả 3 kênh bán hàng), `returns_transactions`.
   * **Gold:** `mart_omnichannel_performance` (Đối soát doanh thu 3 kênh), `mart_returns_analysis` (Phân tích lý do đổi trả).

4. **🎯 Phân hệ Khuyến mãi & Khách hàng 360 (Promotions & Customer 360):**
   * **Bronze:** `promotion_raw` (300 dòng), `customer_raw` (100.000 dòng), `customer_demographics_raw` (1.92M dòng).
   * **Silver:** `dim_promotion` (300 dòng), `dim_customer_360` (100.000 dòng).
   * **Gold:** `mart_promotion_sales_performance` (Doanh số theo campaign), `mart_customer_segmentation` (12.079 phân khúc).

---

## 📊 4. Lớp Ngữ nghĩa & Bộ chỉ số Kinh doanh (Semantic Layer & KPIs)

Toàn bộ công thức tính toán tài chính được đóng gói tại View ngữ nghĩa trung tâm:  
`iceberg.retail_gold.semantic_sales_mart`

### 4.1. Bảng định nghĩa công thức chỉ số (KPIs):
| Chỉ số (KPI) | Tên cột / Công thức SQL | Ý nghĩa kinh doanh |
| :--- | :--- | :--- |
| **Doanh thu thuần** | `ROUND(SUM(net_revenue), 2)` | Doanh thu thực nhận sau khi đã trừ giảm giá và chiết khấu. |
| **Doanh thu gộp** | `ROUND(SUM(gross_revenue), 2)` | Doanh thu tính theo giá niêm yết ban đầu (`list_price * quantity`). |
| **Lợi nhuận thuần** | `ROUND(SUM(net_profit), 2)` | Lợi nhuận ròng sau khi trừ giá vốn hàng bán và chi phí trực tiếp. |
| **Biên lợi nhuận %**| `ROUND((SUM(net_profit) / NULLIF(SUM(net_revenue), 0)) * 100, 2)` | Tỷ suất sinh lời (`Profit Margin %`) của từng danh mục và cửa hàng. |
| **Tổng số đơn hàng**| `COUNT(DISTINCT order_id)` | Lượng đơn hàng phát sinh thực tế (loại bỏ trùng lặp mã đơn). |
| **Vòng quay kho/kệ**| `ROUND(units_sold_on_shelf / NULLIF(total_warehouse_stock, 0), 4)` | Tốc độ tiêu thụ hàng hóa trên kệ so với lượng tồn kho. |

---

## 🤖 5. Trợ lý Phân tích AI Đa nền tảng (Dual-Engine AI Chatbot)

Ứng dụng Streamlit được tích hợp sâu vào hệ thống với cơ chế **Dual Engine**:

1. **Cloud LLM Engine (DeepSeek-V4-Flash / Google Gemini):**
   * Đọc schema thực tế của Lakehouse và tự động dịch câu hỏi ngôn ngữ tự nhiên thành cú pháp Trino SQL chuẩn xác.
   * Tự động quét và hỗ trợ toàn bộ **9 bảng Gold Data Marts**.
2. **Smart Rule Parser (Chế độ dự phòng nội bộ):**
   * Tự động kích hoạt khi mất kết nối mạng hoặc không có API Key, đảm bảo hệ thống không bao giờ bị gián đoạn hoạt động.
3. **Bộ lọc làm sạch SQL (`clean_generated_sql`):**
   * Hỗ trợ đầy đủ cú pháp CTE (`WITH ... AS (...)`) và lệnh `SELECT`, loại bỏ ký tự thừa và dấu chấm phẩy `;` cuối dòng.

---

## 🚀 6. Hướng dẫn Triển khai & Vận hành (Quick Start)

### 6.1. Khởi động hạ tầng Docker
```powershell
# Di chuyển vào thư mục dự án
cd D:\local-lakehouse

# Khởi động toàn bộ cụm dịch vụ (MinIO, Postgres, HMS, Trino, Superset, Chatbot)
docker compose up -d
```

### 6.2. Thực thi các Pipeline ETL Medallion
```powershell
# 1. Pipeline Bán lẻ cơ bản (TPC-DS Store Sales)
python scripts/etl_tpcds_sf1.py

# 2. Pipeline Chuỗi cung ứng, Tồn kho & Đối soát Kho - Kệ
python scripts/etl_supply_chain_inventory.py

# 3. Pipeline Khuyến mãi & Khách hàng 360 độ
python scripts/etl_promo_customer360.py

# 4. Pipeline Đa kênh (Store, Web, Catalog) & Giao vận, Đổi trả
python scripts/etl_omnichannel_logistics.py

# 5. Config-driven ETL linh hoạt qua file YAML
python scripts/dynamic_etl_runner.py config/etl_pipeline.yaml
```

### 6.3. Bảng điều khiển dịch vụ & Thông tin đăng nhập

| Dịch vụ | Địa chỉ Web (URL) | Tài khoản / Thông tin | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Apache Superset** | `http://localhost:8089` | `admin` / `admin` | Đã liên kết sẵn Trino & Data Marts |
| **AI Data Assistant** | `http://localhost:8501` | Mở trực tiếp hoặc icon `🤖` trên Superset | Text-to-SQL + Auto Chart |
| **Trino Web UI** | `http://localhost:8080` | Username: `admin` | Giám sát query phân tán |
| **MinIO Console** | `http://localhost:9001` | `admin` / `password123` | Quản trị S3 Bucket `warehouse` |
| **PostgreSQL Catalog**| `localhost:5433` | User: `postgres` \| DB: `metastore` | Siêu dữ liệu Iceberg JDBC |

---

## 📁 7. Cấu trúc Thư mục Dự án

```text
D:\local-lakehouse\
├── config\
│   ├── etl_pipeline.yaml           # Cấu hình ETL Bán hàng mẫu
│   └── inventory_pipeline.yaml     # Cấu hình ETL Tồn kho mẫu
├── chatbot\
│   └── app.py                      # Ứng dụng Streamlit Text-to-SQL nhận diện 9 Gold Marts
├── scripts\
│   ├── dynamic_etl_runner.py       # Engine thực thi ETL động từ YAML
│   ├── etl_tpcds_sf1.py            # Pipeline ETL Bán lẻ cơ bản
│   ├── etl_supply_chain_inventory.py # Pipeline ETL Tồn kho & Kho - Kệ
│   ├── etl_promo_customer360.py    # Pipeline ETL Khuyến mãi & Khách hàng 360
│   ├── etl_omnichannel_logistics.py # Pipeline ETL Đa kênh & Đổi trả
│   └── run_etl.py                  # Script ETL mẫu cho môi trường cục bộ
├── trino-catalog\
│   ├── iceberg.properties          # Cấu hình Iceberg Catalog (MinIO S3 + Postgres JDBC)
│   ├── lakehouse.properties        # Cấu hình Hive Catalog (MinIO S3 + Hive Metastore)
│   └── tpcds.properties            # Cấu hình TPC-DS Data Generator Connector
├── docker-compose.yml              # File triển khai toàn bộ 6 microservices
├── superset_config.py              # Cấu hình bảo mật Superset & tắt bộ lọc HTML
├── superset_init_db.py             # Script tự động đăng ký kết nối Trino vào Superset khi khởi động
├── ARCHITECTURE_DIAGRAM.html       # Sơ đồ kiến trúc tương tác trực quan bằng HTML/Tailwind
├── ARCHITECTURE_AND_BUSINESS_GUIDE.md # Tài liệu đặc tả kỹ thuật & nghiệp vụ chi tiết
└── README.md                       # Tài liệu tổng quan dự án (File này)
```
