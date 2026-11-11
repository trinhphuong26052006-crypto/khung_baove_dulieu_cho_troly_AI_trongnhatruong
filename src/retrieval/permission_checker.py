"""src/auth/permission_checker.py

Kiểm tra quyền truy cập tài liệu cho prototype trợ lý AI/RAG nhà trường.

Nguyên tắc:
    AccessAllowed(user_role, document)
        = user_role in document["allowed_roles"]

Lưu ý:
- Đây là AUTHORIZATION (phân quyền), không phải xác thực danh tính.
- Quyền phải được kiểm tra trước khi tài liệu trái quyền trở thành
  ứng viên/context cho mô hình.
"""

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple


VALID_ROLES = {"SinhVien", "GiangVien", "QuanTri"}


@dataclass(frozen=True)
class PermissionDecision:
    doc_id: str
    role: str
    allowed: bool
    reason: str


class PermissionChecker:
    def __init__(self, valid_roles: Optional[Iterable[str]] = None):
        self.valid_roles = set(valid_roles or VALID_ROLES)

    @staticmethod
    def _normalize_allowed_roles(value: Any) -> List[str]:
        """Hỗ trợ JSON array và CSV chuẩn dùng dấu |."""
        if isinstance(value, list):
            return [str(x).strip() for x in value if str(x).strip()]

        if isinstance(value, str):
            return [x.strip() for x in value.split("|") if x.strip()]

        return []

    def check_document(
        self,
        user_role: str,
        document_metadata: Dict[str, Any],
    ) -> PermissionDecision:
        role = str(user_role).strip()
        doc_id = str(document_metadata.get("doc_id", "UNKNOWN"))

        # Fail closed nếu role không hợp lệ.
        if role not in self.valid_roles:
            return PermissionDecision(
                doc_id=doc_id,
                role=role,
                allowed=False,
                reason="invalid_role",
            )

        allowed_roles = self._normalize_allowed_roles(
            document_metadata.get("allowed_roles", [])
        )

        # Fail closed nếu metadata quyền bị thiếu/hỏng.
        if not allowed_roles:
            return PermissionDecision(
                doc_id=doc_id,
                role=role,
                allowed=False,
                reason="missing_or_invalid_allowed_roles",
            )

        if role in allowed_roles:
            return PermissionDecision(
                doc_id=doc_id,
                role=role,
                allowed=True,
                reason="role_in_allowed_roles",
            )

        return PermissionDecision(
            doc_id=doc_id,
            role=role,
            allowed=False,
            reason="role_not_in_allowed_roles",
        )

    def filter_authorized_metadata(
        self,
        user_role: str,
        documents: Iterable[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[PermissionDecision]]:
        """
        Lọc metadata theo role TRƯỚC retrieval.

        Trả về:
        - authorized: tài liệu được phép trở thành tập ứng viên.
        - denied: quyết định từ chối để ghi security log.
        """
        authorized: List[Dict[str, Any]] = []
        denied: List[PermissionDecision] = []

        for document in documents:
            decision = self.check_document(user_role, document)
            if decision.allowed:
                authorized.append(document)
            else:
                denied.append(decision)

        return authorized, denied

    def filter_retrieved_results(
        self,
        user_role: str,
        results: Iterable[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[PermissionDecision]]:
        """
        Defense-in-depth sau retrieval.

        Không thay thế pre-retrieval authorization; đây chỉ là cổng kiểm tra
        thứ hai nếu vector store/integration trả về tài liệu ngoài dự kiến.
        """
        return self.filter_authorized_metadata(user_role, results)


if __name__ == "__main__":
    checker = PermissionChecker()

    demo_documents = [
        {
            "doc_id": "DOC-P001",
            "classification": "Public",
            "allowed_roles": ["SinhVien", "GiangVien", "QuanTri"],
        },
        {
            "doc_id": "DOC-I001",
            "classification": "Internal",
            "allowed_roles": ["GiangVien", "QuanTri"],
        },
        {
            "doc_id": "DOC-R001",
            "classification": "Restricted",
            "allowed_roles": ["QuanTri"],
        },
    ]

    for role in ["SinhVien", "GiangVien", "QuanTri"]:
        allowed, denied = checker.filter_authorized_metadata(role, demo_documents)
        print(
            f"{role}: "
            f"ALLOW={[d['doc_id'] for d in allowed]} | "
            f"DENY={[d.doc_id for d in denied]}"
        )
