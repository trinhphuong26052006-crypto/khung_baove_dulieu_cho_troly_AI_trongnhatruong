"""
src/retrieval/retriever.py
==========================
Module truy xuất tài liệu kết hợp kiểm soát phân quyền (RBAC-aware Retriever).

Chức năng chính:
- Tải nội dung các tài liệu được cấp phép theo vai trò của người dùng.
- Tạo chỉ mục tìm kiếm ngữ nghĩa hoặc TF-IDF / Vector Store.
- Lọc triệt để các tài liệu ngoài phạm vi quyền hạn trước khi trả về cho RAG Engine.
- Tích hợp Relevance Gate để đảm bảo chỉ trả về các tài liệu thực sự liên quan đến câu hỏi,
  không đề xuất tài liệu lạc đề khi không tìm thấy kết quả.
"""

import os
import re
from typing import List, Dict, Any, Optional
from src.retrieval.permission_checker import PermissionChecker


# Danh sách các từ thể loại văn bản chung (không dùng để xác định chủ đề chuyên môn)
GENRE_WORDS = {
    "báo cáo", "kế hoạch", "hướng dẫn", "thông báo", "quy chế", 
    "quy định", "biên bản", "hồ sơ", "danh sách", "chính sách", "sổ tay"
}

# Hư từ, từ nối thông dụng trong tiếng Việt
STOPWORDS = {
    "về", "của", "cho", "và", "các", "những", "trong", "theo", "là", 
    "có", "được", "tại", "ở", "với", "báo", "cáo", "việc", "xin", 
    "hỏi", "tôi", "em", "thầy", "cô", "làm", "sao", "thế", "nào", "gì"
}

# Các chủ đề nghiệp vụ chuyên biệt cốt lõi
SPECIALIZED_DOMAINS = [
    "kiểm toán", "bảng điểm", "kết quả học tập", "học phí", "học bổng", "lịch thi", "kỷ luật", 
    "ký túc xá", "nội trú", "đồ án", "khóa luận", "bảo lưu", 
    "khiếu nại", "tốt nghiệp", "chuẩn đầu ra", "ngoại ngữ", "tin học",
    "miễn giảm", "vay vốn", "bảo hiểm y tế", "phòng máy", "thực tập",
    "quyền truy cập"
]


def is_document_relevant(query: str, doc: Dict[str, Any], user_role: Optional[str] = None) -> bool:
    """
    Đánh giá xem tài liệu trích xuất có thực sự liên quan và hỗ trợ câu hỏi hay không.
    Ngăn chặn Retriever trả về tài liệu sai chủ đề (False Positives) do trùng các từ đơn lẻ.
    """
    q_clean = query.lower()
    title_lower = doc.get("title", "").lower()
    desc_lower = doc.get("description", "").lower()
    content_lower = doc.get("content", "").lower()
    doc_text = f"{title_lower} {desc_lower} {content_lower}"

    # Kiểm tra ý định hỏi dữ liệu cá nhân của vai trò SinhVien (Personal Data Intent)
    if user_role == "SinhVien":
        personal_terms = ["của tôi", "của em", "cá nhân", "của mình"]
        if any(pt in q_clean for pt in personal_terms) and any(k in q_clean for k in ["bảng điểm", "điểm", "kết quả học tập"]):
            return False

    # 1. Rào chắn từ khóa chuyên biệt:
    # Nếu câu hỏi nhắm vào một chủ đề nghiệp vụ đặc thù (như 'bảng điểm', 'kiểm toán', 'học phí'...)
    # thì tài liệu BẮT BUỘC phải thực sự xoay quanh chủ đề đó (ở tiêu đề, mô tả hoặc xuất hiện nhiều lần).
    for kw in SPECIALIZED_DOMAINS:
        if kw in q_clean:
            has_kw = (kw in title_lower or kw in desc_lower or content_lower.count(kw) >= 3)
            if not has_kw:
                return False

    # 2. Tách các cụm 2 từ (bigrams) trong query
    words = [w for w in re.findall(r"\b\w+\b", q_clean) if len(w) > 1 and w not in STOPWORDS]
    if not words:
        return True

    bigrams = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
    subject_bigrams = [bg for bg in bigrams if bg not in GENRE_WORDS]

    # Nếu có cụm chủ đề 2 từ, yêu cầu khớp ít nhất 1 cụm trong tài liệu
    if subject_bigrams:
        return any(bg in doc_text for bg in subject_bigrams)

    # 3. Với câu hỏi ngắn, kiểm tra sự xuất hiện của ít nhất 1 từ đơn có ý nghĩa
    meaningful_singles = [w for w in words if w not in GENRE_WORDS and len(w) >= 3]
    if meaningful_singles:
        return any(re.search(r"\b" + re.escape(w) + r"\b", doc_text) for w in meaningful_singles)

    return True


class DocumentRetriever:
    """
    Retriever thực hiện truy xuất tài liệu kèm cơ chế Pre-retrieval filtering theo vai trò
    và Relevance Gate ngăn chặn trả về tài liệu không liên quan.
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
        Chỉ trả về các tài liệu thực sự phù hợp với câu hỏi (Relevance Filtered).
        """
        if not query or not query.strip():
            return []

        authorized_docs = self.get_authorized_documents(user_role)
        if not authorized_docs:
            return []

        # Lọc sơ bộ bằng Relevance Gate
        candidate_docs = [doc for doc in authorized_docs if is_document_relevant(query, doc, user_role)]
        if not candidate_docs:
            return []

        query_terms = [t.lower() for t in query.split() if len(t) > 1 and t.lower() not in STOPWORDS]
        if not query_terms:
            query_terms = [t.lower() for t in query.split() if len(t) > 1]

        scored_docs = []

        for doc in candidate_docs:
            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()
            desc_lower = doc.get("description", "").lower()

            # Tính điểm mức độ phù hợp (BM25 / Keyword matching cơ bản)
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
