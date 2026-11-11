# TỪ ĐIỂN DỮ LIỆU (DATA DICTIONARY)

## 1. Mục đích

Tài liệu mô tả cấu trúc, kiểu dữ liệu và ý nghĩa các thuộc tính trong `documents_metadata.json`, phục vụ quản lý, phân loại và kiểm soát quyền truy cập tài liệu của trợ lý AI trong nhà trường.

## 2. Danh sách thuộc tính

| Thuộc tính | Kiểu dữ liệu | Ý nghĩa |
|---|---|---|
| `doc_id` | String | Mã định danh duy nhất của tài liệu |
| `title` | String | Tiêu đề tài liệu |
| `file_path` | String | Đường dẫn tới file TXT từ thư mục gốc |
| `classification` | Enum | Mức phân loại Public, Internal, Restricted |
| `allowed_roles` | Array[String] | Danh sách vai trò được phép truy cập |
| `department` | String | Đơn vị sở hữu hoặc quản lý tài liệu trong bộ dữ liệu |
| `retention_days` | Integer | Số ngày lưu trữ đề xuất trong môi trường thử nghiệm |
| `created_date` | String (YYYY-MM-DD) | Ngày tạo dữ liệu |
| `description` | String | Mô tả ngắn về tài liệu |
| `university` | String | Trường đại học có nguồn tham khảo |
| `source_url` | String (URL) | Đường dẫn nguồn công khai |
| `data_origin` | Enum | Nguồn gốc nội dung tài liệu |
| `is_synthetic` | Boolean | Đánh dấu tài liệu giả lập |
| `word_count` | Integer | Số từ của tài liệu |

## 3. Quy tắc phân quyền

| Mức phân loại | Vai trò được phép |
|---|---|
| Public | SinhVien, GiangVien, QuanTri |
| Internal | GiangVien, QuanTri |
| Restricted | QuanTri |

Hệ thống phải kiểm tra `allowed_roles` trước khi cung cấp nội dung tài liệu cho bộ máy truy xuất RAG.

## 4. Quy tắc dữ liệu

- `doc_id` không được trùng lặp.
- Mỗi tài liệu TXT phải có một bản ghi metadata tương ứng.
- `file_path` phải trỏ tới file tồn tại.
- `classification` phải thuộc một trong ba mức được quy định.
- `allowed_roles` phải phù hợp với mức phân loại.
- `retention_days` phải là số nguyên dương.
- `created_date` sử dụng định dạng YYYY-MM-DD.
- `data_origin` nhận giá trị `official_public_paraphrase` hoặc `synthetic_based_on_public_context`.
- Tài liệu Internal và Restricted là dữ liệu giả lập, không sử dụng thông tin cá nhân thật.

## 5. Ý nghĩa trong hệ thống

Metadata được sử dụng để kiểm tra quyền truy cập, xác định nguồn tài liệu, hỗ trợ truy xuất có kiểm soát và áp dụng chính sách lưu trữ dữ liệu trong môi trường thử nghiệm.