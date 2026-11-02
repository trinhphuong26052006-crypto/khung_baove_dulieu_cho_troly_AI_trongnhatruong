# MÔ HÌNH ĐE DỌA (THREAT MODEL)

## 1. Mục tiêu và phạm vi đánh giá

Tài liệu này mô hình hóa đe dọa cho prototype **“Khung bảo vệ dữ liệu cho trợ lý trí tuệ nhân tạo dùng trong nhà trường”**.

Mục tiêu là xác định tài sản, ranh giới tin cậy, bề mặt tấn công, phân tích theo STRIDE, ánh xạ Threat → Control → Implementation → Test → Evidence và xác định residual risk.

Phạm vi gồm: tài liệu Public/Internal/Restricted, metadata, role context, Permission Checker, retrieval/vector store, local LLM, output filter, security/audit log và tools/integrations nếu có.

> Prototype hiện mô phỏng `SinhVien`, `GiangVien`, `QuanTri`; chọn role phục vụ kiểm thử RBAC, chưa phải authentication production.

## 2. Kiến trúc, luồng dữ liệu và Trust Boundary

### 2.1 Luồng runtime

`Người dùng → Role Manager → Input Guard → Permission Checker → Authorized Retrieval → Local LLM → Output Filter → Người dùng`

Sự kiện bảo mật quan trọng được ghi vào Security/Audit Log đã làm sạch.

### 2.2 Luồng RAG

1. Nhận query và role context.
2. Input Guard kiểm tra input bất thường.
3. Permission Checker áp dụng `AccessAllowed(user_role, document) = user_role ∈ document.allowed_roles`.
4. Tài liệu trái quyền bị loại trước khi trở thành candidate/context.
5. Retrieval tìm trong phạm vi được phép.
6. Context được đưa vào local LLM/môi trường do nhóm kiểm soát.
7. Output Filter kiểm tra leakage, dữ liệu nhạy cảm và canary.
8. Trả câu trả lời.
9. Ghi ALLOW/DENY và sự kiện cần thiết nhưng không ghi thừa nội dung nhạy cảm.

### 2.3 Trust Boundary

Backend, metadata, documents, vector store, local LLM và security log nằm trong môi trường prototype do nhóm kiểm soát. User input, retrieved content và dữ liệu từ integration/tool phải được xem là dữ liệu không tin cậy. Prompt và nội dung tài liệu không được phép thay thế chính sách hệ thống.

## 3. Tài sản cần bảo vệ

| ID   | Asset                     | Nội dung                                 | Thuộc tính chính                         |
| ---- | ------------------------- | ---------------------------------------- | ---------------------------------------- |
| A-01 | Documents                 | Public/Internal/Restricted               | Confidentiality, Integrity               |
| A-02 | Metadata/ACL              | classification, allowed_roles, retention | Integrity, Confidentiality               |
| A-03 | Role Context              | SinhVien/GiangVien/QuanTri               | Integrity                                |
| A-04 | Prompt/Conversation       | query và context                         | Confidentiality, Integrity               |
| A-05 | Vector Store              | chunks, vectors, metadata                | Confidentiality, Integrity               |
| A-06 | Model/System Instructions | model, system policy                     | Integrity, Confidentiality               |
| A-07 | Output                    | answer trước/sau filtering               | Confidentiality, Integrity               |
| A-08 | Security/Audit Logs       | ALLOW/DENY, lỗi, evidence                | Integrity, Confidentiality, Auditability |
| A-09 | Tools/Integrations        | chức năng hệ thống gọi                   | Least privilege, Integrity               |
| A-10 | Test Evidence             | query set, leakage/canary/results        | Integrity, Reproducibility               |

## 4. Tác nhân và bề mặt tấn công

Tác nhân gồm người dùng hợp lệ nhưng cố vượt quyền, người nhập prompt độc hại, tài liệu chứa malicious instruction, người có quyền cao lạm dụng quyền, tool cấu hình quá rộng và lỗi tích hợp làm bỏ qua ACL.

Bề mặt tấn công: role context, prompt, metadata/ACL, ingestion/indexing, retrieval, retrieved context, LLM inference, output, tools và logs.

## 5. Phân tích theo STRIDE

**S** Spoofing; **T** Tampering; **R** Repudiation; **I** Information Disclosure; **D** Denial of Service; **E** Elevation of Privilege.

### TH-01 — Chọn/giả mạo vai trò [S]

**Asset:** A-03. Nếu role simulation bị hiểu nhầm thành authentication, người dùng có thể tự chọn role cao.  
**Control:** validate role; tách simulation khỏi authentication; production dùng IdP/session đáng tin cậy.  
**Test:** invalid role phải bị từ chối.

### TH-02 — Privilege Escalation [E]

**Asset:** A-01, A-02, A-03. SinhVien cố truy cập Internal/Restricted hoặc GiangVien cố truy cập Restricted.  
**Control:** PermissionChecker, `role ∈ allowed_roles`, fail-closed.  
**Implementation:** `src/auth/permission_checker.py`.  
**Test:** `tests/test_permission_checker.py`.

### TH-03 — Metadata ACL Tampering [T/E]

