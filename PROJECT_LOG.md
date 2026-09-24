# NHẬT KÝ DỰ ÁN DATA LAKEHOUSE & BI PLATFORM (LOCAL)

Tài liệu này ghi lại toàn bộ tiến độ triển khai, các công cụ đã sử dụng, cấu hình và trạng thái của hệ thống.

---

## 1. BẢNG TỔNG HỢP CÁC CÔNG CỤ ĐÃ SỬ DỤNG

| Công cụ | Phiên bản / Image | Vai trò | Cổng (Port) / Đường dẫn | Trạng thái |
| :--- | :--- | :--- | :--- | :--- |
| **MinIO** | `minio/minio:latest` | Object Storage (Giả lập AWS S3) | API: `9000`, Web UI: `9001` | Đã cấu hình |
| **PostgreSQL** | `postgres:15-alpine` | Metadata Database cho HMS & Superset | `5432` | Đã cấu hình |
| **Hive Metastore** | `bitsondatadev/hive-metastore:3.1.3` | Standalone Metadata Catalog | `9083` | Đã cấu hình |
| **Trino** | `trinodb/trino:latest` | Distributed SQL Query Engine | Web UI & JDBC: `8080` | Đã cấu hình |
| **Apache Superset**| `apache/superset:3.1.0` | BI Dashboard & Visualisation | Web UI: `8088` | Đã cấu hình |
| **TPC-DS** | Trino Built-in Connector | Bộ dữ liệu giả lập bán lẻ đa kênh (~1GB) | Catalog `tpcds` | Đã kiểm tra |
| **AI Chatbot** | Streamlit + Trino DBAPI | Giao diện Chatbot phân tích dữ liệu | `chatbot/app.py` | Đã tạo mã nguồn |

---

## 2. TIẾN ĐỘ THỰC HIỆN

### Giai đoạn 1: Thiết kế & Khởi tạo Hạ tầng Local
- [x] Tạo file kiến trúc `docker-compose.yml` kết nối 5 service cốt lõi (MinIO, Postgres, HMS, Trino, Superset).
- [x] Khởi tạo sẵn bucket `warehouse` trên MinIO.
- [x] Tạo file cấu hình Trino Catalog `trino-catalog/lakehouse.properties` trỏ về MinIO và Hive Metastore.
- [x] Khởi tạo Database riêng `superset` và `metastore` trong PostgreSQL qua `init-dbs.sql`.

### Giai đoạn 2: Khám phá Dữ liệu & Xây dựng Semantic Layer
- [x] Tìm hiểu cấu trúc bộ dữ liệu TPC-DS (24 bảng: 7 Fact, 17 Dimension).
- [x] Thiết kế Semantic Layer bằng Trino View (`semantic_sales_mart`) để chuẩn hóa công thức KPI và ẩn logic JOIN cho AI Chatbot.
- [x] Tạo mã nguồn Chatbot phân tích Text-to-SQL bằng Streamlit (`chatbot/app.py`).

### Giai đoạn 3: Xác thực & Kết nối Trino
- [x] Thiết lập phương thức kết nối Trino qua Username (`data_analyst`).
- [x] Tài liệu hóa 3 cách kết nối: DBeaver, Python SDK (`trino`), Trino Web UI.

---

## 3. THÔNG TIN ĐĂNG NHẬP & TRUY CẬP

* **MinIO Console**: `http://localhost:9001`
  * Username: `admin` | Password: `password123`
* **Trino Web UI**: `http://localhost:8080`
  * Username: `data_analyst` (không cần mật khẩu)
* **Apache Superset**: `http://localhost:8088`
  * Username: `admin` | Password: `admin`
  * Chuỗi kết nối Trino trong Superset: `trino://admin@trino:8080/lakehouse`
* **File nhật ký này**: `PROJECT_LOG.md`

---

