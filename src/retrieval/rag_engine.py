"""RAG Engine: RBAC pre-retrieval, Ollama REST, safe errors and performance logs."""
import os
import sys
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.permission_checker import PermissionChecker
from src.retrieval.retriever import DocumentRetriever


class RAGEngine:
    def __init__(
        self,
        metadata_path: Optional[str] = None,
        base_dir: Optional[str] = None,
        ollama_model: str = "llama3.2",
        ollama_base_url: str = "http://localhost:11434",
        embedding_model_name: str = "all-MiniLM-L6-v2",
        vector_db_type: str = "chroma",
    ):
        self.base_dir = base_dir or str(PROJECT_ROOT)
        self.checker = PermissionChecker(metadata_path)
        self.retriever = DocumentRetriever(metadata_path, self.base_dir)
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.embedding_model_name = embedding_model_name
        self.vector_db_type = vector_db_type
        self.vector_store = None
        self.embeddings = None
        self._init_vector_store()

    def _init_vector_store(self) -> None:
        """Keep existing embedding initialization for compatibility."""
        try:
            from langchain_ollama import OllamaEmbeddings
            self.embeddings = OllamaEmbeddings(
                model=self.ollama_model,
                base_url=self.ollama_base_url,
            )
        except ImportError:
            self.embeddings = None

    def retrieve_context(
        self, query: str, user_role: str, top_k: int = 3
    ) -> List[Dict[str, Any]]:
        allowed_doc_ids = self.checker.get_allowed_doc_ids(user_role)
        if not allowed_doc_ids:
            return []
        candidate_docs = self.retriever.search_documents(
            query=query, user_role=user_role, top_k=top_k
        )
        return [
            doc for doc in candidate_docs
            if doc.get("doc_id") in allowed_doc_ids
        ]

    def build_prompt(
        self, query: str, user_role: str, retrieved_docs: List[Dict[str, Any]]
    ) -> str:
        if not retrieved_docs:
            context_str = "Không tìm thấy tài liệu phù hợp trong phạm vi quyền hạn được cấp."
        else:
            context_blocks = []
            for idx, doc in enumerate(retrieved_docs, start=1):
                context_blocks.append(
                    f"--- TÀI LIỆU {idx}: {doc.get('title')} ({doc.get('doc_id')}) ---\n"
                    f"Mức phân loại: {doc.get('classification')}\n"
                    f"Nội dung:\n{doc.get('content', '')}\n"
                )
            context_str = "\n".join(context_blocks)

        return f"""Bạn là Trợ lý Trí tuệ Nhân tạo hỗ trợ thông tin học vụ trong nhà trường.
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

    def query_ollama(self, prompt: str) -> str:
        """Single Ollama request, with bounded generation and timing metrics."""
        url = f"{self.ollama_base_url}/api/generate"
        # Tune via environment without modifying RBAC or retrieval.
        num_predict = max(64, int(os.getenv("OLLAMA_NUM_PREDICT", "256")))
        timeout = max(10, int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120")))
        payload = json.dumps({
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "10m",
            "options": {"num_predict": num_predict},
        }, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        start = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.perf_counter() - start
            if data.get("error"):
                raise RuntimeError("Ollama returned an error")
            answer = data.get("response")
            if not isinstance(answer, str):
                raise ValueError("Invalid Ollama response")
            print(f"[PERF OLLAMA] HTTP total: {elapsed:.2f}s", file=sys.stderr, flush=True)
            for key, label in (
                ("load_duration", "Model load"),
                ("prompt_eval_duration", "Prompt evaluation"),
                ("eval_duration", "Token generation"),
            ):
                value = data.get(key)
                if isinstance(value, (int, float)):
                    print(f"[PERF OLLAMA] {label}: {value / 1e9:.2f}s", file=sys.stderr, flush=True)
            for key in ("prompt_eval_count", "eval_count"):
                value = data.get(key)
                if isinstance(value, int):
                    print(f"[PERF OLLAMA] {key}: {value}", file=sys.stderr, flush=True)
            return answer
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
            # Never include the prompt or document contents in a fallback response.
            print(f"[OLLAMA ERROR] {type(exc).__name__}", file=sys.stderr, flush=True)
            raise RuntimeError("Ollama request failed; check local service logs") from exc

    def answer_query(
        self, query: str, user_role: str, top_k: int = 3
    ) -> Dict[str, Any]:
        retrieved_docs = self.retrieve_context(query, user_role, top_k)
        prompt = self.build_prompt(query, user_role, retrieved_docs)
        response_text = self.query_ollama(prompt)
        return {
            "query": query,
            "user_role": user_role,
            "retrieved_documents": [
                {
                    "doc_id": d.get("doc_id"),
                    "title": d.get("title"),
                    "classification": d.get("classification"),
                    "department": d.get("department"),
                }
                for d in retrieved_docs
            ],
            "total_retrieved": len(retrieved_docs),
            "answer": response_text,
        }


if __name__ == "__main__":
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
        if res["total_retrieved"] == 0:
            print("    [!] Không có quyền hoặc không tìm thấy tài liệu phù hợp.")
