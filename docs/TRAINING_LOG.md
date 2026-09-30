# 📋 Nhật Ký Đào Tạo & Kiến Thức Thu Hoạch Dự Án (Project Training Log)

Tài liệu này tổng hợp toàn bộ kiến thức kỹ thuật, kiến trúc hệ thống, kinh nghiệm thực chiến và xử lý sự cố tích lũy được trong suốt quá trình triển khai dự án **Modern Data Lakehouse & AI Business Intelligence Platform**.

---

## 1. Kiến Trúc Modern Data Lakehouse & Hạ Tầng Phân Tán
* **Decoupled Architecture (Tách rời Tính toán & Lưu trữ)**:
  - Khác biệt với Data Warehouse truyền thống (ràng buộc chặt phần cứng), Lakehouse tách rời hoàn toàn: Storage trên MinIO Object Storage (AWS S3 Compatible) và Compute trên Trino Distributed SQL Engine.
  - Tối ưu chi phí lưu trữ, khả năng mở rộng (scaling) độc lập giữa dung lượng đĩa và tài nguyên CPU/RAM.
* **Apache Iceberg Table Format v2**:
  - Hỗ trợ giao dịch chuẩn ACID trên Data Lake, loại bỏ hiện tượng đọc bẩn (dirty read) và xung đột khi ghi đồng thời.
  - Tính năng Time Travel & Snapshot Isolation: Dễ dàng quay ngược thời gian để kiểm tra dữ liệu lịch sử hoặc hoàn tác lỗi.
  - Phân vùng ẩn (Hidden Partitioning): Tự động partition pruning mà không bắt buộc người dùng phải nhớ cấu trúc thư mục vật lý.

---

## 2. Kỹ Thuật Chuyển Đổi Dữ Liệu Với dbt (Data Build Tool)
* **Quy trình ELT Chuẩn Công Nghiệp**:
  - Thay vì ETL truyền thống biến đổi dữ liệu trước khi nạp, ELT nạp dữ liệu thô vào Lakehouse rồi dùng dbt để khai thác tối đa sức mạnh xử lý phân tán của Trino.
* **Kiến trúc Medallion 3 tầng hoàn chỉnh**:
  - **Bronze (17 models)**: Ingestion nguyên trạng từ nguồn TPC-DS SF1, chuẩn hóa tên cột snake_case, gắn metadata thời gian `_ingested_at`.
  - **Silver (10 models)**: Làm sạch dữ liệu, khử NULL bằng `COALESCE`, lọc giá trị dị biệt, hợp nhất đa kênh (`fct_returns_unified`).
  - **Gold (7 models)**: Pre-aggregate các Data Mart nghiệp vụ phức tạp, kết hợp đa bảng chéo miền (Sales + Inventory + Returns + Products).
* **Quản lý phả hệ & kiểm thử tự động (DAG & Data Quality)**:
  - Quản lý phụ thuộc tự động qua Jinja macro `{{ ref(...) }}` và `{{ source(...) }}`.
  - Tự động hóa kiểm tra tính toàn vẹn dữ liệu qua 9 bộ test: `unique`, `not_null`, `accepted_values`.

---

## 3. Quản Lý Chiều Biến Đổi Chậm (Slowly Changing Dimensions - SCD)
* **Nắm vững bản chất các kiểu SCD**:
  - **Type 1 (Ghi đè)**: Dùng cho thông tin sửa lỗi hoặc không cần theo dõi lịch sử (SĐT, Email) bằng câu lệnh `MERGE INTO`.
  - **Type 2 (Lưu vết toàn diện)**: Chuẩn mực lưu vết lịch sử khách hàng (`dim_customers`) với các trường `valid_from`, `valid_to`, `is_current` và Surrogate Key.
  - **Type 3 (Thêm cột)**: Lưu trạng thái liền kề (`current_value`, `previous_value`).
* **Kỹ thuật As-Of Query (Truy vấn thời điểm)**:
  - Tái hiện chính xác trạng thái khách hàng tại ngày phát sinh đơn hàng trong quá khứ thông qua điều kiện `BETWEEN valid_from AND valid_to`.
* **Tự động hóa với `dbt snapshot`**:
  - Tự động phát hiện thay đổi và đóng/mở phiên bản dữ liệu chỉ bằng khai báo cấu hình YAML.

---

## 4. Bảo Mật & Phân Quyền Zero Trust (Trino RBAC & Superset SSO)
* **File-based RBAC trên Trino**:
  - Cấu hình qua `trino-security/rules.json`:
    - Role `analyst`: Bị chặn hoàn toàn quyền đọc tầng Bronze & Silver; chỉ được truy vấn tầng Gold đã tinh chế.
    - Role `admin`: Toàn quyền DDL, DML trên toàn bộ hệ thống.
* **Đồng bộ phiên đăng nhập một lần (Single Sign-On - SSO)**:
  - Tích hợp Chatbot Drawer trực tiếp trên giao diện Apache Superset qua `tail_js_custom_extra.html`.
  - Chatbot gọi API `/api/v1/me/` của Superset để tự động kế thừa danh tính người dùng và truyền trực tiếp vào Trino Connection.
* **Chế độ Khóa cứng (Strict Mode)**:
  - Ẩn nút đăng xuất và form đăng nhập thủ công khi chạy nhúng, loại bỏ triệt để nguy cơ người dùng tự ý đổi tài khoản hoặc leo quyền.

---

## 5. Kinh Nghiệm Xử Lý Sự Cố Thực Chiến (Troubleshooting & Lessons Learned)
1. **Lỗi Column Not Found trong Trino**:
   - *Nguyên nhân*: Truy vấn nhầm tên cột không tồn tại (`ih.category` thay vì join qua `dim_products`).
   - *Bài học*: Luôn quét metadata thời gian thực (`DESCRIBE table`) trước khi sinh truy vấn SQL tự động.
2. **Lỗi Trino Server Initializing**:
   - *Nguyên nhân*: Trino cần vài giây để kết nối Hive Metastore và nạp plugin Iceberg khi khởi động lại.
   - *Bài học*: Cần thiết lập cơ chế retry/backoff hoặc kiểm tra readiness probe trước khi gửi query.
3. **Hiện tượng Cache Template Superset**:
   - *Nguyên nhân*: Gunicorn và trình duyệt lưu đệm mã HTML cũ của template Jinja.
   - *Bài học*: Khởi động lại container Superset và dùng `Ctrl + F5` khi cập nhật custom JavaScript/CSS.
4. **SQL Injection & Cú pháp Trino SQL**:
   - *Bài học*: Bộ lọc `clean_generated_sql` phải xử lý triệt để các khối mã Markdown thừa, hỗ trợ cả `WITH` và `SELECT`, đồng thời loại bỏ dấu chấm phẩy `;` cuối câu lệnh để tránh lỗi phân tích cú pháp của Trino JDBC.
