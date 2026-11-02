# Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường

## 1. Mục tiêu

Prototype minh họa các biện pháp bảo vệ dữ liệu cho trợ lý AI/RAG nội bộ. Hệ thống sử dụng ba mức phân loại tài liệu (`Public`, `Internal`, `Restricted`) và ba ngữ cảnh vai trò (`SinhVien`, `GiangVien`, `QuanTri`).

Trọng tâm của prototype là **RBAC ở mức tài liệu, pre-retrieval authorization, output filtering, logging/audit và kiểm thử rò rỉ/vượt quyền**.

> `role_manager.py` hiện mô phỏng vai trò phục vụ kiểm thử. Đây chưa phải cơ chế authentication danh tính production.

## 2. RBAC Matrix

| Vai trò   | Public | Internal | Restricted |
| --------- | ------ | -------- | ---------- |
| SinhVien  | ALLOW  | DENY     | DENY       |
| GiangVien | ALLOW  | ALLOW    | DENY       |
| QuanTri   | ALLOW  | ALLOW    | ALLOW      |

Quy tắc thực thi trực tiếp:

`AccessAllowed(user_role, document) = user_role ∈ document.allowed_roles`

## 3. Kiến trúc runtime

```text
Người dùng
    ↓
Role Manager
    ↓
Input Guard
    ↓
Permission Checker
    ↓
Authorized Document Set
    ↓
Vector Retrieval
    ↓
Local LLM
    ↓
Output Filter
    ↓
Câu trả lời

Các sự kiện quan trọng → Security/Audit Log
```

**Yêu cầu quan trọng:** tài liệu trái quyền phải bị loại trước khi trở thành context của mô hình. Kiểm tra lại kết quả retrieval chỉ là defense-in-depth, không thay thế pre-retrieval authorization.

## 4. Cấu trúc thư mục

```text
project/
├── data/
│   ├── documents/
│   │   ├── public/
│   │   ├── internal/
│   │   └── restricted/
│   └── metadata/
│       ├── documents_metadata.json
│       └── documents_metadata.csv
├── docs/
│   ├── data_flow_diagram.drawio
│   ├── data_flow_diagram.svg
│   ├── threat_model.drawio
│   ├── threat_model.svg
│   ├── data_dictionary.md
│   ├── statistics.md
│   └── review_notes.md
├── src/
│   ├── auth/
│   │   ├── role_manager.py
│   │   └── permission_checker.py
│   ├── retrieval/
│   ├── security/
│   └── main.py
└── tests/
    └── test_permission_checker.py
```

## 5. Vai trò của `permission_checker.py`

`PermissionChecker` không quyết định quyền từ tên classification bằng một bảng hard-code thứ hai. Quyền tài liệu được lấy trực tiếp từ metadata `allowed_roles`.

Ví dụ:

```python
checker = PermissionChecker()

authorized, denied = checker.filter_authorized_metadata(
    user_role=current_role,
    documents=metadata_records,
)
```

Sau bước này, **chỉ `authorized` mới được chuyển sang retrieval/index selection**.

Có thể ghi các `denied` vào security log với các trường như `timestamp`, `role`, `doc_id`, `action`, `decision`, `reason`. Không ghi toàn bộ nội dung Restricted vào log.

## 6. Chạy kiểm thử

Tại thư mục gốc dự án:

```bash
python tests/test_permission_checker.py
```

Kết quả mong đợi:

```text
PERMISSION CHECKER TEST: PASS
```

Có thể chạy demo:

```bash
python src/auth/permission_checker.py
```

Kết quả logic mong đợi:

- SinhVien: chỉ Public.
- GiangVien: Public + Internal.
- QuanTri: Public + Internal + Restricted.

## 7. Luồng RAG an toàn đề xuất

### 7.1 Ingestion/indexing

1. Đọc TXT và metadata.
2. Validate metadata.
3. Chunk tài liệu.
4. Gắn `doc_id`, `classification`, `allowed_roles` vào metadata của chunk.
5. Tạo embedding.
6. Lưu vector store trong môi trường do nhóm kiểm soát.

### 7.2 Query/runtime

1. Thiết lập role thử nghiệm.
2. Nhận câu hỏi.
3. Input Guard kiểm tra input bất thường.
4. Permission Checker tạo tập tài liệu được phép.
5. Retrieval chỉ tìm trên phạm vi được phép.
6. Context được gửi cho **local LLM**.
7. Output Filter kiểm tra nội dung nhạy cảm/canary.
8. Trả câu trả lời.
9. Ghi audit/security log đã làm sạch.

## 8. Mô hình đe dọa

Các nhóm đe dọa chính:

- giả mạo/chọn sai role;
- privilege escalation;
- prompt injection;
- ACL bypass;
- retrieval tài liệu trái quyền;
- leakage qua output;
- log chứa dữ liệu nhạy cảm;
- log tampering;
- excessive retention;
- tool permission quá rộng;
- denial of service;
- admin abuse.

Sơ đồ chi tiết nằm trong `docs/threat_model.drawio`.

## 9. Kiểm thử bắt buộc

Theo yêu cầu đề tài, test set cuối cùng phải có:

- ít nhất 25 truy vấn bình thường;
- ít nhất 15 truy vấn vượt quyền/rò rỉ;
- đo correct-answer;
- correct-refusal;
- leakage;
- latency trước/sau control;
- phân tích false refusal và residual leakage.

## 10. An toàn dữ liệu

Chỉ dùng dữ liệu giả lập hoặc dữ liệu công khai được phép. Không gửi Internal/Restricted thật lên dịch vụ AI công cộng. Với prototype này, inference được thiết kế theo hướng mô hình chạy cục bộ/môi trường do nhóm kiểm soát.

## 11. Trạng thái hiện tại

Giai đoạn hiện tại đã có nền tảng metadata/RBAC và thiết kế DFD/threat model. Các bước tiếp theo là tích hợp Permission Checker với retrieval, local LLM, output filter, security logger và bộ test tái lập.
