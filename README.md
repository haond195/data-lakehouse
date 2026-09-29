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
[TẦNG GOLD:   retail_gold / stg_gold] ── Chiến lược: UPSERT / AGGREGATION (7 Data Marts cho BI/AI)
```

### 3.1. Phân tầng Medallion chuẩn hóa bằng dbt-trino (34 Models & 9 Data Tests)

Dự án triển khai quy trình ETL & Data Transformation chuẩn hóa toàn diện qua **dbt-trino** với **34 models** bao phủ 4 phân hệ TPC-DS SF1:

1. **🛍️ Phân hệ Bán hàng & Doanh thu (Retail Sales):**
   * **Bronze:** `stg_store_sales` (~2.88M dòng).
   * **Silver:** `fct_sales_clean`, `dim_stores`, `dim_date`.
   * **Gold:** `mart_store_sales_kpis`, `mart_product_category_kpis`.

2. **📦 Phân hệ Chuỗi cung ứng & Kho - Kệ (Supply Chain & Inventory):**
   * **Bronze:** `stg_inventory` (11.7M dòng), `stg_warehouse`.
   * **Silver:** `fct_inventory_balance`, `dim_warehouses`.
   * **Gold:** `mart_inventory_health`, `mart_inventory_sales_velocity` (**MỚI - Đa bảng:** Kết hợp Sales + Inventory + Products để đo tỷ lệ tồn/bán & cảnh báo cạn kho).

3. **🌐 Phân hệ Bán lẻ Đa kênh (Omnichannel: Store + Web + Catalog):**
   * **Bronze:** `stg_web_sales`, `stg_catalog_sales`, `stg_store_returns`, `stg_web_returns`, `stg_catalog_returns`, `stg_reason`.
   * **Silver:** `fct_web_sales_clean`, `fct_catalog_sales_clean`, `fct_returns_unified` (Hợp nhất trả hàng 3 kênh).
   * **Gold:** `mart_omnichannel_performance` (Đối soát 3 kênh), `mart_product_return_rates` (**MỚI - Đa bảng:** Kết hợp Sales + Returns + Products + Date để đo tỷ lệ trả hàng và thất thoát doanh thu).

4. **🎯 Phân hệ Khách hàng 360 & Khuyến mãi (Customer 360 & SCD Type 2):**
   * **Bronze:** `stg_customer`, `stg_customer_address`, `stg_customer_demographics`, `stg_promotion`.
   * **Silver:** `dim_customers` (Hỗ trợ SCD Type 2 lưu vết lịch sử địa chỉ/thu nhập), `dim_products`.
   * **Gold:** `mart_customer_segmentation` (Phân khúc giá trị khách hàng và độ nhạy khuyến mãi).

---

## 📊 4. Lớp Ngữ nghĩa & Bộ chỉ số Kinh doanh (Semantic Layer & Multi-table KPIs)

### 4.1. Bảng định nghĩa công thức chỉ số đa bảng (Cross-Table / Multi-Domain Metrics):
| Chỉ số (KPI) | Bảng nguồn liên kết | Công thức tính toán | Ý nghĩa kinh doanh |
| :--- | :--- | :--- | :--- |
| **Tỷ lệ hoàn trả hàng (Return Rate %)** | `fct_sales_clean` + `fct_returns_unified` + `dim_products` | `ROUND(returned_qty / NULLIF(sold_qty, 0) * 100, 2)` | Đo lường tỷ lệ hàng trả theo từng ngành hàng để phát hiện lỗi chất lượng sản phẩm. |
| **Doanh thu thuần sau trả hàng** | `fct_sales_clean` + `fct_returns_unified` | `ROUND(gross_revenue - refund_amount, 2)` | Doanh thu thực tế sau khi đã trừ hoàn tiền cho khách trả hàng. |
| **Tỷ lệ tồn kho / bán ra (Stock-to-Sales)** | `fct_sales_clean` + `fct_inventory_balance` | `ROUND(stock_on_hand / NULLIF(monthly_sold_qty, 0), 2)` | Đo lường mức độ dự trữ hàng hóa so với tốc độ tiêu thụ thực tế. |
| **Số ngày dự trữ tồn kho (Days of Supply)** | `fct_sales_clean` + `fct_inventory_balance` | `ROUND(stock_to_sales_ratio * 30, 1)` | Dự báo số ngày còn hàng; cảnh báo thiếu hàng (`< 15 ngày`) hoặc ứ đọng (`> 90 ngày`). |
| **Giá trị đơn hàng trung bình (AOV)** | `mart_omnichannel_performance` | `ROUND(total_revenue / NULLIF(total_orders, 0), 2)` | Giá trị mua sắm trung bình trên mỗi đơn hàng giữa Store, Web và Catalog. |
| **Biên lợi nhuận ròng (Margin %)** | `fct_sales_clean` | `ROUND(net_profit / NULLIF(net_revenue, 0) * 100, 2)` | Hiệu quả sinh lời của sản phẩm và kênh bán hàng. |

---

## 🤖 5. Trợ lý Phân tích AI & Cơ chế Đồng bộ Superset (AI Chatbot & SSO)

Ứng dụng Streamlit được tích hợp sâu vào hệ thống với các tính năng:

1. **Đồng bộ Đăng nhập Một lần (Single Sign-On - SSO):**
   - Nhúng thanh trượt AI Chatbot Drawer trực tiếp trên giao diện Superset qua `tail_js_custom_extra.html`.
   - Tự động gọi API `/api/v1/me/` của Superset để nhận diện danh tính người dùng (`admin` hoặc `analyst`) mà không cần đăng nhập lại.
2. **Chế độ Khóa cứng Bảo mật (Strict Mode):**
   - Khi chạy nhúng trong Superset, Chatbot tự động ẩn nút Đăng xuất và khóa cứng danh tính theo phiên Superset, ngăn chặn tự ý đổi tài khoản hoặc leo quyền.
3. **Phân quyền dữ liệu Zero Trust (Trino RBAC):**
   - Cấu hình qua `trino-security/rules.json`:
     - **`admin`**: Toàn quyền DDL/DML trên mọi Catalog (`iceberg`, `iceberg_stg`, `tpcds`) và mọi tầng dữ liệu.
     - **`analyst`**: Chỉ đọc (`SELECT`) trên các schema Gold (`retail_gold`, `stg_gold`); **bị chặn triệt để** khi truy cập tầng Bronze và Silver (`iceberg.*`).
4. **Bộ chọn Nguồn dữ liệu Động (Dynamic Catalog & Schema):**
   - Trực tiếp chọn Catalog (`iceberg_stg`, `iceberg`, `tpcds`) và Schema ngay trên đầu trang.
   - Dynamic Schema Injection: Quét cấu trúc bảng và cột thời gian thực nạp vào System Prompt cho LLM.
5. **Động cơ kép & Tự động trực quan hóa (Auto Chart):**
   - Hỗ trợ FPT AI DeepSeek-V4-Flash và Google Gemini. Tự động nhận diện dữ liệu kết quả để vẽ biểu đồ Cột, Đường hoặc Tròn.

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

# 6. Chạy chuẩn hóa 34 Models dbt-trino (Bronze, Silver, 7 Gold Marts)
python scripts/run_dbt.py

# 7. Kiểm thử trực quan SCD Type 1, Type 2, Type 3
python scripts/test_scd_visual.py
```

