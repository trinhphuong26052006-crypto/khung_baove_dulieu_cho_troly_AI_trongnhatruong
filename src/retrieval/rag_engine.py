"""
src/retrieval/rag_engine.py
===========================
Module trung tâm tích hợp Vector Store + Mô hình ngôn ngữ cục bộ (Ollama)
kèm cơ chế kiểm soát truy cập theo vai trò (Pre-retrieval Access Control RAG).

Kiến trúc luồng xử lý:
1. Nhận câu hỏi (Query) và vai trò người dùng (user_role) từ auth/role_manager.
2. PermissionChecker xác định danh sách doc_id được phép xem (pre-retrieval filter).
3. Vector Store (ChromaDB / FAISS) truy xuất top-k đoạn văn bản (chunks) liên quan
   nhưng BẮT BUỘC chỉ nằm trong tập tài liệu được phép.
4. Lắp ráp Context an toàn (không chứa dữ liệu cấm / ngoài quyền).
5. Gửi Prompt đến mô hình cục bộ Ollama (hoặc mock nếu Ollama daemon chưa bật)
   để sinh câu trả lời có kiểm soát.
"""

import os
import json
from typing import List, Dict, Any, Optional

from src.retrieval.permission_checker import PermissionChecker
from src.retrieval.retriever import DocumentRetriever


