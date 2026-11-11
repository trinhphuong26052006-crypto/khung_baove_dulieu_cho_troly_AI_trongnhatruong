"""src/retrieval/permission_checker.py

Kiểm tra quyền truy cập tài liệu cho prototype trợ lý AI/RAG nhà trường.

Nguyên tắc:
    AccessAllowed(user_role, document)
        = user_role in document["allowed_roles"]

Lưu ý:
- Đây là AUTHORIZATION (phân quyền), không phải xác thực danh tính.
- Quyền phải được kiểm tra trước khi tài liệu trái quyền trở thành
  ứng viên/context cho mô hình.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple


VALID_ROLES = {"SinhVien", "GiangVien", "QuanTri"}


@dataclass(frozen=True)
class PermissionDecision:
    doc_id: str
    role: str
    allowed: bool
    reason: str


class PermissionChecker:
    """
    Kiểm tra và lọc quyền truy cập tài liệu theo vai trò (RBAC).
    Tương thích cả giao diện Document-level authorization và Metadata-based retrieval.
    """

    DEFAULT_METADATA_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "metadata", "documents_metadata.json"
    )

    def __init__(
        self,
        metadata_path: Optional[str] = None,
        valid_roles: Optional[Iterable[str]] = None
    ):
        self.metadata_path = metadata_path or self.DEFAULT_METADATA_PATH
        self.valid_roles = set(valid_roles or VALID_ROLES)
        self._metadata: List[Dict[str, Any]] = []
        self._metadata_by_id: Dict[str, Dict[str, Any]] = {}
        self.load_metadata()

    def load_metadata(self) -> None:
        """Tải dữ liệu metadata từ tệp JSON nếu tồn tại."""
        if os.path.exists(self.metadata_path):
            try:
                with open(self.metadata_path, "r", encoding="utf-8") as f:
                    self._metadata = json.load(f)
                self._metadata_by_id = {doc["doc_id"]: doc for doc in self._metadata if "doc_id" in doc}
            except Exception:
                self._metadata = []
                self._metadata_by_id = {}
        else:
            self._metadata = []
            self._metadata_by_id = {}

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
        """
        return self.filter_authorized_metadata(user_role, results)

    # --------------------------------------------------------------------------
    # CÁC PHƯƠNG THỨC TIỆN ÍCH CHO RETRIEVER & MAIN PIPELINE
    # --------------------------------------------------------------------------

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Lấy toàn bộ danh sách metadata tài liệu được nạp."""
        return self._metadata.copy()

    def get_allowed_documents(self, user_role: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các bản ghi tài liệu mà vai trò `user_role` được phép truy cập.
        """
        if not user_role or not self._metadata:
            return []
        authorized, _ = self.filter_authorized_metadata(user_role, self._metadata)
        return authorized

    def get_allowed_doc_ids(self, user_role: str) -> Set[str]:
        """
        Lấy tập hợp các doc_id mà `user_role` được phép truy cập.
        """
        allowed_docs = self.get_allowed_documents(user_role)
        return {doc["doc_id"] for doc in allowed_docs if "doc_id" in doc}

    def get_allowed_classifications(self, user_role: str) -> List[str]:
        """
        Xác định danh sách các mức phân loại (Public, Internal, Restricted) mà vai trò được phép truy cập.
        SinhVien: ['Public']
        GiangVien: ['Public', 'Internal']
        QuanTri: ['Public', 'Internal', 'Restricted']
        """
        role = str(user_role).strip()
        if role == "SinhVien":
            return ["Public"]
        elif role == "GiangVien":
            return ["Public", "Internal"]
        elif role == "QuanTri":
            return ["Public", "Internal", "Restricted"]
        return []

    def is_access_allowed(self, doc_id: str, user_role: str) -> bool:
        """
        Kiểm tra một doc_id cụ thể có được phép truy cập bởi user_role hay không.
        """
        if not doc_id or not user_role:
            return False
        doc = self._metadata_by_id.get(doc_id)
        if not doc:
            return False
        decision = self.check_document(user_role, doc)
        return decision.allowed

    def filter_documents_by_role(self, documents: List[Dict[str, Any]], user_role: str) -> List[Dict[str, Any]]:
        """
        Hậu kiểm / Lọc một danh sách tài liệu retrieved để đảm bảo 100% không lọt tài liệu cấm.
        """
        authorized, _ = self.filter_retrieved_results(user_role, documents)
        return authorized


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
