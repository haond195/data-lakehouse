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

### 3.1. Phân tầng Medallion
* **🥉 Tầng Bronze (`iceberg.retail_bronze`):**
  * *Bản chất:* Nơi tiếp nhận dữ liệu thô đầu tiên từ các hệ thống nguồn (Raw Zone).
  * *Bảng mẫu:* `store_sales_raw` (100.000 dòng).
  * *Chiến lược:* **APPEND** — Dữ liệu mới được thêm liên tục vào cuối tập hợp, giữ nguyên cấu trúc thô, không sửa đổi logic và bổ sung mốc thời gian `_ingested_at` phục vụ kiểm toán (Data Audit).

* **🥈 Tầng Silver (`iceberg.retail_silver`):**
  * *Bản chất:* Dữ liệu sau khi trải qua quá trình lọc sạch (Data Cleansing), kiểm tra hợp lệ (Validation) và chuẩn hóa cấu trúc (Standardization).
  * *Bảng mẫu:* `sales_transactions` (92.276 dòng).
  * *Chiến lược:* **OVERWRITE / REFRESH** — Lọc sạch các giao dịch lỗi (`net_paid IS NOT NULL AND quantity > 0`), liên kết khóa ngoại với các Dimension (Date, Store, Item) và chuyển đổi các giá trị `NULL` thành các nhãn có nghĩa bằng `COALESCE`.

* **🥇 Tầng Gold (`iceberg.retail_gold`):**
  * *Bản chất:* Tầng tinh chế dữ liệu kinh doanh cuối cùng (Curated Business-level Marts).
  * *Bảng mẫu:* `mart_monthly_store_performance` (4.133 dòng), `store_performance_daily` (7 dòng).
  * *Chiến lược:* **UPSERT / AGGREGATION** — Tổng hợp sẵn các chỉ số KPI theo Tháng/Cửa hàng/Ngành hàng, giúp Dashboard trên Superset và câu truy vấn của AI Chatbot phản hồi tức thì trong **0,18 giây**.

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
| **Biên lợi nhuận %**| `ROUND((SUM(net_profit) / SUM(net_revenue)) * 100, 2)` | Tỷ suất sinh lời (`Profit Margin %`) của từng danh mục và cửa hàng. |
| **Tổng số đơn hàng**| `COUNT(DISTINCT order_id)` | Lượng đơn hàng phát sinh thực tế (loại bỏ trùng lặp mã đơn). |
| **Số lượng bán ra** | `SUM(quantity_sold)` | Tổng số đơn vị sản phẩm tiêu thụ. |

---

## 🤖 5. Trợ lý Phân tích AI Đa nền tảng (Dual-Engine AI Chatbot)

Ứng dụng Streamlit được tích hợp sâu vào hệ thống với cơ chế **Dual Engine**:

1. **Cloud LLM Engine (DeepSeek-V4-Flash / Google Gemini):**
   * Đọc schema thực tế của Lakehouse và tự động dịch câu hỏi ngôn ngữ tự nhiên (tiếng Việt/tiếng Anh) thành cú pháp Trino SQL chuẩn xác.
   * Tối ưu hóa thời gian suy luận: Rút gọn prompt, cấu hình `max_tokens=1000` và nâng `timeout=75s` giúp trả lời câu hỏi phức tạp chỉ sau **12–15 giây**.
2. **Smart Rule Parser (Chế độ dự phòng nội bộ):**
   * Tự động kích hoạt khi mất kết nối mạng hoặc không có API Key, đảm bảo hệ thống không bao giờ bị gián đoạn hoạt động.
3. **Bộ lọc làm sạch SQL (`clean_generated_sql`):**
   * Tự động trích xuất khối lệnh `SELECT`, loại bỏ văn bản markdown thừa và cắt bỏ dấu chấm phẩy `;` cuối dòng để đảm bảo Trino DBAPI thực thi không lỗi.

---

## 🚀 6. Hướng dẫn Triển khai & Vận hành (Quick Start)

### 6.1. Khởi động hạ tầng Docker
```powershell
# Di chuyển vào thư mục dự án
cd D:\local-lakehouse

# Khởi động toàn bộ cụm dịch vụ (MinIO, Postgres, HMS, Trino, Superset, Chatbot)
docker compose up -d
```

### 6.2. Chạy Pipeline ETL dữ liệu TPC-DS SF1
```powershell
python -X utf8 D:\local-lakehouse\scripts\etl_tpcds_sf1.py
```
*Kết quả:* Nạp và biến đổi thành công **100.000 dòng Bronze** ➔ **92.276 dòng Silver** ➔ **4.133 dòng Gold KPIs** trong **5,01 giây**.

### 6.3. Chạy Config-driven ETL (Tự động hóa với YAML)
```powershell
python scripts/dynamic_etl_runner.py config/etl_pipeline.yaml
```
*Ưu điểm:* Khi có dữ liệu mới, chỉ cần tạo file YAML mô tả cột và quy tắc chuyển đổi mà không cần sửa code Python.

### 6.4. Bảng điều khiển dịch vụ & Thông tin đăng nhập

| Dịch vụ | Địa chỉ Web (URL) | Tài khoản / Thông tin | Ghi chú |
| :--- | :--- | :--- | :--- |
| **Apache Superset** | `http://localhost:8089` | `admin` / `admin` | Đã liên kết sẵn Trino & 4 Datasets |
| **AI Data Assistant** | `http://localhost:8501` | Mở trực tiếp hoặc icon `🤖` trên Superset | Text-to-SQL + Auto Chart |
| **Trino Web UI** | `http://localhost:8080` | Username: `admin` | Giám sát query phân tán |
| **MinIO Console** | `http://localhost:9001` | `admin` / `password123` | Quản trị S3 Bucket `warehouse` |
| **PostgreSQL Catalog**| `localhost:5433` | User: `postgres` \| DB: `metastore` | Siêu dữ liệu Iceberg JDBC |

---

## 📁 7. Cấu trúc Thư mục Dự án

```text
D:\local-lakehouse\
├── config\
│   └── etl_pipeline.yaml           # Cấu hình mẫu cho Config-driven ETL
├── chatbot\
│   └── app.py                      # Ứng dụng Streamlit Text-to-SQL tích hợp DeepSeek & Gemini
├── scripts\
│   ├── dynamic_etl_runner.py       # Engine thực thi ETL động từ file YAML
│   ├── etl_tpcds_sf1.py            # Pipeline ETL toàn trình chuẩn Medallion từ TPC-DS SF1
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
