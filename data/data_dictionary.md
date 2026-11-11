# TỪ ĐIỂN DỮ LIỆU (DATA DICTIONARY)

## 1. Mục đích

Tài liệu này quy định cấu trúc, ý nghĩa, miền giá trị và cách biểu diễn metadata của bộ dữ liệu dùng cho đề tài **“Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường”**.

`documents_metadata.json` là bản metadata chuẩn dùng cho pipeline. `documents_metadata.csv` là biểu diễn dạng bảng phục vụ kiểm tra, thống kê và đối soát. Hai file phải chứa cùng tập `doc_id` và tương đương về mặt logic.

## 2. Danh sách thuộc tính

| Thuộc tính       | Kiểu          | Bắt buộc | Quy tắc                                                               |
| ---------------- | ------------- | -------: | --------------------------------------------------------------------- |
| `doc_id`         | String        |       Có | Duy nhất; `DOC-Pxxx`, `DOC-Ixxx`, `DOC-Rxxx`                          |
| `title`          | String        |       Có | Không rỗng                                                            |
| `file_path`      | String        |       Có | Đường dẫn tương đối tới TXT                                           |
| `classification` | Enum          |       Có | `Public`, `Internal`, `Restricted`                                    |
| `allowed_roles`  | Array[String] |       Có | Quyền truy cập trực tiếp của tài liệu                                 |
| `department`     | String        |       Có | Đơn vị sở hữu/quản lý hoặc đơn vị mô phỏng                            |
| `retention_days` | Integer       |       Có | Public=365, Internal=180, Restricted=90 trong prototype               |
| `created_date`   | String        |       Có | `YYYY-MM-DD`                                                          |
| `description`    | String        |       Có | Mô tả ngắn                                                            |
| `university`     | String        |       Có | Trường/nguồn bối cảnh tham khảo                                       |
| `source_url`     | URL string    |       Có | Nguồn công khai cần được kiểm chứng                                   |
| `data_origin`    | Enum          |       Có | `official_public_paraphrase` hoặc `synthetic_based_on_public_context` |
| `is_synthetic`   | Boolean       |       Có | `true` với dữ liệu nghiệp vụ giả lập                                  |
| `word_count`     | Integer       |       Có | Thuộc tính dẫn xuất, phải được tính lại từ TXT khi validation         |

## 3. Quy tắc biểu diễn JSON và CSV

- JSON: `allowed_roles` là mảng chuỗi.
- CSV: `allowed_roles` dùng dấu `|`, ví dụ `SinhVien|GiangVien|QuanTri`.
- Không dùng chuỗi kiểu Python như `['SinhVien', 'GiangVien']` trong CSV.
- `is_synthetic` trong JSON là Boolean; trong CSV dùng `true`/`false`.

## 4. Chính sách RBAC

| Classification | Allowed roles mặc định       | Retention |
| -------------- | ---------------------------- | --------: |
| Public         | SinhVien, GiangVien, QuanTri |       365 |
| Internal       | GiangVien, QuanTri           |       180 |
| Restricted     | QuanTri                      |        90 |

Quyết định truy cập tài liệu được thực thi theo:
`AccessAllowed(user_role, document) = user_role ∈ document.allowed_roles`.

Kiểm tra quyền phải diễn ra **trước khi nội dung trái quyền được đưa vào tập ứng viên/context của RAG**.

## 5. Quy tắc nhất quán

1. `doc_id` không trùng.
2. Tiền tố P/I/R phải khớp `classification`.
3. Thư mục `public/internal/restricted` trong `file_path` phải khớp `classification`.
4. `allowed_roles` phải khớp chính sách RBAC.
5. `retention_days` phải là số nguyên dương và khớp chính sách prototype.
6. `created_date` đúng `YYYY-MM-DD`.
7. Internal/Restricted phải dùng `synthetic_based_on_public_context` và `is_synthetic=true`.
8. Mỗi metadata record phải có đúng một TXT tương ứng và ngược lại.
9. `word_count` phải được tính tự động từ TXT; không coi giá trị nhập tay là bằng chứng cuối cùng.
10. URL nguồn phải được kiểm chứng trước khi tuyên bố provenance đã đạt.

## 6. Dữ liệu giả lập, PII và canary

Internal và Restricted chỉ dùng dữ liệu giả lập, không dùng PII thật. Việc dùng mã giả như `SV-Gxxx`, `GV-Gxxx`, `LOP-Gxx` giúp giảm rủi ro nhưng không thay thế bước rà soát PII.

Canary marker/token (nếu dùng) là chuỗi giả phục vụ phát hiện leakage trong thử nghiệm. Registry canary phải nằm ngoài kho tài liệu được index vào RAG.

## 7. Diễn giải `is_synthetic`

`is_synthetic=false` ở tài liệu Public không có nghĩa TXT là bản sao nguyên văn nguồn chính thức. Nó chỉ biểu thị tài liệu được diễn giải từ một nguồn công khai xác định, thay vì là tình huống nghiệp vụ giả lập.
