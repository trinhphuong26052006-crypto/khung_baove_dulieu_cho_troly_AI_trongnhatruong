"""
src/retrieval/permission_checker.py
===================================
Module kiểm tra quyền truy cập tài liệu dựa trên vai trò (Pre-retrieval Access Control).

Chức năng chính:
- Tải metadata của các tài liệu từ documents_metadata.json.
- Xác định tài liệu nào người dùng có vai trò hiện tại được phép truy cập.
- Cung cấp bộ lọc doc_id hợp lệ (allowed_doc_ids) cho Retriever / Vector Store.
"""

import json
import os
from typing import List, Dict, Any, Optional, Set


class PermissionChecker:
    """
    Kiểm tra và lọc quyền truy cập tài liệu theo vai trò (RBAC).
    """

    DEFAULT_METADATA_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "metadata", "documents_metadata.json"
    )

    def __init__(self, metadata_path: Optional[str] = None):
        """
        Khởi tạo PermissionChecker với đường dẫn metadata.
        """
        self.metadata_path = metadata_path or self.DEFAULT_METADATA_PATH
        self._metadata: List[Dict[str, Any]] = []
        self._metadata_by_id: Dict[str, Dict[str, Any]] = {}
        self.load_metadata()

    def load_metadata(self) -> None:
        """Tải dữ liệu metadata từ tệp JSON."""
        if not os.path.exists(self.metadata_path):
            raise FileNotFoundError(f"Không tìm thấy file metadata tại: {self.metadata_path}")

        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self._metadata = json.load(f)

        self._metadata_by_id = {doc["doc_id"]: doc for doc in self._metadata}

    def get_allowed_documents(self, user_role: str) -> List[Dict[str, Any]]:
        """
        Lấy danh sách các bản ghi tài liệu mà vai trò `user_role` được phép truy cập.
        """
        if not user_role:
            return []

        allowed = []
        for doc in self._metadata:
            roles = doc.get("allowed_roles", [])
            if user_role in roles:
                allowed.append(doc)
        return allowed

    def get_allowed_doc_ids(self, user_role: str) -> Set[str]:
        """
        Lấy tập hợp các doc_id mà `user_role` được phép truy cập.
        Thường dùng để lọc (pre-filter) trong Vector Store.
        """
        allowed_docs = self.get_allowed_documents(user_role)
        return {doc["doc_id"] for doc in allowed_docs}

    def is_access_allowed(self, doc_id: str, user_role: str) -> bool:
        """
        Kiểm tra một doc_id cụ thể có được phép truy cập bởi user_role hay không.
        """
        if not doc_id or not user_role:
            return False

        doc = self._metadata_by_id.get(doc_id)
        if not doc:
            return False

        return user_role in doc.get("allowed_roles", [])

    def filter_documents_by_role(self, documents: List[Dict[str, Any]], user_role: str) -> List[Dict[str, Any]]:
        """
        Hậu kiểm / Lọc một danh sách tài liệu retrieved để đảm bảo 100% không lọt tài liệu cấm.
        """
        allowed_ids = self.get_allowed_doc_ids(user_role)
        filtered = []
        for d in documents:
            doc_id = d.get("doc_id") or d.get("metadata", {}).get("doc_id")
            if doc_id in allowed_ids:
                filtered.append(d)
        return filtered