class RAGEngine:
    """
    RAG Engine an toàn cho trường học, tích hợp kiểm soát truy cập và Ollama.
    """

    def __init__(
        self,
        metadata_path: Optional[str] = None,
        base_dir: Optional[str] = None,
        ollama_model: str = "llama3.2",
        ollama_base_url: str = "http://localhost:11434",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        vector_db_type: str = "chroma"
    ):
        """
        Khởi tạo hệ thống RAG an toàn.
        :param metadata_path: Đường dẫn tệp metadata JSON
        :param base_dir: Thư mục gốc chứa tài liệu
        :param ollama_model: Tên mô hình chạy trên Ollama (llama3, mistral, gemma...)
        :param ollama_base_url: Địa chỉ endpoint của Ollama local
        :param embedding_model_name: Tên mô hình embeddings
        :param vector_db_type: 'chroma' hoặc 'faiss'
        """
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.checker = PermissionChecker(metadata_path)
        self.retriever = DocumentRetriever(metadata_path, self.base_dir)
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url
        self.embedding_model_name = embedding_model_name
        self.vector_db_type = vector_db_type

        # Cấu trúc Vector Store cache
        self.vector_store = None
        self.embeddings = None
        self._init_vector_store()

    def _init_vector_store(self) -> None:
        """
        Khởi tạo hoặc kết nối Vector Store khi các thư viện langchain/chromadb/faiss sẵn sàng.
        Hỗ trợ fallback an toàn nếu chưa cài đặt xong.
        """
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            self.embeddings = HuggingFaceEmbeddings(model_name=self.embedding_model_name)
            print(f"[RAGEngine] Đã tải mô hình embeddings: {self.embedding_model_name}")
        except Exception as e:
            # Fallback nếu thư viện đang tải hoặc chưa sẵn sàng
            self.embeddings = None

    def retrieve_context(self, query: str, user_role: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Truy xuất tài liệu an toàn: Bắt buộc áp dụng Pre-retrieval Access Control.
        Chỉ tìm kiếm trong các tài liệu mà `user_role` có quyền truy cập.
        """
        allowed_doc_ids = self.checker.get_allowed_doc_ids(user_role)
        if not allowed_doc_ids:
            return []

        # Truy xuất tài liệu phù hợp thông qua retriever có kiểm soát
        candidate_docs = self.retriever.search_documents(query=query, user_role=user_role, top_k=top_k)

        # Hậu kiểm bảo vệ 2 lớp (Defense-in-depth)
        verified_docs = []
        for doc in candidate_docs:
            if doc.get("doc_id") in allowed_doc_ids:
                verified_docs.append(doc)

        return verified_docs

    def build_prompt(self, query: str, user_role: str, retrieved_docs: List[Dict[str, Any]]) -> str:
        """
        Xây dựng Prompt hoàn chỉnh kết hợp bối cảnh an toàn.
        """
        if not retrieved_docs:
            context_str = "Không tìm thấy tài liệu phù hợp trong phạm vi quyền hạn được cấp."
        else:
            context_blocks = []
            for idx, doc in enumerate(retrieved_docs, start=1):
                block = (
                    f"--- TÀI LIỆU {idx}: {doc.get('title')} ({doc.get('doc_id')}) ---\n"
                    f"Mức phân loại: {doc.get('classification')}\n"
                    f"Nội dung:\n{doc.get('content', '')}\n"
                )
                context_blocks.append(block)
            context_str = "\n".join(context_blocks)

        prompt = f"""Bạn là Trợ lý Trí tuệ Nhân tạo hỗ trợ thông tin học vụ trong nhà trường.
Vai trò của người dùng hiện tại là: [{user_role}].

QUY TẮC BẢO VỆ DỮ LIỆU:
1. Chỉ trả lời dựa trên các thông tin được cung cấp trong phần [NGỮ CẢNH TÀI LIỆU] dưới đây.
2. Tuyệt đối không suy diễn hoặc tiết lộ thông tin nội bộ / bảo mật ngoài phạm vi quyền của vai trò [{user_role}].
3. Nếu ngữ cảnh không có thông tin hoặc người dùng không có quyền xem, hãy giải thích rõ ràng và từ chối cung cấp một cách lịch sự.

[NGỮ CẢNH TÀI LIỆU]:
{context_str}

[CÂU HỎI CỦA NGƯỜI DÙNG]:
{query}

[CÂU TRẢ LỜI CỦA TRỢ LÝ]:"""
        return prompt

    def query_ollama(self, prompt: str) -> str:
        """
        Gửi prompt tới mô hình Ollama cục bộ.
        """
        try:
            from langchain_ollama import OllamaLLM
            llm = OllamaLLM(model=self.ollama_model, base_url=self.ollama_base_url)
            return llm.invoke(prompt)
        except Exception:
            # Fallback trực tiếp bằng urllib nếu langchain-ollama chưa nạp hoặc dùng REST API của Ollama
            import urllib.request
            import urllib.error
            url = f"{self.ollama_base_url}/api/generate"
            payload = json.dumps({
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False
            }).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    return data.get("response", "")
            except Exception as ex:
                return (
                    f"[Thông báo từ RAG Engine]\n"
                    f"Đã xây dựng ngữ cảnh an toàn thành công theo quyền hạn.\n"
                    f"(Lưu ý: Không thể kết nối tới Ollama tại {self.ollama_base_url}. Vui lòng đảm bảo dịch vụ Ollama đang chạy: 'ollama serve')\n\n"
                    f"Prompt ngữ cảnh an toàn đã chuẩn bị:\n{prompt}"
                )

    def answer_query(self, query: str, user_role: str, top_k: int = 3) -> Dict[str, Any]:
        """
        Quy trình xử lý hoàn chỉnh một truy vấn từ người dùng.
        :param query: Câu hỏi của người dùng
        :param user_role: Vai trò người dùng (SinhVien, GiangVien, QuanTri)
        :param top_k: Số lượng tài liệu liên quan tối đa
        :return: Dict chứa câu trả lời, danh sách tài liệu tham chiếu và quyền truy cập
        """
        # 1. Truy xuất tài liệu có kiểm soát phân quyền
        retrieved_docs = self.retrieve_context(query, user_role, top_k)

        # 2. Xây dựng prompt bảo mật
        prompt = self.build_prompt(query, user_role, retrieved_docs)

        # 3. Gọi mô hình sinh câu trả lời
        response_text = self.query_ollama(prompt)

        return {
            "query": query,
            "user_role": user_role,
            "retrieved_documents": [
                {
                    "doc_id": d.get("doc_id"),
                    "title": d.get("title"),
                    "classification": d.get("classification"),
                    "department": d.get("department")
                }
                for d in retrieved_docs
            ],
            "total_retrieved": len(retrieved_docs),
            "answer": response_text
        }


if __name__ == "__main__":
    # Demo kiểm tra nhanh RAG Engine với các vai trò khác nhau
    engine = RAGEngine()

    print("=" * 70)
    print("DEMO RAG ENGINE - KIỂM SOÁT TRUY XUẤT THEO VAI TRÒ")
    print("=" * 70)

    test_queries = [
        ("Lịch thi học kỳ 2 xem ở đâu?", "SinhVien"),
        ("Kế hoạch tổ chức thi kết thúc học phần nội bộ", "SinhVien"),
        ("Kế hoạch tổ chức thi kết thúc học phần nội bộ", "GiangVien"),
        ("Hồ sơ kỷ luật học viên SV-G014", "SinhVien"),
        ("Hồ sơ kỷ luật học viên SV-G014", "QuanTri"),
    ]

    for q, role in test_queries:
        print(f"\n[Người dùng: {role}] Hỏi: '{q}'")
        res = engine.answer_query(q, role, top_k=2)
        print(f" -> Số tài liệu được cấp phép truy xuất: {res['total_retrieved']}")
        for d in res["retrieved_documents"]:
            print(f"    + [{d['classification']}] {d['doc_id']}: {d['title']}")
        if res['total_retrieved'] == 0:
            print("    [!] Không có quyền hoặc không tìm thấy tài liệu phù hợp.")

