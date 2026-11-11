"""
src/retrieval/retriever.py
==========================
Module truy xuất tài liệu kết hợp kiểm soát phân quyền (RBAC-aware Retriever).

Chức năng chính:
- Tải nội dung các tài liệu được cấp phép theo vai trò của người dùng.
- Tạo chỉ mục tìm kiếm ngữ nghĩa hoặc TF-IDF / Vector Store.
- Lọc triệt để các tài liệu ngoài phạm vi quyền hạn trước khi trả về cho RAG Engine.
"""

import os
from typing import List, Dict, Any, Optional
from src.retrieval.permission_checker import PermissionChecker


class DocumentRetriever:
    """
    Retriever thực hiện truy xuất tài liệu kèm cơ chế Pre-retrieval filtering theo vai trò.
    """

    def __init__(self, metadata_path: Optional[str] = None, base_dir: Optional[str] = None):
        self.checker = PermissionChecker(metadata_path)
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def get_document_content(self, file_path: str) -> str:
        """Đọc nội dung văn bản từ file_path."""
        abs_path = os.path.join(self.base_dir, file_path) if not os.path.isabs(file_path) else file_path
        if not os.path.exists(abs_path):
            return ""
        with open(abs_path, "r", encoding="utf-8") as f:
            return f.read()

    def get_authorized_documents(self, user_role: str) -> List[Dict[str, Any]]:
        """
        Lấy toàn bộ tài liệu cùng nội dung mà user_role được phép truy cập.
        """
        allowed_metas = self.checker.get_allowed_documents(user_role)
        authorized_docs = []
        for meta in allowed_metas:
            content = self.get_document_content(meta["file_path"])
            doc_item = dict(meta)
            doc_item["content"] = content
            authorized_docs.append(doc_item)
        return authorized_docs

    def search_documents(self, query: str, user_role: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Tìm kiếm tài liệu liên quan đến câu hỏi trong phạm vi quyền hạn của vai trò.
        """
        authorized_docs = self.get_authorized_documents(user_role)
        if not authorized_docs or not query:
            return []

        query_terms = [t.lower() for t in query.split() if len(t) > 1]
        scored_docs = []

        for doc in authorized_docs:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            desc_lower = doc.get("description", "").lower()

            # Tính điểm mức độ phù hợp (BM25 / Keyword matching cơ bản khi chưa có Vector Store)
            score = 0
            for term in query_terms:
                if term in title_lower:
                    score += 5
                if term in desc_lower:
                    score += 3
                if term in content_lower:
                    score += 1 + min(content_lower.count(term), 5)

            if score > 0:
                scored_docs.append((score, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for score, doc in scored_docs[:top_k]]

