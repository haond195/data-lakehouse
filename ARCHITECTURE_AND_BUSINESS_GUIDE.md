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

### 1.2. Định nghĩa Bộ chỉ số đo lường cốt lõi theo từng Nghiệp vụ (Business KPIs)

#### A. Nghiệp vụ Bán lẻ & Cửa hàng (Retail Sales):
1. **Giá trị trung bình đơn hàng (Average Order Value - AOV):**
   $$\text{AOV} = \frac{\text{Net Revenue}}{\text{Total Orders}}$$
2. **Biên lợi nhuận thuần (Net Profit Margin %):**
   $$\text{Profit Margin (\%)} = \left( \frac{\text{Net Profit}}{\text{Net Revenue}} \right) \times 100$$
3. **Đơn giá bán trung bình (Average Unit Price - AUP):**
   $$\text{AUP} = \frac{\text{Net Revenue}}{\text{Units Sold}}$$

#### B. Nghiệp vụ Chuỗi cung ứng & Kho - Kệ (Supply Chain & Inventory):
1. **Vòng quay tồn kho kho - kệ (Inventory Turnover Ratio):**
   $$\text{Turnover Ratio} = \frac{\text{Units Sold on Shelf}}{\text{Total Warehouse Stock}}$$
2. **Số ngày bán hết tồn kho (Days Sales of Inventory - DSI):**
   $$\text{DSI} = \left( \frac{\text{Total Warehouse Stock}}{\text{Units Sold on Shelf}} \right) \times 30$$
   *Ý nghĩa:* Dự báo số ngày tồn kho còn lại; phát hiện rủi ro tồn ứ (`OVERSTOCK_RISK`) hoặc cháy hàng (`OUT_OF_STOCK`).
3. **Mật độ hàng hóa lưu kho (Storage Density):**
   $$\text{Density} = \frac{\text{Total Units Stored}}{\text{Warehouse Area (Sq Ft)}}$$

#### C. Nghiệp vụ Bán lẻ Đa kênh & Giao vận (Omnichannel & Returns):
1. **Tỷ trọng doanh thu theo kênh (Channel Revenue Share %):**
   $$\text{Channel Share (\%)} = \left( \frac{\text{Channel Revenue}}{\sum \text{Omnichannel Revenue}} \right) \times 100$$
2. **Tỷ lệ đổi trả hàng (Return Rate %):**
   $$\text{Return Rate (\%)} = \left( \frac{\text{Returned Units}}{\text{Units Sold}} \right) \times 100$$
3. **Tỷ lệ hoàn tiền trên doanh thu (Refund Impact Ratio %):**
   $$\text{Refund Impact (\%)} = \left( \frac{\text{Total Refunded Amount}}{\text{Net Revenue}} \right) \times 100$$

#### D. Nghiệp vụ Khuyến mãi & Khách hàng (Promotions & Marketing ROI):
1. **Hiệu suất sinh lời chiến dịch (Promotion ROI %):**
   $$\text{Promotion ROI (\%)} = \left( \frac{\text{Promotion Revenue} - \text{Promo Cost}}{\text{Promo Cost}} \right) \times 100$$
2. **AOV đơn hàng khuyến mãi (Promo AOV):**
   $$\text{Promo AOV} = \frac{\text{Promotion Revenue}}{\text{Promo Orders Count}}$$
3. **Phân bố quy mô khách hàng theo phân khúc (Segment Customer Density):**
   $$\text{Segment Count} = \text{COUNT}(\text{DISTINCT } \text{customer\_id}) \quad \text{theo Quốc gia, Học vấn, Hạng tín dụng}$$

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
[Nguồn: TPC-DS SF1 / Files / RDBMS] 
       │ 
       ▼ (1. Extract thô nguyên bản)
[TẦNG BRONZE: retail_bronze] ── Lưu thô, bổ sung audit timestamp (_ingested_at)
       │ 
       ▼ (2. Clean, Type cast, COALESCE NULLs, Joins)
[TẦNG SILVER: retail_silver] ── Làm sạch, lọc giao dịch lỗi, khử giá trị NULL
       │ 
       ▼ (3. Pre-aggregate Business KPIs)
