# THỐNG KÊ BỘ DỮ LIỆU

## 1. Tổng quan

Bộ dữ liệu hiện có **96 metadata records**:

- Public: **38** (39.58%)
- Internal: **34** (35.42%)
- Restricted: **24** (25.00%)

Các con số trên được tính trực tiếp từ metadata. Việc khẳng định đủ 96 file TXT tồn tại, `word_count` chính xác và không có PII thật chỉ được thực hiện sau khi chạy validation trên thư mục tài liệu thực tế.

## 2. RBAC Matrix

| Vai trò   | Public    | Internal  | Restricted |
| --------- | --------- | --------- | ---------- |
| SinhVien  | Được phép | Không     | Không      |
| GiangVien | Được phép | Được phép | Không      |
| QuanTri   | Được phép | Được phép | Được phép  |

## 3. Chính sách lưu trữ trong prototype

- Public: 365 ngày.
- Internal: 180 ngày.
- Restricted: 90 ngày.

Đây là chính sách thử nghiệm của prototype, không được diễn giải thành thời hạn lưu trữ pháp lý của các trường tham khảo.

## 4. Nguồn và tính giả lập

Public được mô tả bằng `official_public_paraphrase`; Internal/Restricted dùng `synthetic_based_on_public_context`. Các URL phải được kiểm chứng riêng trước khi kết luận provenance đạt yêu cầu.

## 5. Mục đích sử dụng

1. Mô phỏng ba ngữ cảnh vai trò để kiểm thử RBAC.
2. Kiểm thử pre-retrieval access control.
3. Kiểm thử truy vấn vượt quyền/rò rỉ.
4. Kiểm thử post-generation safety filter.
5. Ghi log và tính correct-answer, correct-refusal, leakage, latency.
6. Phân tích false refusal và residual leakage.

## 6. Lưu ý về xác thực

Prototype hiện mô phỏng vai trò để kiểm thử phân quyền; việc người dùng tự chọn `SinhVien/GiangVien/QuanTri` **không phải cơ chế authentication danh tính thực tế**.

## 7. Trạng thái validation

Chỉ ghi `PASS` khi `scripts/validate_dataset.py` đã được chạy với đầy đủ thư mục `data/documents/` và không còn lỗi bắt buộc.
