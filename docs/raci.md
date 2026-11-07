# MA TRẬN PHÂN CÔNG TRÁCH NHIỆM (RACI MATRIX)

## 1. Mục đích

RACI này mô tả **trách nhiệm vận hành và quản trị an toàn của hệ thống**, không phải bảng chia việc của ba thành viên làm đồ án.

Các chủ thể:

- **User:** người sử dụng trợ lý.
- **System Administrator:** người vận hành hệ thống và control kỹ thuật.
- **Data Owner:** đơn vị/chủ thể chịu trách nhiệm đối với dữ liệu.
- **Security/Audit Responsible:** người kiểm tra an toàn, log, evidence và sự cố.

## 2. Quy ước

- **R – Responsible:** trực tiếp thực hiện.
- **A – Accountable:** chịu trách nhiệm cuối cùng/phê duyệt.
- **C – Consulted:** được tham vấn.
- **I – Informed:** được thông báo.

Mỗi hoạt động cần có ít nhất một R và nên có một A rõ ràng.

## 3. Ma trận RACI

| Hoạt động                      | User | System Administrator | Data Owner | Security/Audit |
| ------------------------------ | ---- | -------------------- | ---------- | -------------- |
| Gửi câu hỏi hợp lệ             | R    | I                    | I          | I              |
| Tuân thủ Acceptable Use Policy | R    | C                    | A          | C              |
| Xác định classification        | I    | C                    | A/R        | C              |
| Xác định `allowed_roles`       | I    | C                    | A/R        | C              |
| Phê duyệt ngoại lệ truy cập    | I    | C                    | A/R        | C              |
| Quản lý role mapping kỹ thuật  | I    | A/R                  | C          | C              |
| Thực thi Permission Checker    | I    | A/R                  | C          | C              |
| Quản lý authorized retrieval   | I    | A/R                  | C          | C              |
| Quản lý Vector Store           | I    | A/R                  | C          | C              |
| Vận hành Local LLM             | I    | A/R                  | C          | C              |
| Vận hành Input Guard           | I    | A/R                  | C          | C              |
| Vận hành Output Filter         | I    | A/R                  | C          | C              |
| Định nghĩa canary test         | I    | C                    | C          | A/R            |
| Quản lý security/audit log     | I    | R                    | C          | A              |
| Xem xét access DENY bất thường | I    | R                    | C          | A              |
| Xác định retention dữ liệu     | I    | C                    | A/R        | C              |
| Thực hiện xóa dữ liệu          | I    | R                    | A          | C              |
| Xác minh xóa khỏi vector/index | I    | R                    | A          | C              |
| Xây dựng security test         | I    | C                    | C          | A/R            |
| Đánh giá leakage/false refusal | I    | C                    | C          | A/R            |
| Điều tra incident              | C    | R                    | A          | R              |
| Phê duyệt corrective action    | I    | R                    | A          | C              |
| Rà soát policy                 | I    | C                    | A          | R              |

## 4. Liên kết control và trách nhiệm

### TH-02 – Privilege Escalation

- System Administrator: R cho implementation Permission Checker.
- Data Owner: A đối với policy quyền.
- Security/Audit: R/C cho kiểm thử bypass và evidence.

### TH-03 – Metadata/ACL Tampering

- Data Owner: A đối với classification/allowed_roles.
- System Administrator: R bảo vệ metadata và chạy validation.
- Security/Audit: R kiểm tra consistency/evidence.

### TH-06 – Unauthorized Retrieval

- System Administrator: A/R cho pre-retrieval filtering.
- Data Owner: C/A về phạm vi dữ liệu.
- Security/Audit: R cho test chứng minh tài liệu trái quyền không vào context.

### TH-07/TH-08 – Output/Canary Leakage

- System Administrator: R cho Output Filter.
- Security/Audit: A/R cho leakage test và đánh giá.
- Data Owner: C khi xác định mức độ ảnh hưởng.

## 5. RACI trong xử lý sự cố

```text
User/Control phát hiện
        ↓
System Administrator cô lập/thu thập evidence
        ↓
Security/Audit đánh giá
        ↓
Data Owner xác định tác động và quyết định
        ↓
System Administrator khắc phục
        ↓
Security/Audit retest
```

## 6. Ghi chú về nhóm sinh viên

Bảng phân công **Thành viên 1 / Thành viên 2 / Thành viên 3** nếu cần cho quản lý tiến độ nên lưu riêng, ví dụ:

```text
docs/project_team_assignment.md
```

Không dùng bảng chia việc nhóm để thay thế responsibility evidence của hệ thống.
