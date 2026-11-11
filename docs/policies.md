# CHÍNH SÁCH BẢO MẬT VÀ QUẢN TRỊ DỮ LIỆU (POLICIES)

## 1. Mục đích và phạm vi

Tài liệu này quy định các nguyên tắc sử dụng, phân loại, truy cập, ghi log, lưu giữ, hủy dữ liệu và xử lý sự cố cho nguyên mẫu trợ lý AI dùng trong nhà trường.

Phạm vi áp dụng gồm tài liệu, metadata, vector store, prompt/context, model/system instructions, output, log và các công cụ tích hợp.

## 2. Chính sách sử dụng hợp lệ (Acceptable Use Policy)

### 2.1 Được phép

- Tra cứu thông tin phục vụ học tập, giảng dạy và quản trị theo đúng quyền.
- Sử dụng dữ liệu Public và dữ liệu giả lập được nhóm chuẩn bị.
- Thực hiện security testing trong bộ test được kiểm soát.
- Ghi nhận kết quả phục vụ đánh giá độ chính xác và an toàn.

### 2.2 Không được phép

- Cố tình truy cập tài liệu ngoài quyền.
- Yêu cầu hệ thống tiết lộ Restricted/Internal khi role không được phép.
- Đưa dữ liệu nội bộ thật hoặc dữ liệu cá nhân thật vào dịch vụ AI công cộng.
- Sửa metadata quyền, log hoặc evidence để làm sai lệch kết quả.
- Sử dụng trợ lý để thực hiện hành động nhạy cảm mà không có phê duyệt con người phù hợp.

## 3. Chính sách phân loại dữ liệu

### 3.1 Public

Thông tin công khai hoặc nội dung được diễn giải từ nguồn công khai đã xác định.

Quyền mặc định:

```text
SinhVien, GiangVien, QuanTri
```

Retention dataset: **365 ngày**.

### 3.2 Internal

Tài liệu giả lập mô phỏng thông tin vận hành nội bộ.

Quyền mặc định:

```text
GiangVien, QuanTri
```

Retention dataset: **180 ngày**.

### 3.3 Restricted

Tài liệu giả lập có mức nhạy cảm cao, ví dụ hồ sơ cá nhân giả định, kỷ luật, tài chính hoặc sự cố.

Quyền mặc định:

```text
QuanTri
```

Retention dataset: **90 ngày**.

## 4. Chính sách kiểm soát truy cập (Access Control Policy)

### 4.1 RBAC

| Classification | SinhVien | GiangVien | QuanTri |
| -------------- | -------: | --------: | ------: |
| Public         |    ALLOW |     ALLOW |   ALLOW |
| Internal       |     DENY |     ALLOW |   ALLOW |
| Restricted     |     DENY |      DENY |   ALLOW |

### 4.2 Quy tắc quyết định

```text
AccessAllowed(user_role, document)
    = user_role ∈ document.allowed_roles
```

`allowed_roles` trong metadata là nguồn trực tiếp để Permission Checker ra quyết định ở mức tài liệu.

### 4.3 Pre-Retrieval Enforcement

Permission check phải diễn ra trước retrieval. Tài liệu bị DENY không được trở thành candidate context của phiên người dùng.

### 4.4 Fail Closed

Hệ thống phải DENY khi:

- role không hợp lệ;
- thiếu hoặc hỏng `allowed_roles`;
- metadata không xác định được;
- control quyền gặp lỗi;
- kết quả retrieval nằm ngoài authorized scope.

### 4.5 Defense in Depth

Có thể kiểm tra quyền lần hai sau retrieval nhưng không được dùng lớp này để thay thế pre-retrieval authorization.

## 5. Chính sách an toàn AI/RAG

- Retrieved content được xem là dữ liệu không hoàn toàn đáng tin cậy.
- Không thực thi instruction nằm trong tài liệu retrieved chỉ vì nó xuất hiện trong context.
- Internal/Restricted không được chuyển đến public AI service.
- Output phải được kiểm tra trước khi trả cho người dùng.
- Canary token, nếu được sử dụng, chỉ phục vụ phát hiện leakage trong dữ liệu giả lập.
- Registry của canary không được đưa vào vector store/context.
- Công cụ có khả năng tạo thay đổi hoặc hành động nhạy cảm phải yêu cầu quyền tối thiểu và phê duyệt phù hợp.