### 6.3. Bảng điều khiển dịch vụ & Thông tin đăng nhập

| Dịch vụ / Công cụ | Địa chỉ Web (URL) | Tài khoản / Mật khẩu | Quyền hạn & Vai trò |
| :--- | :--- | :--- | :--- |
| **Apache Superset** | http://localhost:8089 | admin / admin | **Admin:** Toàn quyền quản trị; Chatbot mở toàn quyền Lakehouse |
| **Apache Superset** | http://localhost:8089 | analyst / analyst123 | **Analyst:** Xem Dashboard; Chatbot tự khóa chỉ đọc tầng Gold |
| **Trino CLI / JDBC** | localhost:8080 | User: admin | Toàn quyền DDL, DML trên toàn bộ các Catalog |
| **Trino CLI / JDBC** | localhost:8080 | User: analyst | **Chỉ đọc (SELECT)** trên tầng Gold, **CẤM** tầng Bronze/Silver |
| **AI Data Assistant** | http://localhost:8501 | Tự đồng bộ SSO qua Superset | Chatbot Text-to-SQL + Auto Chart (Strict Mode) |
| **Trino Web UI** | http://localhost:8080 | Username: admin | Giám sát query phân tán thời gian thực |
| **MinIO Console** | http://localhost:9001 | admin / password123 | Quản trị S3 Bucket warehouse & iceberg_stg |
| **PostgreSQL Catalog**| localhost:5433 | User: postgres | DB: metastore / superset | Siêu dữ liệu Iceberg JDBC & Superset |

