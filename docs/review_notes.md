# BIÊN BẢN REVIEW DỮ LIỆU TÀI LIỆU (REVIEW NOTES)

**Ngày thực hiện:** 30/10/2026  
**Dự án:** Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường  
**Mục tiêu:** Rà soát và kiểm định toàn diện chất lượng 50 tài liệu hiện hữu trước khi bổ sung lên hơn 80 tài liệu.

---

## 1. Bảng checklist kiểm tra chất lượng

| Hạng mục kiểm tra | Câu hỏi cần trả lời | Tiêu chuẩn đánh giá | Kết quả rà soát thực tế | Cách xử lý |
|---|---|---|---|---|
| **Nội dung vs Classification** | Nội dung có đúng với mức Public/Internal/Restricted không? | Public: thông tin chung; Internal: quy trình nội bộ/mô phỏng nghiệp vụ trường; Restricted: hồ sơ cá nhân giả định | **ĐẠT (50/50)**: Phân loại chuẩn xác, phản ánh đúng tính chất từng nhóm tài liệu | Duy trì phân loại hiện tại |
| **allowed_roles** | Quyền gán có đúng quy tắc không? | Public: `SinhVien`, `GiangVien`, `QuanTri`<br>Internal: `GiangVien`, `QuanTri`<br>Restricted: `QuanTri` | **ĐẠT (50/50)**: 100% khớp quy tắc phân quyền RBAC đề ra | Không cần chỉnh sửa |
| **doc_id** | Có bị trùng mã không? | Mã định danh duy nhất theo cú pháp `DOC-{P/I/R}XXX` | **ĐẠT**: 50 mã phân bố chuẩn: DOC-P001..P020, DOC-I001..I018, DOC-R001..R012; không trùng lặp | Giữ nguyên hệ thống mã |
| **Tên file & file_path** | Có đúng tiền tố DOC-P / DOC-I / DOC-R không? Đường dẫn có khớp file thực tế? | Tên file chứa tiền tố phân loại, nằm đúng thư mục `public/`, `internal/`, `restricted/` | **PHÁT HIỆN LỖI (1 lỗi)**: Tại bản ghi `DOC-P001`, `file_path` trong metadata ghi là `...DOC-P001_quy_che_dao_tao_dai_hoc_nam_2026.txt` nhưng file thực tế trên ổ đĩa là `...DOC-P001_quy_che_dao_tao.txt` | Cập nhật `file_path` trong cả `documents_metadata.json` và `documents_metadata.csv` đồng bộ với tên file thực tế `data/documents/public/DOC-P001_quy_che_dao_tao.txt` |
| **Độ dài nội dung** | Có quá ngắn (< 100 từ) hoặc quá dài (> 450 từ) không? | Độ dài thiết kế chuẩn từ 150 - 400 từ | **ĐẠT (50/50)**: Tất cả tài liệu đều đạt độ dài từ 300 đến 400 từ | Giữ nguyên |
| **Dữ liệu thật** | Có vô tình dùng tên/MSSV/điểm thật không? | Không lộ lọt PII (Personally Identifiable Information) thật; mã nhân vật giả lập dùng tiền tố `SV-Gxxx`, `GV-Gxxx`, `LOP-Gxx` | **ĐẠT (50/50)**: Các tài liệu Restricted và Internal đều ghi rõ tuyên bố giả lập mô phỏng, dùng mã giả định | Đảm bảo các tài liệu bổ sung mới tuân thủ nghiêm ngặt chuẩn này |

---

## 2. Chi tiết lỗi và hành động khắc phục

### Lỗi #001: Lệch file_path tại DOC-P001
- **Vị trí lỗi:** File `data/metadata/documents_metadata.json` và `data/metadata/documents_metadata.csv`
- **Giá trị ban đầu:** `data/documents/public/DOC-P001_quy_che_dao_tao_dai_hoc_nam_2026.txt`
- **Giá trị thực tế file:** `data/documents/public/DOC-P001_quy_che_dao_tao.txt`
- **Nguyên nhân:** Lỗi đồng bộ khi biên soạn tên file và metadata trước đó.
- **Hành động đã xử lý:** Đã đồng bộ đường dẫn trong metadata trỏ chính xác về `data/documents/public/DOC-P001_quy_che_dao_tao.txt`. Hệ thống kiểm tra tự động xác nhận 100% tài liệu liên kết thành công.

---

## 3. Kế hoạch bổ sung tài liệu (Đợt 2: Nâng tổng số tài liệu lên > 80)

Nhằm đáp ứng mục tiêu mở rộng bộ dữ liệu lên 90–100 tài liệu phục vụ thử nghiệm RAG và kiểm soát truy cập, nhóm phân công:

- **Thành viên 1:** Viết thêm 18 tài liệu Public (`DOC-P021` đến `DOC-P038`), nâng tổng số Public từ 20 lên 38.
- **Thành viên 2:** Viết thêm 16 tài liệu Internal (`DOC-I019` đến `DOC-I034`), nâng tổng số Internal từ 18 lên 34.
- **Thành viên 3:** Viết thêm 12 tài liệu Restricted (`DOC-R013` đến `DOC-R024`), nâng tổng số Restricted từ 12 lên 24.

**Tổng cộng sau bổ sung:** 96 tài liệu (Đạt mục tiêu 90 – 100 tài liệu).