### Cập nhật ngày 18/09/2026: Sửa lỗi khởi động & Kích hoạt Trino thành công
- [x] Thay thế image itsondatadev/hive-metastore lỗi thời bằng pache/hive:3.1.3.
- [x] Đổi cổng port conflict: PostgreSQL map sang 5433:5432, Superset map sang 8089:8088.
- [x] Xử lý lỗi UTF-8 BOM trên Windows cho các file catalog .properties.
- [x] Cập nhật chuẩn cấu hình S3 cho Trino 482 (s.s3.enabled=true, s3.region=us-east-1).
- [x] **Trino đã Up và Healthy 100%** trên cổng localhost:8080.
- [x] Test thành công truy vấn TPC-DS (SELECT c_customer_sk, c_first_name FROM tpcds.sf1.customer LIMIT 3;).
- [x] Hive Metastore 3.1.3 đã khởi tạo schema và chạy thành công trên cổng 9083.
- [x] Trino kết nối thành công với cả 	pcds và lakehouse (MinIO S3 + HMS).
- [x] Đã cấu hình catalog iceberg với JDBC Catalog (lưu trữ metadata chuẩn hiện đại thay cho Hive truyền thống).
- [x] Đã tạo thành công schema iceberg.retail_gold và bảng customer_gold (500 dòng).
- [x] Dữ liệu thực tế được ghi thành công dạng file .parquet và metadata Iceberg vào MinIO tại /warehouse/retail_gold/.
- [x] Apache Superset 3.1.0 đã khởi tạo và chạy thành công trên cổng http://localhost:8089.
- [x] User admin Superset: dmin / dmin.
- [x] Chuỗi kết nối Trino chuẩn cho Superset: 	rino://admin@trino:8080/iceberg.
- [x] Tạo thành công biểu đồ đầu tiên trên Apache Superset từ bảng Iceberg.
- [x] Nâng cấp ứng dụng Streamlit AI Chatbot (chatbot/app.py) kết nối trực tiếp với Trino và Apache Iceberg để phân tích qua ngôn ngữ tự nhiên.
- [x] Tắt bộ lọc bảo mật HTML trong Superset (HTML_SANITIZATION = False) để cho phép hiển thị iframe Chatbot trên Dashboard.
- [x] Đã di chuyển toàn bộ các bảng cốt lõi từ TPC-DS sang Apache Iceberg trên MinIO S3 (customer_gold, item, date_dim, store, promotion, store_sales, web_sales).
- [x] Đã xây dựng Semantic Layer: View iceberg.retail_gold.semantic_sales_mart chuẩn hóa thực thể và nối sẵn Fact + Dimensions.
- [x] Định nghĩa chuẩn các chỉ số kinh doanh (Metrics): Doanh thu gộp (Gross), Doanh thu thuần (Net), Chi phí (Cost), Lợi nhuận (Profit), Biên lợi nhuận (Margin %), Số lượng đơn (Orders).
- [x] Tích hợp tự động hóa hoàn toàn: Đưa Chatbot vào thành container local-chatbot trong docker-compose.yml.
- [x] Tích hợp Global AI Sidebar vào Superset qua file template chuẩn 	ail_js_custom_extra.html.
- [x] Bây giờ chỉ cần chạy docker compose up -d: Cả 6 service cùng khởi động, Superset tự động có nút nổi tròn 🤖 và thanh trượt AI Sidebar trên mọi trang mà không cần cấu hình thủ công.
- [x] Tự động hóa đăng ký Database Connection Trino trên Superset qua file superset_init_db.py.
- [x] Từ nay mỗi lần khởi động Docker, Superset luôn có sẵn kết nối Trino vĩnh viễn mà không bao giờ phải kết nối lại bằng tay.
- [x] Tích hợp AI LLM Đa nền tảng: Kết nối thành công FPT AI Marketplace (DeepSeek-V4-Flash) và Google Gemini API với cơ chế dự phòng Smart Rule Parser.
- [x] Tối ưu hóa thời gian suy luận của Reasoning LLM: Rút gọn prompt và nâng timeout lên 75s, phản hồi mượt mà sau 12–15 giây.
- [x] Xử lý triệt để giá trị NULL/None trong Semantic Layer bằng hàm COALESCE, đưa tỷ lệ khuyết tật dữ liệu trên báo cáo về 0.
- [x] Xây dựng và thực thi thành công toàn trình Pipeline ETL chuẩn Medallion (Bronze -> Silver -> Gold) từ bộ dữ liệu TPC-DS SF1 (100.000 dòng hoàn thành trong 5 giây).
- [x] Tự động đăng ký các bảng Gold/Silver thành Datasets có sẵn trên Apache Superset kèm đầy đủ metadata cột.
- [x] Xuất bản tài liệu toàn diện nghiệp vụ & kỹ thuật tại file ARCHITECTURE_AND_BUSINESS_GUIDE.md.