[TẦNG GOLD:   retail_gold]   ── Bảng Data Marts tính sẵn phục vụ Superset & AI
```

### 3.1. 5 Kỹ thuật ETL cốt lõi được triển khai trong Pipeline
1. **Kiến trúc Medallion (Multi-Hop Storage Pattern):**
   * Tách bạch 3 vùng lưu trữ độc lập trên Apache Iceberg/MinIO: `Bronze` (thô) ➔ `Silver` (làm sạch) ➔ `Gold` (tổng hợp phân tích).
2. **Lọc dữ liệu rác & Dị thường (Data Filtering & Validation):**
   * Lọc bỏ đơn hàng âm hoặc thiếu giá trị thanh toán: `WHERE raw_net_paid IS NOT NULL AND raw_quantity > 0` (loại bỏ 7.724 bản ghi bất thường từ TPC-DS).
3. **Xử lý giá trị thiếu bằng nhãn nghiệp vụ (Data Imputation với `COALESCE`):**
   * Gán giá trị mặc định cho dữ liệu NULL để bảo toàn tính toàn vẹn báo cáo: `COALESCE(store_name, 'Online / Non-Store')`, `COALESCE(category, 'Uncategorized')`, `COALESCE(customer_id, 0)`.
4. **Làm phẳng dữ liệu theo mô hình hình sao (Denormalization & Star Schema Joins):**
   * Liên kết bảng Fact giao dịch với các Dimension (`date_dim`, `item`, `store`) thành bảng phẳng duy nhất ở tầng Silver giúp BI và AI truy vấn không cần JOIN phức tạp.
5. **Tính toán an toàn & Kiểm toán dòng đời (Safe Math & Lineage Auditing):**
   * Tránh lỗi chia cho 0 bằng `NULLIF`: `ROUND((SUM(net_profit) / NULLIF(SUM(net_revenue), 0)) * 100, 2) AS profit_margin_pct`.
   * Gắn nhãn thời gian truy vết ở từng tầng: `_ingested_at` (Bronze), `_transformed_at` (Silver), `_calculated_at` (Gold).

### 3.2. Chi tiết phân tầng dữ liệu Medallion hoàn chỉnh

#### A. Phân hệ Bán lẻ & Doanh thu (Retail Sales Domain):
* **🥉 Tầng Bronze (`retail_bronze.store_sales_raw` - 100.000 dòng):** Tiếp nhận dữ liệu giao dịch bán lẻ thô.
* **🥈 Tầng Silver (`retail_silver.sales_transactions` - 92.276 dòng):** Làm sạch đơn hàng lỗi, chuẩn hóa kiểu `DOUBLE`, liên kết Dimension.
* **🥇 Tầng Gold (`retail_gold.mart_monthly_store_performance` - 4.133 dòng):** Gom nhóm tính sẵn doanh thu, chi phí, lợi nhuận theo Tháng/Cửa hàng.

#### B. Phân hệ Chuỗi cung ứng & Kho - Kệ (Supply Chain & Inventory Domain):
* **🥉 Tầng Bronze:**
  * `retail_bronze.warehouse_raw` (5 dòng): Thông tin thô các kho hàng.
  * `retail_bronze.inventory_raw` (150.000 dòng): Dữ liệu kiểm kê số lượng tồn kho nguyên bản.
* **🥈 Tầng Silver:**
  * `retail_silver.dim_warehouse` (5 dòng): Danh mục kho chuẩn hóa diện tích và vị trí.
  * `retail_silver.inventory_snapshot` (142.546 dòng): Tồn kho làm sạch, liên kết chi tiết tên sản phẩm, thương hiệu, đơn giá và giá trị tồn kho.
* **🥇 Tầng Gold:**
  * `retail_gold.mart_inventory_turnover` (667 dòng): Đối soát hàng bán trên kệ (`sales_transactions`) với hàng tồn kho (`inventory_snapshot`), tính tỷ lệ quay vòng kho - kệ (`shelf_to_warehouse_ratio`).
  * `retail_gold.mart_warehouse_utilization` (5 dòng): Đo lường mật độ lưu trữ (`density_units_per_sq_ft`) và tổng giá trị hàng hóa tại từng kho.

#### C. Phân hệ Khuyến mãi & Khách hàng 360 (Promotion & Customer 360 Domain):
* **🥉 Tầng Bronze:**
  * `retail_bronze.promotion_raw` (300 dòng): Dữ liệu chiến dịch marketing thô.
  * `retail_bronze.customer_raw` (100.000 dòng): Thông tin định danh khách hàng.
  * `retail_bronze.customer_demographics_raw` (1.920.800 dòng): Dữ liệu nhân khẩu học (giới tính, học vấn, tín dụng).
* **🥈 Tầng Silver:**
  * `retail_silver.dim_promotion` (300 dòng): Chuẩn hóa chi phí và kênh marketing (Email, TV).
  * `retail_silver.dim_customer_360` (100.000 dòng): Hợp nhất họ tên, email, quốc gia, tình trạng hôn nhân, học vấn và xếp hạng tín dụng.
* **🥇 Tầng Gold:**
  * `retail_gold.mart_promotion_sales_performance` (300 dòng): Đánh giá doanh thu và lợi nhuận tạo ra từ từng chương trình khuyến mãi.
  * `retail_gold.mart_customer_segmentation` (12.079 dòng): Phân khúc khách hàng đa chiều theo Quốc gia, Giới tính, Học vấn và Xếp hạng tín dụng.

#### D. Phân hệ Bán lẻ Đa kênh & Giao vận, Đổi trả (Omnichannel & Returns Domain):
* **🥉 Tầng Bronze:**
  * `retail_bronze.web_sales_raw` (50.000 dòng): Dữ liệu đơn hàng kênh Web trực tuyến.
  * `retail_bronze.catalog_sales_raw` (50.000 dòng): Dữ liệu đơn hàng qua Catalog ấn phẩm.
  * `retail_bronze.store_returns_raw` (25.000 dòng): Dữ liệu đổi trả hàng nguyên bản.
  * `retail_bronze.ship_mode_raw` (20 dòng): Danh mục phương thức vận chuyển.
  * `retail_bronze.return_reason_raw` (75 dòng): Danh mục lý do đổi trả hàng.
* **🥈 Tầng Silver:**
  * `retail_silver.omnichannel_sales_transactions` (191.790 dòng): Hợp nhất 3 kênh Store, Web, Catalog thành 1 bảng giao dịch đa kênh chuẩn hóa duy nhất.
  * `retail_silver.returns_transactions` (24.138 dòng): Làm sạch giao dịch trả hàng, liên kết lý do hoàn trả và tiền hoàn lại.
* **🥇 Tầng Gold:**
  * `retail_gold.mart_omnichannel_performance` (126 dòng): Đối soát so sánh doanh thu, đơn hàng, giá trị trung bình đơn (AOV) giữa 3 kênh Store vs Web vs Catalog theo Tháng/Năm.
  * `retail_gold.mart_returns_analysis` (76 dòng): Phân tích chi tiết số lượng hàng trả và tổng tiền hoàn theo từng lý do trả hàng.

### 3.3. Tự động hóa với mô hình Config-driven ETL
Hệ thống hỗ trợ cơ chế nạp dữ liệu không cần viết lại mã nguồn Python:
* **File cấu hình YAML ([config/etl_pipeline.yaml](file:///D:/local-lakehouse/config/etl_pipeline.yaml)):** Khai báo nguồn dữ liệu, danh sách cột mapping tầng Bronze, điều kiện lọc tầng Silver, và các chỉ số tổng hợp tầng Gold.
* **Engine điều phối ([scripts/dynamic_etl_runner.py](file:///D:/local-lakehouse/scripts/dynamic_etl_runner.py)):** Đọc cấu hình YAML và tự động sinh SQL Trino tương ứng để thực thi toàn trình Bronze ➔ Silver ➔ Gold. Khi có bộ dữ liệu mới, chỉ cần tạo 1 file YAML mới và chạy:
  ```bash
  python scripts/dynamic_etl_runner.py config/<pipeline_moi>.yaml
  ```

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

| Ứng dụng | Địa chỉ Web (URL) | Tài khoản / Mật khẩu | Quyền hạn & Vai trò |
| :--- | :--- | :--- | :--- |
| **Apache Superset** | http://localhost:8089 | dmin / dmin | **Admin:** Toàn quyền quản trị hệ thống |
| **Apache Superset** | http://localhost:8089 | nalyst / nalyst123 | **Gamma (Analyst):** Xem Dashboard, không sửa kết nối |
| **Trino CLI / JDBC** | localhost:8080 | User: dmin | Toàn quyền DDL, DML trên toàn bộ các Catalog |
| **Trino CLI / JDBC** | localhost:8080 | User: nalyst | **Chỉ đọc (SELECT)** trên tầng Gold, **CẤM** tầng Bronze/Silver |
| **AI Chatbot** | http://localhost:8501 | Mở trực tiếp | Hỏi đáp tự động với các Gold Marts |
| **Trino Web UI** | http://localhost:8080 | User: dmin | Theo dõi truy vấn & hiệu năng cụm |
| **MinIO Console** | http://localhost:9001 | dmin / password123 | Quản trị S3 Object Storage |
| **PostgreSQL** | localhost:5433 | User: postgres, DB: metastore | Lưu trữ siêu dữ liệu Catalog |

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

---

## 7. BẢO MẬT & PHÂN QUYỀN TRUY CẬP (SECURITY & ACCESS CONTROL)

Hệ thống triển khai cơ chế phân quyền RBAC độc lập, hiệu năng cao mà **không cần phụ thuộc vào Apache Ranger**:

1. **Trino File-based Access Control (	rino-security/rules.json):**
   * Được cấu hình qua ccess-control.properties với cơ chế kiểm soát trực tiếp trong nhân Trino (tốn 0 MB RAM phụ trợ).
   * **Tài khoản nalyst:**
     * Quyền trên 
etail_gold: Chỉ được phép SELECT.
     * Quyền trên 
etail_bronze & 
etail_silver: privileges: [] -> Trino lập tức trả về lỗi Access Denied: Cannot select from table... nếu cố tình truy vấn dữ liệu thô.
     * Quyền DDL: Bị tước bỏ quyền DROP TABLE, DROP VIEW, ALTER để bảo vệ toàn vẹn dữ liệu.
   * **Tài khoản dmin & etl_*:** Có đầy đủ quyền DDL/DML phục vụ quá trình pipeline và quản trị hệ thống.

2. **Superset Role-Based Access Control (RBAC):**
   * **Role Admin:** Toàn quyền cấu hình kết nối Database, tạo Schema, quản trị người dùng.
   * **Role Gamma (nalyst):** Người dùng nghiệp vụ chỉ được xem biểu đồ và Dashboard được cấp phép, không thể can thiệp vào tầng kết nối hạ tầng.


---

## 8. ĐÁNH GIÁ HỆ THỐNG: CÁC ĐIỂM ĐÃ HOÀN THÀNH & PHẠM VI CHƯA TRIỂN KHAI

### 8.1. Các hạng mục đã hoàn thành xuất sắc (Đạt chuẩn Enterprise Lakehouse)
1. **Kiến trúc Modern Lakehouse phân tách Compute & Storage:**
   * Lưu trữ phân tán dạng Parquet trên MinIO S3 với định dạng bảng Apache Iceberg v2 hỗ trợ ACID, Time Travel và Schema Evolution.
   * Động cơ xử lý phân tán Trino In-Memory cho tốc độ truy vấn cực nhanh (< 0.2s) trên hàng trăm nghìn bản ghi.
2. **Bao phủ 100% 4 phân hệ nghiệp vụ Medallion (Bronze -> Silver -> Gold):**
   * *Bán lẻ Cửa hàng (Retail Sales):* Bảng hóa đơn, chỉ số doanh thu thuần, doanh thu gộp, lợi nhuận.
   * *Chuỗi cung ứng & Kho - Kệ (Supply Chain & Inventory):* Đối soát số lượng hàng trên kệ và hàng tồn kho, tính số ngày tồn kho (DSI) và phân loại nguy cơ ứ đọng hàng (OVERSTOCK_RISK).
   * *Bán lẻ Đa kênh & Giao vận, Đổi trả (Omnichannel & Returns):* Hợp nhất 3 kênh Store, Web, Catalog thành 1 bảng giao dịch duy nhất (191k dòng); phân tích nguyên nhân đổi trả hàng.
   * *Khuyến mãi & Khách hàng 360 (Promotions & Customer 360):* Đo lường ROI % từng chiến dịch quảng cáo; phân khúc khách hàng theo học vấn, tín dụng, quốc gia.
3. **Mô hình Config-driven ETL tự động hóa:**
   * Cơ chế khai báo nguồn và quy tắc lọc/tính toán qua file YAML (config/etl_pipeline.yaml), thực thi tự động qua engine Python mà không cần lập trình lại hệ thống.
4. **Bộ chỉ số phân tích nghiệp vụ chuyên sâu (Semantic Views):**
   * Đóng gói sẵn các công thức tài chính chuẩn hóa: AOV, AUP, Net Margin %, DSI, Vòng quay tồn kho, Tỷ trọng doanh thu kênh, Campaign ROI %, Return Rate %.
5. **Bảo mật & Phân quyền RBAC nội bộ không cần Apache Ranger:**
   * Phân quyền trực tiếp trong Trino qua 
ules.json: Tài khoản nalyst chỉ được đọc tầng Gold, bị chặn hoàn toàn khi truy cập tầng Bronze/Silver hoặc cố tình thực hiện lệnh phá hoại (DROP TABLE/VIEW).
   * Phân quyền vai trò trên Apache Superset giữa nhóm Admin và nhóm nghiệp vụ Gamma (nalyst).
6. **Trợ lý Phân tích AI Text-to-SQL Động cơ kép:**
   * Tự động quét cấu trúc 9 bảng/view Gold trong thời gian thực (Schema Introspection), sinh câu lệnh SQL chuẩn Trino (hỗ trợ cả CTE WITH phức tạp) và tự động trực quan hóa biểu đồ.

---

### 8.2. Các hạng mục chưa đưa vào hệ thống & Giải thích lý do kỹ thuật

1. **Luồng dữ liệu thời gian thực (Real-time Streaming qua Kafka / Flink / Spark Streaming):**
   * *Lý do:* Bộ dữ liệu TPC-DS SF1 là dữ liệu lịch sử/tĩnh phục vụ phân tích xu hướng quản trị. Trong nghiệp vụ doanh nghiệp thực tế, 95% báo cáo tài chính, hiệu quả kho bãi và marketing chỉ cần đối soát theo mẻ định kỳ (Batch ETL hàng đêm hoặc hàng giờ). Bật Kafka + Spark Streaming chạy 24/7 chỉ làm lãng phí 2-3 GB RAM máy chủ mà không tạo thêm giá trị phân tích cho dữ liệu tĩnh.
2. **Công cụ điều phối luồng tập trung (Workflow Orchestrator: Apache Airflow / Dagster):**
   * *Lý do:* Hệ thống hiện tại đã có bộ script ETL chuẩn hóa và engine Config-driven YAML có thể gọi tự động qua Windows Task Scheduler hoặc cronjob nhẹ nhàng. Cài đặt thêm Apache Airflow đòi hỏi ít nhất 4 container phụ trợ (Webserver, Scheduler, Triggerer, Worker) tốn thêm 2.5 GB RAM, không tối ưu cho môi trường cục bộ (Local).
3. **Bộ kiểm định chất lượng dữ liệu độc lập (Great Expectations / Soda Core):**
   * *Lý do:* Toàn bộ quy tắc kiểm tra chất lượng dữ liệu (Data Quality Checks) gồm: kiểm tra khóa chính, loại bỏ bản ghi rác (WHERE raw_net_paid IS NOT NULL AND raw_quantity > 0), khử NULL (COALESCE), và chống chia cho 0 (NULLIF) đã được nhúng chặt chẽ ngay tại các câu lệnh chuyển đổi tầng Silver và View Gold.
4. **Triển khai cụm phân tán đa máy chủ (Multi-node Kubernetes Cluster):**
   * *Lý do:* Hệ thống được đóng gói hoàn hảo trong docker-compose.yml trên một máy trạm duy nhất nhằm phục vụ tối đa nhu cầu kiểm thử, chấm đồ án và trình diễn PoC (Proof of Concept) mà không phát sinh chi phí thuê máy chủ đám mây (Cloud). Toàn bộ kiến trúc đều đã sẵn sàng để scale-out lên cụm Kubernetes khi doanh nghiệp có nhu cầu.