**Asset:** A-02. `allowed_roles` có thể bị sửa, thiếu hoặc sai kiểu.  
**Control:** metadata validation + fail-closed.  
**Test:** missing/invalid ACL → DENY.

### TH-04 — User Prompt Injection [T]

**Asset:** A-04, A-06. User yêu cầu bỏ qua policy hoặc tiết lộ Restricted.  
**Control:** Input Guard; policy tách khỏi prompt; authorization không phụ thuộc quyết định của LLM.  
**Test:** bypass/prompt-injection queries.

### TH-05 — Malicious Retrieved Instruction [T]

**Asset:** A-01, A-05, A-06. Document có thể chứa instruction thao túng model.  
**Control:** coi retrieved text là untrusted data; tách system policy khỏi document content.  
**Test:** injection-in-document test.

### TH-06 — Unauthorized Retrieval [I/E]

**Asset:** A-01, A-05. Tài liệu trái quyền có thể lọt vào candidate/context.  
**Control:** pre-retrieval authorization + metadata filter + defense-in-depth.  
**Implementation:** `PermissionChecker.filter_authorized_metadata()`.  
**Test:** bypass + canary/leakage tests.

### TH-07 — Sensitive Output Leakage [I]

**Asset:** A-01, A-07. Output có thể chứa dữ liệu không phù hợp do lỗi pipeline/context.  
**Control:** Output Filter + refusal.  
**Evidence:** leakage rate, correct-refusal.

### TH-08 — Canary Leakage [I]

**Asset:** A-01 Restricted, A-07. Canary Restricted xuất hiện trong output trái quyền là bằng chứng leakage.  
**Control:** Canary Detector; registry nằm ngoài dữ liệu index.  
**Test:** canary test.

### TH-09 — Tool Permission quá rộng [E]

**Asset:** A-09. Tool quyền cao có thể bị lợi dụng.  
**Control:** least privilege, allowlist, human approval.  
**Test:** unauthorized-action scenario. Nếu prototype chưa có action tool, đây là threat mở rộng.

### TH-10 — Sensitive/Excessive Logs [I]

**Asset:** A-08. Log toàn bộ prompt/context/output có thể tạo bản sao dữ liệu nhạy cảm.  
**Control:** minimization, sanitization, retention.  
**Test:** log inspection.

### TH-11 — Log/Evidence Tampering [T/R]

**Asset:** A-08, A-10. Sửa/xóa log làm mất auditability.  
**Control:** access control, integrity review, reproducible evidence.  
**Test:** audit review.

### TH-12 — DoS/Admin Abuse [D/E]

**Asset:** availability và tài sản có quyền cao.  
**Control:** rate limiting, monitoring, least privilege, separation of duties.  
**Test:** load/admin-misuse scenario.

## 6. Biện pháp giảm thiểu theo lớp

**Prevent:** data minimization → metadata validation → RBAC → pre-retrieval authorization → local inference → least privilege → output filtering.  
**Detect:** denied-access logging → canary detection → leakage metric → monitoring/audit.  
**Respond:** DENY → security event → sửa/cô lập metadata sai → điều chỉnh control → phân tích false refusal/residual leakage.

## 7. Traceability với Threat Register

`threat_register.md` là bảng truy vết chính thức. ID TH-01…TH-12 phải giống nhau trong hai file.

Ví dụ:  
`TH-02 Privilege Escalation` → `PermissionChecker fail-closed` → `src/auth/permission_checker.py` → `tests/test_permission_checker.py` → `SV→Internal/Restricted = DENY` → evidence test.

Control chưa triển khai hoặc chưa chạy test phải ghi `Planned/Chưa kiểm chứng`, không được ghi PASS.

## 8. Đánh giá rủi ro

Mức rủi ro trong Threat Register là **định tính ban đầu**:

- **Rất cao:** có thể trực tiếp làm lộ dữ liệu trái quyền/phá authorization.
- **Cao:** ảnh hưởng đáng kể tới confidentiality/integrity/availability.
- **Trung bình:** tác động giới hạn hoặc cần thêm điều kiện.

Ưu tiên: TH-02, TH-03, TH-06, TH-07, TH-08. Muốn công bố risk score định lượng phải bổ sung Likelihood × Impact.

## 9. Residual Risk

Sau control vẫn còn: role chưa có authentication thật; prompt injection không thể xử lý chỉ bằng keyword; metadata/integration có thể lỗi; output filter có false positive/negative; model có thể hallucinate; vector store/log cần hardening production; tools tương lai mở rộng attack surface.

## 10. Kế hoạch kiểm chứng

Bộ test cuối cùng cần ≥25 normal queries và ≥15 bypass/leakage attempts; so sánh trước/sau control; đo correct-answer, correct-refusal, leakage, latency; phân tích false refusal và residual leakage.

`tests/*.py` chứa code test; `tests/queries/` chứa input test; `tests/results/` chứa evidence.

## 11. Kết luận

Threat Model xác định 12 threat xuyên suốt role, metadata, retrieval, inference, output, tools và logs. Control trung tâm là **pre-retrieval authorization dựa trên `allowed_roles`**, kết hợp defense-in-depth, output filtering và audit. `threat_register.md` phải được cập nhật đồng thời khi threat/control/test thay đổi.