---

## 📁 7. Cấu trúc Thư mục Dự án

```text
D:\local-lakehouse\
├── dbt_lakehouse\               # Dự án dbt-trino chuẩn công nghiệp (34 Models, Lineage, Tests)
│   ├── dbt_project.yml         # Cấu hình dự án dbt Medallion
│   ├── profiles.yml            # Kết nối Trino Iceberg Engine (target stg & dev)
│   └── models/
│       ├── bronze/             # 17 Staging models nén dữ liệu từ nguồn TPC-DS SF1
│       ├── silver/             # 10 Dimensions & Clean Facts (fct_returns_unified, fct_inventory_balance,...)
│       └── gold/               # 7 Data Marts (mart_product_return_rates, mart_inventory_sales_velocity,...)
├── docs\
│   └── SCD_GUIDE.md            # Cẩm nang kiến thức & Hướng dẫn kiểm thử trực quan SCD Type 1, 2, 3
├── config\
│   ├── etl_pipeline.yaml           # Cấu hình ETL Bán hàng mẫu
│   └── inventory_pipeline.yaml     # Cấu hình ETL Tồn kho mẫu
├── chatbot\
│   └── app.py                      # Ứng dụng Streamlit AI Chatbot (SSO, Strict Mode, Dynamic Catalog/Schema)
├── scripts\
│   ├── run_dbt.py                  # Runner thực thi dbt run & dbt test tự động
│   ├── test_scd_visual.py          # Script kiểm thử trực quan luồng SCD Type 1, Type 2, Type 3
│   ├── dynamic_etl_runner.py       # Engine thực thi ETL động từ file YAML
│   ├── etl_tpcds_sf1.py            # Pipeline ETL Bán lẻ cơ bản
│   ├── etl_supply_chain_inventory.py # Pipeline ETL Tồn kho & Kho - Kệ
│   ├── etl_promo_customer360.py    # Pipeline ETL Khuyến mãi & Khách hàng 360
│   └── etl_omnichannel_logistics.py # Pipeline ETL Đa kênh & Đổi trả
├── trino-catalog\
│   ├── iceberg.properties          # Catalog Iceberg chính (MinIO S3 + Postgres JDBC)
│   ├── iceberg_stg.properties      # Catalog Iceberg Stage/Dev (MinIO S3 + Postgres HMS)
│   └── tpcds.properties            # Connector phát sinh dữ liệu chuẩn TPC-DS SF1
├── trino-security\
│   └── rules.json                  # Quy tắc phân quyền Trino RBAC (Zero Trust cho analyst & admin)
├── docker-compose.yml              # File triển khai toàn bộ hạ tầng containerized microservices
├── tail_js_custom_extra.html       # JavaScript nhúng Superset SSO Drawer & xác thực /api/v1/me/
├── superset_config.py              # Cấu hình bảo mật Superset & CORS
├── superset_init_db.py             # Script tự động đăng ký kết nối Trino vào Superset khi khởi động
├── ARCHITECTURE_DIAGRAM.html       # Sơ đồ kiến trúc tương tác trực quan bằng HTML/Tailwind
├── ARCHITECTURE_AND_BUSINESS_GUIDE.md # Tài liệu đặc tả kỹ thuật & nghiệp vụ chi tiết
└── README.md                       # Tài liệu tổng quan dự án (File này)
```

