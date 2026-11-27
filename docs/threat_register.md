# THREAT REGISTER

## 1. Mục đích

Đây là bảng truy vết của `threat_model.md`. Hai file dùng chung ID **TH-01 → TH-12**.

`Threat → Control → Implementation → Test → Evidence`

Control chưa triển khai/chưa test không được ghi PASS.

## 2. Quy ước STRIDE

**S** Spoofing · **T** Tampering · **R** Repudiation · **I** Information Disclosure · **D** Denial of Service · **E** Elevation of Privilege.

## 3. Threat Register

| ID    | Asset/điểm tấn công     | STRIDE | Đe dọa                            | Rủi ro ban đầu | Control chính                                                      | Implementation                             | Test/Evidence yêu cầu                                | Trạng thái                                                |
| ----- | ----------------------- | ------ | --------------------------------- | -------------- | ------------------------------------------------------------------ | ------------------------------------------ | ---------------------------------------------------- | --------------------------------------------------------- |
| TH-01 | Role Context            | S      | Chọn/giả mạo role                 | Cao            | Tách simulation khỏi authentication; validate role; production IdP | `src/auth/role_manager.py`                 | Invalid role → DENY                                  | Một phần; chưa có authentication production               |
| TH-02 | Authorization/Documents | E      | Privilege escalation              | Rất cao        | PermissionChecker fail-closed                                      | `src/auth/permission_checker.py`           | `test_permission_checker.py`: SV→I/R DENY; GV→R DENY | Đã có control + unit test                                 |
| TH-03 | Metadata ACL            | T/E    | Sửa/xóa/thiếu `allowed_roles`     | Rất cao        | Metadata validation + fail-closed                                  | PermissionChecker + dataset validator      | Missing/invalid ACL → DENY                           | Một phần; cần lưu validation evidence                     |
| TH-04 | User Prompt             | T      | Prompt injection                  | Cao            | Input Guard; authorization độc lập LLM                             | `src/security/input_guard.py` dự kiến      | Attack/bypass queries                                | Chưa triển khai đầy đủ                                    |
| TH-05 | Retrieved Document      | T      | Malicious instruction             | Cao            | Retrieved text = untrusted; policy separation                      | Retrieval/prompt assembly dự kiến          | Injection-in-document                                | Chưa triển khai đầy đủ                                    |
| TH-06 | Retrieval/Vector Store  | I/E    | Unauthorized document vào context | Rất cao        | Pre-retrieval auth + filter + defense-in-depth                     | `filter_authorized_metadata()` + retriever | Unauthorized doc không vào context; canary/leakage   | Permission control có; chưa tích hợp hoàn chỉnh retriever |
| TH-07 | Output                  | I      | Sensitive leakage                 | Rất cao        | Output Filter + refusal                                            | `src/security/output_filter.py` dự kiến    | Leakage rate + correct-refusal                       | Chưa triển khai                                           |
| TH-08 | Restricted/Output       | I      | Canary leakage                    | Rất cao        | Canary detector; registry không index                              | `tests/canary_registry.json` dự kiến       | Canary test                                          | Chưa triển khai                                           |
| TH-09 | Tools                   | E      | Tool permission quá rộng          | Cao            | Least privilege + allowlist + human approval                       | Khi tích hợp tool                          | Unauthorized-action test                             | Planned nếu có action tool                                |
| TH-10 | Logs                    | I      | Sensitive/excessive log retention | Cao            | Minimization + sanitization + retention                            | Security logger dự kiến                    | Log inspection                                       | Chưa triển khai đầy đủ                                    |
| TH-11 | Audit/Evidence          | T/R    | Sửa/xóa log/evidence              | Trung bình/Cao | Access control + integrity review                                  | `tests/results/` + audit process           | Audit review                                         | Chưa triển khai đầy đủ                                    |
| TH-12 | Availability/Admin      | D/E    | DoS/admin abuse                   | Cao            | Rate limit + monitoring + least privilege                          | Deployment/operations dự kiến              | Load/admin-misuse                                    | Planned                                                   |

## 4. Traceability trọng tâm

### TH-02 — Privilege Escalation

**Threat:** SV cố truy cập Internal/Restricted; GV cố truy cập Restricted.  
**Control:** `AccessAllowed = user_role ∈ document.allowed_roles`.  
**Implementation:** `src/auth/permission_checker.py`.  
**Test:** `tests/test_permission_checker.py`.

Expected:

- SinhVien → Public ALLOW; Internal/Restricted DENY.
- GiangVien → Public/Internal ALLOW; Restricted DENY.
- QuanTri → cả ba ALLOW.

### TH-03 — Metadata ACL Tampering

`allowed_roles` thiếu/hỏng → fail-closed → DENY. Không suy đoán quyền.

### TH-06 — Unauthorized Retrieval

Chuỗi bắt buộc:

`Role → PermissionChecker → Authorized Document Set → Retrieval → defense-in-depth → LLM`

Hiện đã có PermissionChecker; bước tiếp theo là tích hợp filter với retriever/vector store. Evidence cuối phải chứng minh unauthorized document không vào context và không rò rỉ canary.

### TH-07 / TH-08 — Output Leakage

Output Filter/Canary Detector phải được kiểm chứng bằng leakage rate, correct-refusal và canary test. Khi chưa có code/evidence, trạng thái giữ `Chưa triển khai`.

## 5. Liên kết bộ kiểm thử

```text
tests/
├── test_permission_checker.py
├── test_retrieval_access.py
├── test_output_filter.py
├── queries/
│   ├── normal_queries.json
│   └── attack_queries.json
└── results/
    ├── permission_results.json
    ├── retrieval_results.json
    ├── leakage_results.csv
    └── evaluation_summary.csv
```

## 6. Quy tắc cập nhật

1. ID giữ ổn định nếu vẫn là cùng threat.
2. Sửa `threat_model.md` thì cập nhật file này và ngược lại.
3. Code đổi vị trí thì cập nhật Implementation.
4. Chỉ ghi PASS khi test đã thực sự chạy.
5. Evidence tái lập lưu trong `tests/results/`.

## 7. Kết luận

`threat_model.md` giải thích **threat tồn tại vì sao, tác động gì và control nào cần có**; `threat_register.md` cho biết **control nằm ở đâu, test bằng gì, evidence nào cần có và trạng thái triển khai hiện tại**.
