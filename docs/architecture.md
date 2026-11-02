# KIẾN TRÚC HỆ THỐNG (SYSTEM ARCHITECTURE)

## 1. Mục tiêu và phạm vi

Hệ thống là nguyên mẫu trợ lý AI dùng trong nhà trường, sử dụng tài liệu được phân loại thành ba mức **Public, Internal và Restricted**. Kiến trúc được thiết kế theo nguyên tắc defense-in-depth nhằm giảm nguy cơ truy cập vượt quyền, rò rỉ dữ liệu, prompt injection, lạm dụng công cụ và ghi log quá mức.

Nguyên tắc cốt lõi:

- Kiểm tra quyền **trước retrieval**.
- `documents_metadata.json` là nguồn metadata chuẩn; `allowed_roles` là thuộc tính trực tiếp dùng để ra quyết định truy cập.
- Nếu role hoặc metadata quyền không hợp lệ, hệ thống **fail closed** (DENY).
- Internal/Restricted không được gửi tới dịch vụ AI công cộng.
- Mô hình suy luận được định hướng triển khai cục bộ trong môi trường do nhóm kiểm soát.
- Đầu ra được kiểm tra trước khi trả cho người dùng.
- Sự kiện bảo mật cần được ghi log ở mức tối thiểu cần thiết và tuân thủ retention policy.

## 2. Kiến trúc logic

```text
User
  |
  v
Role Manager
  |
  v
Input Guard
  |
  v
Permission Checker
  |
  v
Authorized Document Scope
  |
  v
Retriever / Vector Store
  |
  v
Local LLM
  |
  v
Output Filter / Canary Check
  |
  v
Answer
  |
  +------------------> Security / Audit Logger
```

### 2.1 Role Manager

`RoleManager` quản lý ngữ cảnh vai trò dùng cho nguyên mẫu gồm `SinhVien`, `GiangVien`, `QuanTri`.

Đây là **mô phỏng vai trò phục vụ kiểm thử**, không được mô tả là cơ chế xác thực danh tính production. Trong hệ thống thực tế, role phải được lấy từ cơ chế đăng nhập/SSO đáng tin cậy.

### 2.2 Input Guard

Input Guard tiếp nhận câu hỏi và thực hiện kiểm tra đầu vào như:

- đầu vào rỗng hoặc bất thường;
- yêu cầu cố tình vượt quyền;
- mẫu prompt injection;
- yêu cầu tiết lộ system prompt, log hoặc tài liệu Restricted;
- dữ liệu không phù hợp với phạm vi nguyên mẫu.

Input Guard là lớp giảm thiểu rủi ro, không thay thế Permission Checker.

### 2.3 Permission Checker

Permission Checker là control trọng tâm của hệ thống.

Quyết định truy cập ở mức tài liệu:

```text
AccessAllowed(user_role, document)
    = user_role ∈ document.allowed_roles
```

Ma trận mặc định:

| Classification | SinhVien | GiangVien | QuanTri |
| -------------- | -------: | --------: | ------: |
| Public         |    ALLOW |     ALLOW |   ALLOW |
| Internal       |     DENY |     ALLOW |   ALLOW |
| Restricted     |     DENY |      DENY |   ALLOW |

Permission Checker phải chạy **trước retrieval** để tạo tập tài liệu được phép trở thành ứng viên tìm kiếm.

### 2.4 Metadata Store

Metadata lưu các trường phục vụ quản trị dữ liệu như `doc_id`, `classification`, `allowed_roles`, `retention_days`, `data_origin`, `is_synthetic`, `source_url`, `word_count`.

`documents_metadata.json` là nguồn chuẩn. CSV/XLSX chỉ là bản dẫn xuất phục vụ kiểm tra và báo cáo.

### 2.5 Document Store

Tài liệu TXT được chia thành:

```text
data/documents/public/
data/documents/internal/
data/documents/restricted/
```

`file_path` trong metadata phải ánh xạ đúng tới tài liệu tương ứng.

### 2.6 Vector Store / Retriever

Retriever chỉ được tìm kiếm trên **authorized scope** đã được Permission Checker chấp thuận. Không sử dụng quy trình “retrieve toàn bộ rồi mới lọc quyền” làm control chính.

Một lớp kiểm tra sau retrieval có thể được dùng như defense-in-depth để loại kết quả ngoài phạm vi dự kiến.

### 2.7 Local LLM

Mô hình ngôn ngữ nhận câu hỏi và context đã qua kiểm soát. Với Internal/Restricted, nguyên mẫu phải ưu tiên mô hình chạy cục bộ, ví dụ thông qua Ollama, để tránh đưa dữ liệu nhạy cảm ra dịch vụ AI công cộng.

### 2.8 Output Filter

Output Filter kiểm tra câu trả lời trước khi phát hành, tập trung vào:

- dấu hiệu rò rỉ nội dung không được phép;
- canary token;
- nội dung Restricted xuất hiện trong phiên không có quyền;
- system instruction hoặc dữ liệu vận hành nhạy cảm;
- kết quả cần từ chối an toàn.

