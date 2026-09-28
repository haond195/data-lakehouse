# 📚 Hướng Dẫn & Kiến Thức Về SCD (Slowly Changing Dimensions)

## 1. SCD Là Gì?
- **SCD (Slowly Changing Dimensions - Chiều Biến Đổi Chậm)** là kỹ thuật trong thiết kế Data Warehouse / Lakehouse để theo dõi và quản lý sự thay đổi của dữ liệu danh mục (Dimension) theo thời gian.
- **Vấn đề thực tế**: Khách hàng `Nguyễn Văn A` năm 2021 sống ở **Hà Nội** và mua hàng; năm 2023 chuyển vào **TP.HCM** và tiếp tục mua hàng.
  - Nếu chỉ cập nhật thành "TP.HCM", báo cáo doanh thu năm 2021 sẽ bị ghi nhận nhầm là của chi nhánh TP.HCM.
  - Kỹ thuật SCD sinh ra để giải quyết bài toán lịch sử này.

---

## 2. Các Kiểu SCD Phổ Biến & Ví Dụ Thực Tế

### SCD Type 0: Giữ nguyên gốc (Retain Original)
- **Cách hoạt động**: Không bao giờ thay đổi, giữ nguyên giá trị ban đầu dù nguồn có sửa đổi.
- **Ví dụ**: Ngày sinh (`date_of_birth`), Mã số định danh cá nhân / CCCD.

---

### SCD Type 1: Ghi đè trực tiếp (Overwrite - Không lưu lịch sử)
- **Cách hoạt động**: Khi dữ liệu thay đổi, lấy giá trị mới đè lên giá trị cũ. Lịch sử bị xóa hoàn toàn.
- **Khi nào dùng**: Sửa lỗi chính tả, cập nhật thông tin không quan trọng cần phân tích xu hướng.
- **Ví dụ**:
  - *Trước*: `name = 'Nguyenn Van A'`
  - *Sau*: `name = 'Nguyễn Văn A'` (Sửa lỗi gõ sai chính tả).

---

### SCD Type 2: Thêm dòng mới (Add New Row - Chuẩn mực lưu vết toàn diện)
- **Cách hoạt động**: Giữ nguyên dòng cũ, thêm 1 dòng mới với khóa đại diện (Surrogate Key) mới. Sử dụng các cột: `valid_from`, `valid_to`, `is_current`.
- **Khi nào dùng**: Bắt buộc khi cần phân tích chính xác dữ liệu kinh doanh tại từng thời điểm lịch sử.
- **Ví dụ**:
| customer_id | customer_name | city | valid_from | valid_to | is_current |
| :--- | :--- | :--- | :--- | :--- | :--- |
| C001 | Nguyễn Văn A | Hà Nội | 2021-01-01 | 2023-05-15 | FALSE |
| C001 | Nguyễn Văn A | TP.HCM | 2023-05-16 | NULL | **TRUE** |

---

### SCD Type 3: Thêm cột lưu giá trị cũ (Add New Column)
- **Cách hoạt động**: Giữ nguyên số lượng dòng, nhưng thêm cột `previous_*` bên cạnh `current_*`.
- **Đặc điểm**: Chỉ lưu được 1 mốc thay đổi gần nhất, không theo dõi được nhiều đời lịch sử.
- **Ví dụ**:
| customer_id | customer_name | current_city | previous_city | effective_date |
| :--- | :--- | :--- | :--- | :--- |
| C001 | Nguyễn Văn A | TP.HCM | Hà Nội | 2023-05-16 |

---

### SCD Type 4: Tách bảng lịch sử riêng (History Table)
- **Cách hoạt động**: Tạo 2 bảng riêng biệt:
  - Bảng chính `dim_customers`: Chỉ lưu thông tin hiện tại (Type 1).
  - Bảng phụ `dim_customers_history`: Lưu toàn bộ dòng lịch sử (Type 2).
- **Khi nào dùng**: Khi bảng chính có tần suất truy vấn rất cao và cần tốc độ tối đa.

---

### SCD Type 6: Kiểu kết hợp Hybrid (1 + 2 + 3 = 6)
- **Cách hoạt động**: Kết hợp ưu điểm của Type 1, 2 và 3.
  - Vừa thêm dòng mới khi có thay đổi (Type 2).
  - Vừa có cột lưu giá trị trước đó (Type 3).
  - Vừa ghi đè đồng bộ giá trị hiện tại lên tất cả các dòng cũ để dễ lọc (Type 1).

---

## 3. Cách dbt Tự Động Hóa SCD Type 2 Bằng `Snapshots`

Trong công nghệ truyền thống, kỹ sư phải viết hàng trăm dòng lệnh `MERGE INTO` phức tạp. Với dbt, hệ thống tự động sinh bảng **SCD Type 2** chỉ bằng một block cấu hình:

```sql
-- file: snapshots/snp_customers.sql
{% snapshot snp_customers %}

{{
    config(
      target_schema='stg_silver',
      unique_key='customer_id',
      strategy='check',
      check_cols=['city', 'state', 'credit_rating']
    )
}}

SELECT customer_id, customer_name, city, state, credit_rating
FROM {{ ref('stg_customer') }}

{% endsnapshot %}
```

- Khi bạn gõ lệnh `dbt snapshot`:
  1. dbt tự động so sánh dữ liệu mới và cũ.
  2. Tự thêm các cột `dbt_valid_from`, `dbt_valid_to`, `dbt_updated_at`.
  3. Tự đóng phiên bản cũ (`dbt_valid_to = now()`) và mở phiên bản mới hoàn toàn tự động.
