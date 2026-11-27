# HƯỚNG DẪN SINH VIÊN – permission_checker.py và README.md

## A. `permission_checker.py` đặt ở đâu?

Tạo file: `src/auth/permission_checker.py`.

Không đặt logic này trong UI và không để UI tự quyết định quyền. UI chỉ chuyển role/query; backend mới thực thi authorization.

## B. Vì sao không dùng `classification` làm quyết định cuối cùng?

`classification` mô tả độ nhạy. `allowed_roles` là chính sách quyền trực tiếp của từng tài liệu. Vì vậy:
`role in document["allowed_roles"]` là quyết định document-level.

Nếu vừa hard-code matrix theo classification vừa dùng `allowed_roles`, hệ thống có hai nguồn chính sách và có nguy cơ lệch nhau.

## C. Các hàm sinh viên cần hiểu

1. `_normalize_allowed_roles`: chuẩn hóa JSON array/CSV `|`.
2. `check_document`: trả ALLOW/DENY + reason.
3. `filter_authorized_metadata`: cổng pre-retrieval chính.
4. `filter_retrieved_results`: defense-in-depth sau retrieval.

## D. Fail closed

Nếu role không hợp lệ hoặc `allowed_roles` bị thiếu/hỏng → DENY. Không mặc định ALLOW.

## E. Tích hợp vào main/retrieval

Sai:

```python
results = vector_store.search(query)
safe_results = checker.filter_retrieved_results(role, results)
```

nếu vector store đã đưa tài liệu trái quyền vào candidate/context.

Đúng về mặt thiết kế:

```python
authorized_metadata, denied = checker.filter_authorized_metadata(
    current_role, metadata_records
)

results = retriever.search(
    query=query,
    allowed_doc_ids=[x["doc_id"] for x in authorized_metadata]
)
```

Nếu vector DB hỗ trợ metadata filter, nên filter trực tiếp theo role/doc_id tại truy vấn.

## F. README phải trả lời được 7 câu

1. Đề tài giải quyết vấn đề gì?
2. Có những role/classification nào?
3. Kiến trúc chạy như thế nào?
4. Quyền được kiểm tra ở đâu?
5. Chạy project/test bằng lệnh nào?
6. Dữ liệu nào được phép sử dụng?
7. Bằng chứng đánh giá nào sẽ được tạo?

File `README.md` đi kèm đã viết theo cấu trúc này.
