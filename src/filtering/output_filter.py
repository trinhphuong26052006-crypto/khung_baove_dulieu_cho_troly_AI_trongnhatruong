"""
================================================================================
HỆ THỐNG TRỢ LÝ AI NHÀ TRƯỜNG - KHUNG BẢO VỆ DỮ LIỆU TOÀN DIỆN
================================================================================
Module: src/filtering/output_filter.py
Mục đích:
    Lớp hậu kiểm và lọc an toàn câu trả lời do AI tạo ra (Output Guardrails)
    trước khi gửi đến người dùng cuối.

Vai trò kiến trúc:
    - Đóng vai trò là chốt chặn bảo mật cuối cùng (Defense-in-Depth).
    - Ngăn chặn triệt để tình trạng AI suy diễn (hallucination) hoặc vô tình làm
      lộ thông tin ngoài phạm vi phân quyền của người dùng (RBAC).
    - ĐÁNH GIÁ TÍNH AN TOÀN VÀ CĂN CỨ CỦA CÂU TRẢ LỜI (Groundedness & Source Verification):
      Chặn đứng việc AI tự bịa đặt thông tin, bịa tên trường hoặc bịa nguồn tham khảo.
    - Phát hiện và che giấu thông tin định danh cá nhân (PII) và các hồ sơ
      học vụ nhạy cảm / kỷ luật giả định.
    - Ngăn chặn phản hồi chứa nội dung nguy hiểm, tấn công Prompt Injection ngược.
    - Cơ chế phòng thủ nghiêm ngặt (Fail-Closed): Nếu bộ lọc gặp lỗi hoặc từ chối,
      nội dung không an toàn sẽ bị chặn ngay lập tức.

Quy tắc phân quyền áp dụng (RBAC):
    - SinhVien: Chỉ được xem Public. CẤM mã tài liệu Internal (DOC-Ixxx) và Restricted (DOC-Rxxx),
      các mã hồ sơ kỷ luật cá nhân (SV-Gxxx, BB-Gxxx...).
    - GiangVien: Chỉ được xem Public và Internal. CẤM mã tài liệu Restricted (DOC-Rxxx) và hồ sơ cá nhân.
    - QuanTri: Được phép tiếp cận cả 3 mức (Public, Internal, Restricted).
================================================================================
"""

import re
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set, Tuple

# Cấu hình UTF-8 cho console Windows tránh UnicodeEncodeError
if sys.platform == "win32":
    try:
        if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr and sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


@dataclass
class ViolationDetail:
    """Chi tiết một vi phạm bảo mật hoặc lỗi thiếu căn cứ được phát hiện trong câu trả lời."""
    violation_type: str        # Loại vi phạm (RBAC_LEAKAGE, PII_LEAKAGE, SENSITIVE_CASE, MALICIOUS, UNGROUNDED_CLAIM, ENTITY_HALLUCINATION)
    severity: str              # Mức độ nghiêm trọng: CRITICAL, HIGH, MEDIUM, LOW
    matched_text: str          # Chuỗi ký tự vi phạm hoặc từ khóa bịa đặt
    description: str           # Mô tả chi tiết lý do vi phạm


@dataclass
class FilterResult:
    """Kết quả thẩm định của bộ lọc hậu kiểm."""
    is_safe: bool              # True nếu câu trả lời đạt tiêu chuẩn an toàn
    action_taken: str          # Hành động: PASSED, REDACTED, BLOCKED
    original_text: str         # Nội dung nguyên bản từ AI
    filtered_text: str         # Nội dung an toàn sau khi lọc/che/thay thế
    violations: List[ViolationDetail] = field(default_factory=list)
    source_grounded: bool = False  # True nếu câu trả lời có tài liệu nguồn hỗ trợ và được đối soát thành công

    @property
    def has_violations(self) -> bool:
        """Kiểm tra có bất kỳ vi phạm nào hay không."""
        return len(self.violations) > 0