## 6. Chính sách ghi log và kiểm toán

### 6.1 Mục đích

Log phục vụ:

- phát hiện truy cập bị từ chối;
- điều tra sự cố;
- đánh giá control;
- tái lập kết quả test;
- theo dõi leakage/false refusal/latency.

### 6.2 Dữ liệu nên ghi

- timestamp;
- test/session identifier giả lập;
- role;
- loại sự kiện;
- `doc_id` khi cần;
- ALLOW/DENY;
- reason code;
- loại cảnh báo;
- latency;
- kết quả đánh giá.

### 6.3 Dữ liệu không nên ghi mặc định

- toàn bộ Restricted document;
- prompt chứa dữ liệu nhạy cảm không cần thiết;
- toàn bộ context;
- credential/token;
- dữ liệu cá nhân thật.

### 6.4 Integrity

Security log/evidence phải được hạn chế quyền sửa. Kết quả test đã dùng làm bằng chứng không được chỉnh tay để làm thay đổi kết luận.

## 7. Chính sách lưu giữ dữ liệu

| Loại                 | Thời hạn mặc định |
| -------------------- | ----------------: |
| Public documents     |          365 ngày |
| Internal documents   |          180 ngày |
| Restricted documents |           90 ngày |

Retention của log phải được quy định theo mục đích kiểm toán và tối thiểu hóa dữ liệu. Nếu chưa triển khai cơ chế xóa tự động, báo cáo phải ghi rõ đây là control chưa hoàn thiện.

## 8. Chính sách hủy dữ liệu

Khi hết retention hoặc có quyết định hợp lệ:

1. xác định dữ liệu cần xóa;
2. kiểm tra phụ thuộc/index/vector representation;
3. xóa tài liệu nguồn;
4. xóa/chỉnh index liên quan;
5. xử lý metadata theo quy tắc lưu vết phù hợp;
6. ghi nhận sự kiện hủy;
7. xác minh dữ liệu không còn được retrieval trả về.

Không tuyên bố “đã xóa an toàn” nếu chỉ xóa TXT nhưng vector/index vẫn còn.

## 9. Chính sách xử lý sự cố

Các sự kiện cần xem xét như incident:

- truy cập Internal/Restricted trái quyền;
- leakage/canary xuất hiện trong output trái phép;
- metadata ACL bị sửa;
- log bị xóa/sửa trái phép;
- dữ liệu nhạy cảm bị gửi ra dịch vụ bên ngoài;
- control quan trọng không hoạt động.

Quy trình:

```text
Detect
→ Contain
→ Preserve Evidence
→ Assess Impact
→ Correct Control
→ Retest
→ Document Residual Risk
```

## 10. Ngoại lệ chính sách

Ngoại lệ quyền truy cập phải:

- có lý do;
- được Data Owner phê duyệt;
- có phạm vi và thời hạn;
- được ghi nhận;
- được thu hồi khi hết nhu cầu.

Trong dataset hiện tại, policy mặc định vẫn là Restricted chỉ cho `QuanTri`.

## 11. Trách nhiệm

- **User:** sử dụng đúng mục đích và không cố vượt quyền.
- **System Administrator:** vận hành control, log, retrieval và cấu hình hệ thống.
- **Data Owner:** quyết định classification, quyền truy cập, retention và ngoại lệ.
- **Security/Audit Responsible:** đánh giá evidence, incident và hiệu quả control.

Chi tiết tại `raci.md`.

## 12. Rà soát chính sách

Policy phải được rà soát khi:

- thay đổi classification/RBAC;
- thêm nguồn dữ liệu;
- thêm tool/integration;
- thay đổi LLM;
- phát hiện leakage;
- thay đổi retention;
- có incident hoặc kết quả test cho thấy control không phù hợp.