Output Filter là defense-in-depth, không thay thế pre-retrieval authorization.

### 2.9 Security / Audit Logger

Logger ghi các sự kiện cần thiết như:

- role;
- thời điểm;
- loại hành động;
- `doc_id` liên quan khi phù hợp;
- ALLOW/DENY;
- lý do từ chối;
- loại cảnh báo bảo mật;
- latency/evaluation data cần thiết.

Không ghi toàn bộ nội dung nhạy cảm vào log nếu không cần thiết.

## 3. Luồng xử lý end-to-end

1. Người dùng gửi câu hỏi.
2. Hệ thống lấy role hiện tại.
3. Input Guard kiểm tra đầu vào.
4. Permission Checker lọc metadata theo `allowed_roles`.
5. Hệ thống tạo authorized document scope.
6. Retriever tìm kiếm trong phạm vi đã được phép.
7. Context được đưa vào Local LLM.
8. Output Filter kiểm tra câu trả lời.
9. Câu trả lời hợp lệ được trả cho người dùng.
10. Sự kiện cần thiết được ghi vào audit/security log.

Nếu bất kỳ bước kiểm soát quyền quan trọng nào không xác định được trạng thái hợp lệ, hệ thống ưu tiên DENY.

## 4. Pre-Retrieval Authorization

Pre-retrieval authorization là yêu cầu kiến trúc quan trọng nhất đối với bảo vệ dữ liệu.

Ví dụ `SinhVien`:

```text
96 metadata records
        |
Permission Checker
        |
        +--> Public: authorized
        +--> Internal: denied
        +--> Restricted: denied
        |
        v
Retriever chỉ nhận Public scope
```

Nhờ vậy Internal/Restricted không trở thành context ứng viên cho phiên SinhVien.

## 5. Defense in Depth

| Lớp | Control              | Mục đích                       |
| --- | -------------------- | ------------------------------ |
| 1   | Role Context         | Xác định ngữ cảnh quyền        |
| 2   | Input Guard          | Phát hiện đầu vào nguy hiểm    |
| 3   | Permission Checker   | Ngăn tài liệu vượt quyền       |
| 4   | Authorized Retrieval | Giới hạn tập tìm kiếm          |
| 5   | Local LLM            | Giảm truyền dữ liệu ra ngoài   |
| 6   | Output Filter        | Phát hiện rò rỉ còn sót        |
| 7   | Audit Logging        | Hỗ trợ phát hiện/điều tra      |
| 8   | Retention            | Giảm thời gian tồn tại dữ liệu |

## 6. Trust Boundaries

Các ranh giới tin cậy chính:

- **TB-01 User → Application:** đầu vào người dùng không được mặc định tin cậy.
- **TB-02 Application → Metadata/Document Store:** metadata quyền phải được bảo vệ khỏi sửa trái phép.
- **TB-03 Authorized Scope → Retriever:** chỉ tài liệu đã được phép mới đi qua.
- **TB-04 Retriever → LLM:** retrieved content có thể chứa malicious instruction.
- **TB-05 LLM → Output:** đầu ra mô hình không mặc định an toàn.
- **TB-06 Application → Log Store:** log phải hạn chế dữ liệu nhạy cảm và chống sửa trái phép.

## 7. Fail-Closed Design

Các trường hợp sau phải DENY hoặc dừng an toàn:

- role không hợp lệ;
- thiếu `allowed_roles`;
- metadata quyền sai định dạng;
- tài liệu không xác định classification;
- control quyền không hoạt động;
- kết quả retrieval không chứng minh được thuộc authorized scope.

## 8. Logging và Retention

Retention mặc định của dataset:

| Classification | Retention |
| -------------- | --------: |
| Public         |  365 ngày |
| Internal       |  180 ngày |
| Restricted     |   90 ngày |

Thời hạn log phải được định nghĩa riêng theo mục đích kiểm toán và nguyên tắc tối thiểu hóa dữ liệu; không tự động đồng nhất log retention với document retention nếu chưa có quyết định chính sách.

## 9. Liên kết Threat Model

Kiến trúc liên kết với `threat_model.md` và `threat_register.md`.

Các threat ưu tiên gồm:

- TH-02: privilege escalation;
- TH-03: metadata/ACL tampering;
- TH-06: unauthorized retrieval;
- TH-07: sensitive output leakage;
- TH-08: canary leakage.

Chuỗi bằng chứng:

```text
Architecture
→ DFD
→ Threat Model
→ Threat Register
→ Control
→ Test
→ Evidence
```

## 10. Giới hạn của nguyên mẫu

- Role hiện tại là role simulation, chưa phải production authentication.
- Input Guard, Output Filter, logger và RAG integration chỉ được đánh dấu hoàn thành sau khi code/test tương ứng tồn tại.
- URL nguồn Public phải được xác minh riêng.
- Không được tuyên bố leakage bằng 0 nếu chưa hoàn tất bộ kiểm thử.
- Chỉ sử dụng dữ liệu giả lập hoặc dữ liệu công khai được phép.
