"""
================================================================================
HỆ THỐNG TRỢ LÝ AI NHÀ TRƯỜNG - MÁY CHỦ WEB API & GIAO DIỆN HỎI ĐÁP
================================================================================
File: web_app.py
Chức năng:
    - Máy chủ HTTP chuẩn (sử dụng http.server tích hợp sẵn của Python 3, không cần cài thêm thư viện).
    - Cung cấp RESTful API:
        + GET  /api/health       : Kiểm tra trạng thái máy chủ
        + GET  /api/roles        : Danh sách vai trò và phân quyền (RBAC)
        + GET  /api/config       : Cấu hình hiện tại (Baseline vs Controlled)
        + POST /api/config       : Chuyển đổi chế độ Baseline / Controlled
        + POST /api/chat         : Gửi câu hỏi và nhận câu trả lời cùng nguồn trích dẫn
        + GET  /api/sample-queries: Lấy danh sách 40 câu hỏi mẫu (Normal & Attack)
        + GET  /api/stats        : Thống kê kiểm thử, hiệu năng và bảo mật (Nhiệm vụ Phương)
        + GET  /api/logs         : Đọc lịch sử nhật ký bảo mật từ security_audit.log
        + GET  /api/document     : Xem chi tiết nội dung văn bản nguồn
    - Phục vụ giao diện web hiện đại (Dark Theme) chuẩn giao diện Courdx / Claude.
================================================================================
"""

import os
import sys
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any, List

# Đảm bảo đường dẫn gốc của dự án luôn nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Cấu hình encoding UTF-8 cho console Windows
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import src.main as main_pipeline
from src.main import initialize_system, execute_end_to_end_pipeline, CONFIG

# Khởi tạo pipeline và các component một lần khi chạy web server
print("[WEB SERVER] Đang nạp hệ thống RBAC, RAG Engine và Guardrails...")
COMPONENTS = initialize_system()
print("[WEB SERVER] Đã sẵn sàng phục vụ!")

STATIC_DIR = PROJECT_ROOT / "web" / "static"


def get_metadata_dict() -> Dict[str, Any]:
    meta_path = PROJECT_ROOT / "data" / "metadata" / "documents_metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
            return {d["doc_id"]: d for d in docs}
    return {}


METADATA_BY_ID = get_metadata_dict()


