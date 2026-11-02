# BIÊN BẢN REVIEW DỮ LIỆU (REVIEW NOTES)

## 1. Phạm vi

Review metadata và, khi có thư mục TXT, đối soát toàn bộ tài liệu thực tế.

## 2. Lỗi đã biết và cách khắc phục

### R-001 — DOC-P001 lệch `file_path`

Metadata đã được chuẩn hóa về:
`data/documents/public/DOC-P001_quy_che_dao_tao.txt`.

### R-002 — CSV `allowed_roles` không đồng nhất

Nguyên nhân: một số record được serialize thành chuỗi biểu diễn list Python.
Khắc phục: CSV chuẩn dùng dấu `|`; JSON tiếp tục dùng array.

### R-003 — Thuật ngữ “Authentication”

`role_manager.py` hiện chỉ mô phỏng/chọn vai trò, chưa xác thực danh tính. Báo cáo phải gọi đúng là role simulation + RBAC testing.

## 3. Checklist sau mở rộng

- [ ] JSON parse thành công.
- [ ] CSV parse thành công.
- [ ] JSON ↔ CSV cùng số record và cùng `doc_id`.
- [ ] Không trùng `doc_id`.
- [ ] Prefix ↔ classification đúng.
- [ ] Folder ↔ classification đúng.
- [ ] `allowed_roles` đúng.
- [ ] `retention_days` đúng.
- [ ] `created_date` hợp lệ.
- [ ] `data_origin` ↔ `is_synthetic` hợp lý.
- [ ] 100% `file_path` tồn tại.
- [ ] `word_count` được tính lại từ TXT.
- [ ] Internal/Restricted được rà soát PII.
- [ ] URL nguồn được kiểm chứng.
- [ ] Canary registry (nếu có) không được index vào RAG.

## 4. Nguyên tắc kết luận

Không ghi “96/96 đạt”, “không có PII”, “100% liên kết thành công” hoặc “PASS” nếu chưa có output validation làm bằng chứng.

## 5. Bằng chứng cần lưu

Lưu output của validation tại `tests/validation_report.txt` và commit cùng phiên bản metadata đã kiểm tra.