---

## ⚖️ 8. Đánh giá Hệ thống: Điểm Hoàn thành & Phạm vi Chưa triển khai

### 8.1. Những điểm nổi bật đã làm được:
1. **Kiến trúc Modern Lakehouse chuẩn công nghiệp:** Phân tách hoàn toàn Compute (Trino) và Storage (MinIO S3 / Apache Iceberg v2).
2. **Bao phủ 100% 4 phân hệ dữ liệu TPC-DS:** Bán lẻ (Sales), Chuỗi cung ứng kho - kệ (Supply Chain & Inventory), Đa kênh (Store/Web/Catalog) và Tiếp thị (Promotions & Customer 360).
3. **Mô hình Config-driven ETL:** Cho phép cắm thêm bộ dữ liệu mới chỉ bằng 1 file cấu hình YAML (dynamic_etl_runner.py).
4. **Bộ chỉ số phân tích nghiệp vụ thực tế (Semantic KPIs):** Đóng gói công thức AOV, DSI (Số ngày tồn kho), Vòng quay tồn kho, Tỷ trọng kênh, ROI khuyến mãi.
5. **Cơ chế Phân quyền RBAC nội bộ:** File-based Access Control trong Trino (admin toàn quyền, analyst chỉ đọc tầng Gold, chặn truy cập Bronze/Silver) và Superset User Roles.
6. **Trợ lý AI Text-to-SQL Động cơ kép:** Nhận diện thời gian thực toàn bộ các bảng Gold Marts, hỗ trợ CTE WITH phức tạp và tự động vẽ biểu đồ.

---

### 8.2. Những điểm chưa đưa vào hệ thống & Giải thích lý do:
1. **Luồng dữ liệu thời gian thực (Real-time Streaming qua Kafka / Flink):**
   * *Giải thích:* TPC-DS là bộ dữ liệu quá khứ/tĩnh phục vụ phân tích xu hướng và báo cáo quản trị. 95% báo cáo kinh doanh của doanh nghiệp chỉ cần chạy theo mẻ (Batch ETL hàng đêm hoặc hàng giờ). Bật Kafka + Spark Streaming 24/7 chỉ làm lãng phí 2–3 GB RAM máy chủ mà không mang lại giá trị phân tích vượt trội cho dữ liệu tĩnh.
2. **Công cụ điều phối luồng tập trung (Apache Airflow / Prefect):**
   * *Giải thích:* Hệ thống đã có engine Config-driven YAML và các script ETL độc lập, dễ dàng chạy qua cronjob. Cài thêm Apache Airflow đòi hỏi 4 container phụ trợ tốn thêm 2.5 GB RAM, không tối ưu cho môi trường chạy cục bộ (Local).
3. **Bộ kiểm định chất lượng dữ liệu độc lập (Great Expectations / Soda):**
   * *Giải thích:* Các quy tắc kiểm tra toàn vẹn, loại bỏ bản ghi lỗi (WHERE raw_net_paid IS NOT NULL AND raw_quantity > 0), khử NULL (COALESCE), và chống chia cho 0 (NULLIF) đã được nhúng trực tiếp vào các câu lệnh SQL ở tầng Silver và Gold.
4. **Triển khai cụm phân tán đa node (Kubernetes Cluster):**
   * *Giải thích:* Dự án được tối ưu để chạy khép kín trên Docker Compose trên một máy trạm duy nhất nhằm phục vụ kiểm thử, nghiệm thu đồ án và demo PoC mà không phát sinh chi phí hạ tầng Cloud.