class AIRequestHandler(BaseHTTPRequestHandler):
    """Bộ xử lý yêu cầu HTTP phục vụ Frontend và các API JSON."""

    def _set_headers(self, status_code: int = 200, content_type: str = "application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)

        # 1. API: Kiểm tra trạng thái
        if path == "/api/health":
            self._set_headers(200)
            self.wfile.write(json.dumps({"status": "UP", "time": time.time()}).encode("utf-8"))
            return

        # 2. API: Lấy vai trò và phân quyền
        elif path == "/api/roles":
            self._set_headers(200)
            roles_info = {
                "SinhVien": {
                    "name": "Sinh viên",
                    "badge": "SinhVien",
                    "accessible": ["Public"],
                    "description": "Chỉ xem các văn bản học vụ, học phí, biểu mẫu công khai."
                },
                "GiangVien": {
                    "name": "Giảng viên",
                    "badge": "GiangVien",
                    "accessible": ["Public", "Internal"],
                    "description": "Xem văn bản công khai và tài liệu chuyên môn nội bộ nhà trường."
                },
                "QuanTri": {
                    "name": "Quản trị viên",
                    "badge": "QuanTri",
                    "accessible": ["Public", "Internal", "Restricted"],
                    "description": "Toàn quyền truy cập cả hồ sơ kỷ luật, kiểm toán và văn bản mật."
                }
            }
            self.wfile.write(json.dumps(roles_info, ensure_ascii=False).encode("utf-8"))
            return

        # 3. API: Lấy cấu hình chế độ hiện tại
        elif path == "/api/config":
            self._set_headers(200)
            cfg = {
                "ENABLE_RBAC_PRERETRIEVAL": CONFIG.get("ENABLE_RBAC_PRERETRIEVAL", True),
                "ENABLE_RELEVANCE_GATE": CONFIG.get("ENABLE_RELEVANCE_GATE", True),
                "ENABLE_OUTPUT_FILTER": CONFIG.get("ENABLE_OUTPUT_FILTER", True),
                "STRICT_OUTPUT_FILTER": CONFIG.get("STRICT_OUTPUT_FILTER", True),
                "OLLAMA_MODEL": CONFIG.get("OLLAMA_MODEL", "llama3.2"),
                "TOP_K_DOCUMENTS": CONFIG.get("TOP_K_DOCUMENTS", 3)
            }
            self.wfile.write(json.dumps(cfg, ensure_ascii=False).encode("utf-8"))
            return

        # 4. API: Lấy danh sách câu hỏi mẫu (40 ca test)
        elif path == "/api/sample-queries":
            self._set_headers(200)
            q_path = PROJECT_ROOT / "tests" / "queries" / "test_queries.json"
            if q_path.exists():
                with open(q_path, "r", encoding="utf-8") as f:
                    cases = json.load(f)
                self.wfile.write(json.dumps(cases, ensure_ascii=False).encode("utf-8"))
            else:
                self.wfile.write(json.dumps([]).encode("utf-8"))
            return

        # 5. API: Lấy thống kê kiểm thử và bảo mật (Nhiệm vụ Phương)
        elif path == "/api/stats":
            self._set_headers(200)
            test_results_path = PROJECT_ROOT / "tests" / "results" / "test_results.json"
            queries_path = PROJECT_ROOT / "tests" / "queries" / "test_queries.json"

            stats = {
                "total_documents": len(METADATA_BY_ID),
                "public_docs": sum(1 for d in METADATA_BY_ID.values() if d.get("classification") == "Public"),
                "internal_docs": sum(1 for d in METADATA_BY_ID.values() if d.get("classification") == "Internal"),
                "restricted_docs": sum(1 for d in METADATA_BY_ID.values() if d.get("classification") == "Restricted"),
                "test_cases_count": 0,
                "normal_cases": 0,
                "attack_cases": 0,
                "has_test_results": False,
                "test_pass_count": 0,
                "test_error_count": 0
            }

            if queries_path.exists():
                with open(queries_path, "r", encoding="utf-8") as f:
                    cases = json.load(f)
                    stats["test_cases_count"] = len(cases)
                    stats["normal_cases"] = sum(1 for c in cases if c.get("category") == "normal_rbac")
                    stats["attack_cases"] = sum(1 for c in cases if c.get("category") == "attack")

            if test_results_path.exists():
                try:
                    with open(test_results_path, "r", encoding="utf-8") as f:
                        tr = json.load(f)
                        results = tr.get("results", [])
                        stats["has_test_results"] = True
                        stats["test_pass_count"] = sum(1 for r in results if r.get("retrieval_pass"))
                        stats["test_error_count"] = sum(1 for r in results if r.get("status") == "ERROR")
                except Exception:
                    pass

            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode("utf-8"))
            return

        # 6. API: Lấy nhật ký bảo mật gần nhất (security_audit.log)
        elif path == "/api/logs":
            self._set_headers(200)
            log_path = PROJECT_ROOT / "data" / "logs" / "security_audit.log"
            logs = []
            if log_path.exists():
                try:
                    with open(log_path, "r", encoding="utf-8") as f:
                        lines = [line.strip() for line in f if line.strip()]
                        for line in lines[-50:]:  # Lấy 50 dòng log gần nhất
                            try:
                                logs.append(json.loads(line))
                            except Exception:
                                continue
                except Exception:
                    pass
            self.wfile.write(json.dumps(logs, ensure_ascii=False).encode("utf-8"))
            return

        # 7. API: Xem nội dung chi tiết một tài liệu
        elif path == "/api/document":
            doc_id = query_params.get("doc_id", [""])[0]
            self._set_headers(200)
            if not doc_id:
                self.wfile.write(json.dumps({"error": "Thiếu doc_id"}).encode("utf-8"))
                return

            meta = METADATA_BY_ID.get(doc_id, {})
            # Tìm nội dung trong bộ nạp của retriever
            content = ""
            for doc in COMPONENTS.rag_engine.retriever.get_authorized_documents("QuanTri"):
                if doc.get("doc_id") == doc_id:
                    content = doc.get("content", "")
                    break

            res = {
                "doc_id": doc_id,
                "title": meta.get("title", ""),
                "classification": meta.get("classification", "Public"),
                "department": meta.get("department", ""),
                "university": meta.get("university", ""),
                "description": meta.get("description", ""),
                "content": content
            }
            self.wfile.write(json.dumps(res, ensure_ascii=False).encode("utf-8"))
            return

        # 8. Phục vụ file giao diện (HTML/CSS/JS)
        else:
            if path in ["/", "/index.html"]:
                file_to_serve = STATIC_DIR / "index.html"
                content_type = "text/html"
            else:
                rel_path = path.lstrip("/")
                file_to_serve = STATIC_DIR / rel_path
                if path.endswith(".css"):
                    content_type = "text/css"
                elif path.endswith(".js"):
                    content_type = "application/javascript"
                elif path.endswith(".svg"):
                    content_type = "image/svg+xml"
                elif path.endswith(".png"):
                    content_type = "image/png"
                else:
                    content_type = "text/plain"

            if file_to_serve.exists() and file_to_serve.is_file():
                self._set_headers(200, content_type)
                with open(file_to_serve, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self._set_headers(404, "text/plain")
                self.wfile.write(b"404 Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            body = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            body = {}

        # 1. API: Cấu hình hệ thống (Bật/tắt Baseline vs Controlled)
        if path == "/api/config":
            if "ENABLE_RBAC_PRERETRIEVAL" in body:
                CONFIG["ENABLE_RBAC_PRERETRIEVAL"] = bool(body["ENABLE_RBAC_PRERETRIEVAL"])
            if "ENABLE_RELEVANCE_GATE" in body:
                CONFIG["ENABLE_RELEVANCE_GATE"] = bool(body["ENABLE_RELEVANCE_GATE"])
            if "ENABLE_OUTPUT_FILTER" in body:
                CONFIG["ENABLE_OUTPUT_FILTER"] = bool(body["ENABLE_OUTPUT_FILTER"])

            self._set_headers(200)
            self.wfile.write(json.dumps({
                "message": "Cập nhật cấu hình thành công",
                "config": {
                    "ENABLE_RBAC_PRERETRIEVAL": CONFIG["ENABLE_RBAC_PRERETRIEVAL"],
                    "ENABLE_RELEVANCE_GATE": CONFIG["ENABLE_RELEVANCE_GATE"],
                    "ENABLE_OUTPUT_FILTER": CONFIG["ENABLE_OUTPUT_FILTER"]
                }
            }, ensure_ascii=False).encode("utf-8"))
            return

        # 2. API: Hỏi đáp AI qua RAG và RBAC
        elif path == "/api/chat":
            query = body.get("query", "").strip()
            role = body.get("role", "SinhVien")
            test_id = body.get("test_id", None)

            if not query:
                self._set_headers(400)
                self.wfile.write(json.dumps({"error": "Vui lòng nhập câu hỏi"}).encode("utf-8"))
                return

            if role not in ["SinhVien", "GiangVien", "QuanTri"]:
                role = "SinhVien"

            # Chạy toàn trình qua execute_end_to_end_pipeline
            start_t = time.time()
            outcome = execute_end_to_end_pipeline(
                raw_query=query,
                user_role=role,
                components=COMPONENTS,
                test_id=test_id
            )
            elapsed_ms = round((time.time() - start_t) * 1000, 2)

            retrieved_ids = outcome.get("retrieved_doc_ids", [])
            sources = []
            for doc_id in retrieved_ids:
                meta = METADATA_BY_ID.get(doc_id, {})
                # Trích đoạn nội dung
                preview_snippet = ""
                for doc in COMPONENTS.rag_engine.retriever.get_authorized_documents("QuanTri"):
                    if doc.get("doc_id") == doc_id:
                        content_full = doc.get("content", "")
                        preview_snippet = content_full[:350].strip() + "..."
                        break

                sources.append({
                    "doc_id": doc_id,
                    "title": meta.get("title", doc_id),
                    "classification": meta.get("classification", "Public"),
                    "department": meta.get("department", "Nhà trường"),
                    "university": meta.get("university", "Trường Đại học"),
                    "snippet": preview_snippet,
                    "file_path": meta.get("file_path", f"{doc_id}.md")
                })

            response_payload = {
                "answer": outcome.get("answer", ""),
                "status": outcome.get("status", "SUCCESS"),
                "action_taken": outcome.get("action_taken", "PASSED"),
                "is_safe": outcome.get("is_safe", True),
                "role": role,
                "latency_ms": elapsed_ms,
                "mode": "Controlled" if CONFIG.get("ENABLE_RBAC_PRERETRIEVAL", True) else "Baseline",
                "retrieved_count": len(sources),
                "sources": sources
            }

            self._set_headers(200)
            self.wfile.write(json.dumps(response_payload, ensure_ascii=False).encode("utf-8"))
            return

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint không tồn tại"}).encode("utf-8"))


def run_server(port: int = 8080):
    server_address = ("127.0.0.1", port)
    httpd = HTTPServer(server_address, AIRequestHandler)
    print("=" * 70)
    print(f"🚀 MÁY CHỦ HỎI ĐÁP AI ĐANG CHẠY TẠI: http://localhost:{port}")
    print("=" * 70)
    print("Nhấn Ctrl + C để dừng máy chủ.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[WEB SERVER] Đã dừng máy chủ thành công.")
        httpd.server_close()


if __name__ == "__main__":
    port_arg = 8080
    if len(sys.argv) > 1:
        try:
            port_arg = int(sys.argv[1])
        except ValueError:
            pass
    run_server(port_arg)

