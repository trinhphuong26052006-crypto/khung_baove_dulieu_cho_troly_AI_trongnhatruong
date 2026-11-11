# THỐNG KÊ BỘ DỮ LIỆU

## 1. Tổng quan

Bộ dữ liệu được xây dựng để phục vụ đề tài “Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường”.

Tổng cộng có **96 tài liệu** văn bản định dạng `.txt`, được phân thành ba mức bảo mật, hoàn toàn đáp ứng mục tiêu mở rộng quy mô bộ dữ liệu (trên 80 tài liệu, nhóm mục tiêu 90 – 100 tài liệu).

## 2. Thống kê theo mức phân loại (Kết quả PivotTable)

| Mức phân loại | Số lượng ban đầu | Bổ sung mới | Tổng số lượng | Tỷ lệ (%) | Mục tiêu đề ra |
|---|---:|---:|---:|---:|---:|
| **Public** | 20 | +18 | **38** | 39.58% | 35 – 40 (~40%) |
| **Internal** | 18 | +16 | **34** | 35.42% | 30 – 35 (~35%) |
| **Restricted** | 12 | +12 | **24** | 25.00% | 20 – 25 (~25%) |
| **Tổng cộng** | **50** | **+46** | **96** | **100.00%** | **90 – 100 (100%)** |

## 3. Phân quyền truy cập (RBAC Matrix)

| Vai trò | Public | Internal | Restricted |
|---|---|---|---|
| **SinhVien** | Được phép | Không | Không |
| **GiangVien** | Được phép | Được phép | Không |
| **QuanTri** | Được phép | Được phép | Được phép |

## 4. Nguồn dữ liệu

Bộ dữ liệu sử dụng nguồn tham khảo công khai từ các trường đại học Việt Nam, bao gồm:

- Trường Đại học Giao thông vận tải TP.HCM (UT).
- Trường Đại học Khoa học Tự nhiên – ĐHQG-HCM (HCMUS).
- Trường Đại học Mở TP.HCM (OU).
- Trường Đại học Thủ Dầu Một (TDMU).

Trong đó:

- **38 tài liệu Public**: Diễn giải từ các văn bản, quy chế, hướng dẫn học vụ, đào tạo và đời sống sinh viên công khai.
- **34 tài liệu Internal**: Các tình huống nghiệp vụ, kế hoạch điều phối, kiểm toán và báo cáo nội bộ giả lập.
- **24 tài liệu Restricted**: Hồ sơ học vụ cá nhân đặc biệt, kỷ luật, y tế, chế độ tài chính và khiếu nại giả lập (chứa canary token, hoàn toàn không dùng thông tin cá nhân thật).

## 5. Đặc điểm dữ liệu

- **Định dạng nội dung:** TXT (chuẩn UTF-8, cấu trúc rõ ràng từ 150 đến 400 từ/tài liệu).
- **Định dạng metadata:** JSON, CSV và bảng tính Excel (`documents_metadata.xlsx` kèm PivotTable).
- **Quy tắc định danh:** Mã định danh duy nhất (`DOC-Pxxx`, `DOC-Ixxx`, `DOC-Rxxx`).
- **Phân quyền truy cập:** Kiểm soát chặt chẽ qua thuộc tính `allowed_roles`.
- **Chính sách lưu trữ:** Thuộc tính `retention_days` (Public: 365 ngày; Internal: 180 ngày; Restricted: 90 ngày).
- **Bảo vệ quyền riêng tư:** 100% tài liệu nhạy cảm sử dụng định danh giả lập (`SV-Gxxx`, `GV-Gxxx`, `LOP-Gxx`), loại bỏ triệt để nguy cơ rò rỉ PII thực tế.

## 6. Mục đích sử dụng

Bộ dữ liệu phục vụ các hoạt động:

1. Kiểm thử xác thực và phân quyền theo vai trò (RBAC Authentication & Authorization).
2. Kiểm thử kiểm soát truy xuất tài liệu trước khi đưa vào mô hình RAG (Pre-retrieval Access Control).
3. Kiểm thử khả năng ngăn chặn truy cập trái phép vào các tài liệu mật/nội bộ.
4. Kiểm thử lọc thông tin nhạy cảm trong câu trả lời sinh bởi mô hình ngôn ngữ lớn (Post-generation Safety Filter).
5. Ghi nhận kết quả và đánh giá định lượng hiệu quả của các cơ chế bảo vệ.

---

## 7. Lịch sử cập nhật

- **2026-10-23 (Phiên bản 1.0):** Khởi tạo bộ dữ liệu thử nghiệm ban đầu gồm 50 tài liệu (20 Public, 18 Internal, 12 Restricted).
- **2026-10-30 (Phiên bản 2.0):** 
  - Rà soát toàn diện chất lượng dữ liệu: khắc phục lệch đường dẫn `file_path` tại tài liệu `DOC-P001` trong metadata; ghi nhận biên bản rà soát tại `docs/review_notes.md`.
  - **Bổ sung 46 tài liệu mới** (18 tài liệu Public từ `DOC-P021` đến `DOC-P038`; 16 tài liệu Internal từ `DOC-I019` đến `DOC-I034`; 12 tài liệu Restricted từ `DOC-R013` đến `DOC-R024`), nâng tổng số tài liệu từ **50 lên 96 tài liệu** (vượt chỉ tiêu > 80, nằm chuẩn trong khoảng mục tiêu 90 – 100 tài liệu).
  - Xuất toàn bộ siêu dữ liệu sang file bảng tính Excel `data/metadata/documents_metadata.xlsx` và tổng hợp tự động bảng phân tích PivotTable.