class OutputFilter:
    """
    Bộ lọc hậu kiểm an toàn đầu ra và kiểm định căn cứ nguồn (Groundedness Guardrails).
    """

    # Biểu thức chính quy phát hiện mã tài liệu theo từng cấp độ
    DOC_PUBLIC_PATTERN = re.compile(r"\bDOC-P\d{3}\b", re.IGNORECASE)
    DOC_INTERNAL_PATTERN = re.compile(r"\bDOC-I\d{3}\b", re.IGNORECASE)
    DOC_RESTRICTED_PATTERN = re.compile(r"\bDOC-R\d{3}\b", re.IGNORECASE)
    DOC_ANY_PATTERN = re.compile(r"\bDOC-[PIR]\d{3}\b", re.IGNORECASE)

    # Biểu thức chính quy cho các thực thể hồ sơ cá nhân / kỷ luật giả lập
    SENSITIVE_ENTITY_PATTERNS = [
        (re.compile(r"\bSV-G\d{3}\b", re.IGNORECASE), "Mã hồ sơ sinh viên kỷ luật/nhạy cảm"),
        (re.compile(r"\bGV-G\d{3}\b", re.IGNORECASE), "Mã hồ sơ giảng viên liên quan khiếu nại"),
        (re.compile(r"\bBB-G\d{3}\b", re.IGNORECASE), "Mã biên bản vi phạm kỷ luật"),
        (re.compile(r"\bCX-KL\d{3}\b", re.IGNORECASE), "Mã hồ sơ cứu xét hủy kỷ luật"),
        (re.compile(r"\bHS-G\d{3}\b", re.IGNORECASE), "Mã hồ sơ quản lý kỷ luật nội bộ"),
    ]

    # Nhận diện Canary Token (TH-08: Tín hiệu phát hiện rò rỉ dữ liệu mật giả lập)
    CANARY_PATTERNS = [
        (re.compile(r"canary[\s_-]?token", re.IGNORECASE), "Cụm từ canary token"),
        (re.compile(r"chỉ\s+số\s+mô\s+phỏng\s+[AB](?:\s*:\s*\d+)?", re.IGNORECASE), "Chỉ số mô phỏng canary mật (Chỉ số mô phỏng A/B)"),
        (re.compile(r"CANARY-[A-Z0-9_-]+", re.IGNORECASE), "Mã token canary định dạng chuẩn"),
    ]

    # Biểu thức chính quy nhận diện PII (Personally Identifiable Information)
    CCCD_PATTERN = re.compile(r"(?:CCCD|CMND|Số định danh|Căn cước)?\s*[:#]?\s*(\b\d{9}\b|\b\d{12}\b)", re.IGNORECASE)
    PHONE_PATTERN = re.compile(r"\b(?:\+84|0)(?:3[2-9]|5[6|8|9]|7[0|6-9]|8[1-5]|9[0-9])[0-9]{7}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

    # Các từ khóa/mẫu câu nghi vấn injection ngược hoặc vượt quyền
    MALICIOUS_KEYWORDS = [
        "ignore previous instructions", "system prompt", "developer mode",
        "quy tắc hệ thống đã bị vô hiệu", "bypass security", "vượt qua bảo mật"
    ]

    # Mẫu nhận diện tên trường/cơ sở giáo dục (để kiểm tra xem AI có bịa trường ngoài bối cảnh không)
    INSTITUTION_PATTERN = re.compile(
        r"(?:Trường\s+)?(?:Đại\s+học|ĐHQG|Học\s+viện)\s+[A-ZÀ-Ỹ][\w\s–-]+?(?=\s+(?:trước|vào|tại|để|ở|theo|khi|trong|đã|sẽ|phải|cần|\.|\,|\;|\:|\n|\(|$))", 
        re.IGNORECASE
    )

    # Thông điệp từ chối an toàn chuẩn mực theo từng vai trò
    SAFE_REFUSAL_MESSAGES = {
        "SinhVien": (
            "[THÔNG BÁO BẢO MẬT HỌC VỤ]\n"
            "Câu trả lời đã bị hệ thống bảo vệ dữ liệu chặn lại vì có dấu hiệu chứa "
            "thông tin thuộc danh mục Tài liệu Nội bộ hoặc Mật ngoài phạm vi quyền hạn của Sinh viên.\n"
            "Nếu bạn cần giải đáp về các quy chế hoặc thông tin đào tạo công khai, vui lòng đặt lại câu hỏi."
        ),
        "GiangVien": (
            "[THÔNG BÁO BẢO MẬT HỌC VỤ]\n"
            "Câu trả lời đã bị hệ thống bảo vệ dữ liệu chặn lại vì phát hiện thông tin "
            "thuộc danh mục Hồ sơ Mật (Restricted) chỉ dành riêng cho Ban Giám hiệu và Cấp Quản trị.\n"
            "Vui lòng liên hệ đơn vị chức năng có thẩm quyền nếu thầy/cô cần tiếp cận hồ sơ đặc biệt này."
        ),
        "Default": (
            "[THÔNG BÁO BẢO MẬT HỌC VỤ]\n"
            "Nội dung phản hồi không đáp ứng tiêu chuẩn an toàn thông tin của nhà trường "
            "hoặc không có căn cứ từ tài liệu được cấp phép, đã được tự động chặn bởi hệ thống Output Guardrails."
        )
    }

    def __init__(self, strict_mode: bool = True):
        """
        Khởi tạo bộ lọc hậu kiểm OutputFilter.
        :param strict_mode: Nếu True, tự động chặn hoàn toàn (BLOCK) khi phát hiện vi phạm nghiêm trọng.
        """
        self.strict_mode = strict_mode

    # --------------------------------------------------------------------------
    # 1. CÁC HÀM KIỂM TRA QUY TẮC BẢO MẬT (DETECTION RULES)
    # --------------------------------------------------------------------------

    def check_rbac_leakage(
        self, 
        text: str, 
        user_role: str, 
        allowed_doc_ids: Optional[Set[str]] = None
    ) -> List[ViolationDetail]:
        """
        [Quy tắc 1] Kiểm tra rò rỉ mã tài liệu nằm ngoài thẩm quyền của vai trò.
        """
        violations: List[ViolationDetail] = []
        user_role_norm = (user_role or "").strip().lower()

        found_docs = set(self.DOC_ANY_PATTERN.findall(text))

        for doc_id in found_docs:
            doc_id_upper = doc_id.upper()

            # Đối chiếu với allowed_doc_ids nếu được cung cấp
            if allowed_doc_ids is not None:
                if doc_id_upper not in allowed_doc_ids:
                    severity = "CRITICAL" if doc_id_upper.startswith("DOC-R") else "HIGH"
                    violations.append(ViolationDetail(
                        violation_type="UNAUTHORIZED_DOC_LEAKAGE",
                        severity=severity,
                        matched_text=doc_id,
                        description=f"Mã tài liệu {doc_id} không nằm trong danh mục được phép của vai trò {user_role}."
                    ))
                    continue

            # Kiểm tra theo chuẩn vai trò
            if user_role_norm == "sinhvien":
                if doc_id_upper.startswith("DOC-R"):
                    violations.append(ViolationDetail(
                        violation_type="RESTRICTED_DOC_LEAKAGE",
                        severity="CRITICAL",
                        matched_text=doc_id,
                        description=f"Phát hiện mã tài liệu Mật (Restricted) '{doc_id}' cấm đối với SinhVien."
                    ))
                elif doc_id_upper.startswith("DOC-I"):
                    violations.append(ViolationDetail(
                        violation_type="INTERNAL_DOC_LEAKAGE",
                        severity="HIGH",
                        matched_text=doc_id,
                        description=f"Phát hiện mã tài liệu Nội bộ (Internal) '{doc_id}' cấm đối với SinhVien."
                    ))

            elif user_role_norm == "giangvien":
                if doc_id_upper.startswith("DOC-R"):
                    violations.append(ViolationDetail(
                        violation_type="RESTRICTED_DOC_LEAKAGE",
                        severity="CRITICAL",
                        matched_text=doc_id,
                        description=f"Phát hiện mã tài liệu Mật (Restricted) '{doc_id}' cấm đối với GiangVien."
                    ))

        return violations

    def check_sensitive_entities(self, text: str, user_role: str) -> List[ViolationDetail]:
        """
        [Quy tắc 2] Kiểm tra rò rỉ các mã hồ sơ cá nhân/kỷ luật giả lập (SV-Gxxx, BB-Gxxx...).
        """
        violations: List[ViolationDetail] = []
        user_role_norm = (user_role or "").strip().lower()

        if user_role_norm in ["sinhvien", "giangvien"]:
            for pattern, desc in self.SENSITIVE_ENTITY_PATTERNS:
                matches = pattern.findall(text)
                for match in matches:
                    violations.append(ViolationDetail(
                        violation_type="SENSITIVE_CASE_LEAKAGE",
                        severity="HIGH",
                        matched_text=match,
                        description=f"Phát hiện {desc} '{match}' ngoài phạm vi cho phép của vai trò {user_role}."
                    ))

        return violations

    def check_canary_tokens(self, text: str, user_role: str) -> List[ViolationDetail]:
        """
        [Quy tắc 2b - TH-08] Kiểm tra rò rỉ tín hiệu Canary Token (dữ liệu mật nhúng để phát hiện leakage).
        Chỉ vai trò QuanTri mới được phép tiếp cận.
        """
        violations: List[ViolationDetail] = []
        user_role_norm = (user_role or "").strip().lower()

        if user_role_norm != "quantri":
            for pattern, desc in self.CANARY_PATTERNS:
                matches = pattern.findall(text)
                for match in matches:
                    violations.append(ViolationDetail(
                        violation_type="CANARY_LEAKAGE",
                        severity="CRITICAL",
                        matched_text=match,
                        description=f"Phát hiện tín hiệu {desc} '{match}' trái quyền truy cập của vai trò {user_role} (TH-08)."
                    ))

        return violations

    def check_pii(self, text: str) -> List[ViolationDetail]:
        """
        [Quy tắc 3] Kiểm tra thông tin định danh cá nhân (CCCD, SĐT, Email cá nhân).
        """
        violations: List[ViolationDetail] = []

        for match in self.CCCD_PATTERN.finditer(text):
            val = match.group(1)
            if val and len(val) in [9, 12]:
                violations.append(ViolationDetail(
                    violation_type="PII_IDENTIFIER_LEAKAGE",
                    severity="HIGH",
                    matched_text=val,
                    description=f"Phát hiện số định danh cá nhân (CCCD/CMND): {val[:3]}***{val[-3:]}."
                ))

        for match in self.PHONE_PATTERN.finditer(text):
            val = match.group(0)
            violations.append(ViolationDetail(
                violation_type="PII_PHONE_LEAKAGE",
                severity="MEDIUM",
                matched_text=val,
                description=f"Phát hiện số điện thoại cá nhân: {val[:3]}****{val[-3:]}."
            ))

        for match in self.EMAIL_PATTERN.finditer(text):
            val = match.group(0)
            val_lower = val.lower()
            if val_lower.endswith(".edu.vn") or val_lower.endswith(".edu") or "university" in val_lower:
                continue
            violations.append(ViolationDetail(
                violation_type="PII_EMAIL_LEAKAGE",
                severity="MEDIUM",
                matched_text=val,
                description=f"Phát hiện email cá nhân ngoài hệ thống trường: {val}."
            ))

        return violations

    def check_malicious_content(self, text: str) -> List[ViolationDetail]:
        """
        [Quy tắc 4] Kiểm tra các mẫu injection ngược hoặc dấu hiệu bẻ khóa bối cảnh.
        """
        violations: List[ViolationDetail] = []
        text_lower = text.lower()

        for kw in self.MALICIOUS_KEYWORDS:
            if kw in text_lower:
                violations.append(ViolationDetail(
                    violation_type="MALICIOUS_INJECTION_REFLECTION",
                    severity="HIGH",
                    matched_text=kw,
                    description=f"Phát hiện từ khóa nguy cơ vi phạm an toàn thông tin: '{kw}'."
                ))

        return violations

    def check_groundedness(
        self, 
        text: str, 
        retrieved_docs: Optional[List[Dict[str, Any]]]
    ) -> List[ViolationDetail]:
        """
        [Quy tắc 5] KIỂM TRA TÍNH CĂN CỨ VÀ NGUỒN CỦA CÂU TRẢ LỜI (GROUNDEDNESS CHECK).
        - Nếu retrieved_docs is None: Bỏ qua kiểm tra căn cứ nguồn (cho các cuộc gọi đơn giản).
        - Nếu retrieved_docs == []: Kiểm tra xem AI có tự bịa đặt thông tin khi không có tài liệu nguồn.
        - Nếu retrieved_docs có dữ liệu: Kiểm tra xem AI có tự bịa đặt tên trường/tổ chức không có trong nguồn.
        """
        if retrieved_docs is None:
            return []

        violations: List[ViolationDetail] = []
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return violations

        # Trường hợp 1: Không có tài liệu nào được trích xuất hợp lệ (retrieved_docs == [])
        if len(retrieved_docs) == 0:
            # Nếu phản hồi là thông điệp từ chối/thông báo hệ thống chuẩn -> An toàn
            refusal_indicators = [
                "không tìm thấy", "không có tài liệu", "từ chối", "ngoài phạm vi", 
                "thông báo hệ thống", "thông báo từ hệ thống", "thông báo bảo mật", 
                "chặn lại", "vui lòng liên hệ", "không được phép", "không thuộc phạm vi",
                "quy chế bảo vệ dữ liệu", "không được công khai", "portal", "phòng đào tạo"
            ]
            is_refusal = any(ind in cleaned_text.lower() for ind in refusal_indicators)
            if not is_refusal:
                # AI đang cố tình bịa thông tin thực tế khi không có tài liệu hỗ trợ!
                violations.append(ViolationDetail(
                    violation_type="UNGROUNDED_CLAIM",
                    severity="CRITICAL",
                    matched_text="UNGROUNDED_FACT_ASSERTION",
                    description="Câu trả lời đưa ra thông tin khẳng định nhưng không có bất kỳ tài liệu nguồn nào hỗ trợ (Hallucination without context)."
                ))
            return violations

        # Trường hợp 2: Có tài liệu tham khảo -> Kiểm tra việc bịa đặt thực thể (Entity Hallucination)
        # Ghép toàn bộ nội dung tài liệu tham khảo để đối soát
        combined_doc_text = " ".join([
            (d.get("title", "") + " " + d.get("description", "") + " " + d.get("content", ""))
            for d in retrieved_docs
        ]).lower()

        # Kiểm tra các tên trường/tổ chức xuất hiện trong câu trả lời
        found_institutions = self.INSTITUTION_PATTERN.findall(cleaned_text)
        for inst in found_institutions:
            inst_clean = inst.strip()
            # Bỏ qua các từ chung chung ngắn
            if len(inst_clean) < 10:
                continue
            # Kiểm tra xem tên trường/đơn vị này có nằm trong tài liệu tham khảo không
            inst_lower = inst_clean.lower()
            if inst_lower not in combined_doc_text:
                violations.append(ViolationDetail(
                    violation_type="ENTITY_HALLUCINATION",
                    severity="HIGH",
                    matched_text=inst_clean,
                    description=f"AI đưa ra đơn vị/tên trường '{inst_clean}' không xuất hiện trong bất kỳ tài liệu tham khảo nào được cấp phép."
                ))

        return violations

    # --------------------------------------------------------------------------
    # 2. XỬ LÝ VI PHẠM (REDACTION & BLOCKING)
    # --------------------------------------------------------------------------

    def redact_sensitive_info(self, text: str, violations: List[ViolationDetail]) -> str:
        """
        Che các thông tin nhạy cảm (PII, mã vụ việc, đơn vị bịa đặt) bằng nhãn bảo vệ dữ liệu.
        """
        redacted = text
        sorted_violations = sorted(violations, key=lambda v: len(v.matched_text), reverse=True)

        for v in sorted_violations:
            if not v.matched_text:
                continue

            if "DOC-" in v.matched_text.upper():
                placeholder = "[MÃ TÀI LIỆU ĐÃ ĐƯỢC BẢO MẬT]"
            elif v.violation_type == "PII_IDENTIFIER_LEAKAGE":
                placeholder = "[SỐ ĐỊNH DANH ĐÃ ĐƯỢC ẨN]"
            elif v.violation_type == "PII_PHONE_LEAKAGE":
                placeholder = "[SĐT ĐÃ ĐƯỢC ẨN]"
            elif v.violation_type == "PII_EMAIL_LEAKAGE":
                placeholder = "[EMAIL ĐÃ ĐƯỢC ẨN]"
            elif v.violation_type == "SENSITIVE_CASE_LEAKAGE":
                placeholder = "[MÃ HỒ SƠ ĐÃ ĐƯỢC KHÓA]"
            elif v.violation_type == "ENTITY_HALLUCINATION":
                placeholder = "[THÔNG TIN KHÔNG CÓ CĂN CỨ ĐÃ ĐƯỢC LOẠI BỎ]"
            else:
                placeholder = "[THÔNG TIN ĐÃ ĐƯỢC CHE THEO QUY CHẾ]"

            pattern = re.escape(v.matched_text)
            redacted = re.sub(pattern, placeholder, redacted)

        return redacted

    # --------------------------------------------------------------------------
    # 3. QUY TRÌNH THẨM ĐỊNH TỔNG THỂ (MAIN FILTER PIPELINE - FAIL CLOSED)
    # --------------------------------------------------------------------------

    def filter_response(
        self,
        response_text: str,
        user_role: str,
        allowed_doc_ids: Optional[Set[str]] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None
    ) -> FilterResult:
        """
        Thực hiện toàn bộ chu trình hậu kiểm và lọc câu trả lời trước khi gửi người dùng:
        1. Kiểm tra rò rỉ mã tài liệu theo vai trò (RBAC).
        2. Kiểm tra rò rỉ mã hồ sơ nhạy cảm / kỷ luật.
        3. Kiểm tra rò rỉ PII.
        4. Kiểm tra injection reflection.
        5. Kiểm tra tính căn cứ từ nguồn và chống bịa đặt (Groundedness Check).
        6. Cơ chế Fail-Closed: Nếu có lỗi trong quá trình lọc, chặn an toàn ngay lập tức.
        """
        if not response_text:
            return FilterResult(
                is_safe=True,
                action_taken="PASSED",
                original_text="",
                filtered_text=""
            )

        try:
            all_violations: List[ViolationDetail] = []

            # 1. Kiểm tra rò rỉ phân quyền tài liệu RBAC
            all_violations.extend(self.check_rbac_leakage(response_text, user_role, allowed_doc_ids))

            # 2. Kiểm tra rò rỉ mã hồ sơ nhạy cảm
            all_violations.extend(self.check_sensitive_entities(response_text, user_role))

            # 2b. Kiểm tra rò rỉ tín hiệu Canary Token (TH-08)
            all_violations.extend(self.check_canary_tokens(response_text, user_role))

            # 3. Kiểm tra rò rỉ PII
            all_violations.extend(self.check_pii(response_text))

            # 4. Kiểm tra nội dung độc hại / injection reflection
            all_violations.extend(self.check_malicious_content(response_text))

            # 5. Kiểm tra tính căn cứ từ nguồn tài liệu (Groundedness Check)
            all_violations.extend(self.check_groundedness(response_text, retrieved_docs))

            # Xác định tính căn cứ nguồn (Groundedness status):
            # Chỉ được xem là có căn cứ nguồn (source_grounded=True) khi:
            # 1. Có tài liệu nguồn hỗ trợ (retrieved_docs có ít nhất 1 tài liệu).
            # 2. Không có vi phạm căn cứ nguồn (UNGROUNDED_CLAIM, ENTITY_HALLUCINATION).
            has_groundedness_violations = any(
                v.violation_type in ["UNGROUNDED_CLAIM", "ENTITY_HALLUCINATION"]
                for v in all_violations
            )
            has_supporting_docs = bool(retrieved_docs and len(retrieved_docs) > 0)
            is_source_grounded = has_supporting_docs and not has_groundedness_violations

            # Nếu không có vi phạm -> Đạt chuẩn an toàn (PASSED)
            if not all_violations:
                return FilterResult(
                    is_safe=True,
                    action_taken="PASSED",
                    original_text=response_text,
                    filtered_text=response_text,
                    violations=[],
                    source_grounded=is_source_grounded
                )

            # Phân loại mức độ vi phạm
            has_critical = any(v.severity == "CRITICAL" for v in all_violations)

            # Nếu có vi phạm CRITICAL hoặc ở chế độ strict_mode có vi phạm căn cứ nguồn -> CHẶN TOÀN BỘ (BLOCK)
            if self.strict_mode and has_critical:
                role_key = user_role if user_role in self.SAFE_REFUSAL_MESSAGES else "Default"
                refusal_text = self.SAFE_REFUSAL_MESSAGES[role_key]

                return FilterResult(
                    is_safe=False,
                    action_taken="BLOCKED",
                    original_text=response_text,
                    filtered_text=refusal_text,
                    violations=all_violations
                )

            # Nếu là vi phạm mức HIGH hoặc che được (PII, Hallucinated entity) -> REDACT
            redacted_text = self.redact_sensitive_info(response_text, all_violations)
            warning_note = "\n\n*(Lưu ý: Một số thông tin nhạy cảm hoặc không có căn cứ từ tài liệu đã được bộ lọc tự động che đi nhằm đảm bảo an toàn thông tin.)*"
            final_text = redacted_text + warning_note

            return FilterResult(
                is_safe=False,
                action_taken="REDACTED",
                original_text=response_text,
                filtered_text=final_text,
                violations=all_violations
            )

        except Exception as ex:
            # CƠ CHẾ PHÒNG THỦ FAIL-CLOSED: Bất kỳ lỗi bất thường nào cũng dẫn tới CHẶN an toàn
            safe_error_msg = (
                "[THÔNG BÁO BẢO MẬT HỌC VỤ]\n"
                "Đã phát sinh sự cố trong quá trình hậu kiểm câu trả lời của AI. "
                "Theo chính sách bảo vệ dữ liệu, hệ thống đã chặn hiển thị phản hồi này để đảm bảo an toàn."
            )
            return FilterResult(
                is_safe=False,
                action_taken="BLOCKED",
                original_text=response_text,
                filtered_text=safe_error_msg,
                violations=[ViolationDetail(
                    violation_type="OUTPUT_FILTER_EXCEPTION",
                    severity="CRITICAL",
                    matched_text="ERROR",
                    description=f"Lỗi kiểm định bộ lọc: {str(ex)}"
                )]
            )

    def is_safe(
        self, 
        response_text: str, 
        user_role: str, 
        allowed_doc_ids: Optional[Set[str]] = None,
        retrieved_docs: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Kiểm tra nhanh xem câu trả lời có đạt chuẩn an toàn và căn cứ hay không."""
        result = self.filter_response(response_text, user_role, allowed_doc_ids, retrieved_docs)
        return result.is_safe


# Singleton instance mặc định
default_output_filter = OutputFilter()


def filter_ai_response(
    response_text: str, 
    user_role: str, 
    allowed_doc_ids: Optional[Set[str]] = None,
    retrieved_docs: Optional[List[Dict[str, Any]]] = None,
    strict_mode: bool = True
) -> FilterResult:
    """Hàm giao diện nhanh để lọc câu trả lời của AI."""
    filter_instance = OutputFilter(strict_mode=strict_mode)
    return filter_instance.filter_response(
        response_text=response_text,
        user_role=user_role,
        allowed_doc_ids=allowed_doc_ids,
        retrieved_docs=retrieved_docs
    )
