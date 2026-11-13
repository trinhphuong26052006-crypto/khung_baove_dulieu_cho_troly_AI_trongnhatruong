import sys
import json
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

from src.main import initialize_system, execute_end_to_end_pipeline, CONFIG

VALID_ROLES = {"SinhVien", "GiangVien", "QuanTri"}
CLASSIFICATIONS = {"Public", "Internal", "Restricted"}


def emit(payload):
    print("\n---JSON_OUTPUT_START---")
    print(json.dumps(payload, ensure_ascii=False))


def load_metadata():
    path = PROJECT_ROOT / "data" / "metadata" / "documents_metadata.json"
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if isinstance(data, dict):
        data = data.get("documents", [])
    if not isinstance(data, list):
        return {}
    return {item["doc_id"]: item for item in data
            if isinstance(item, dict) and isinstance(item.get("doc_id"), str)}


def get_mode(rbac, output_filter):
    if rbac and output_filter:
        return "Controlled"
    if not rbac and not output_filter:
        return "Baseline"
    return "Custom"


def main():
    if len(sys.argv) < 3:
        emit({"error": "Thiếu tham số query hoặc role"})
        return

    query = sys.argv[1].strip()
    role = sys.argv[2]
    if role not in VALID_ROLES:
        emit({"error": "Vai trò không hợp lệ"})
        return
    if not query:
        emit({"error": "Câu hỏi không được để trống"})
        return

    enable_rbac = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else True
    enable_filter = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else True
    mode = get_mode(enable_rbac, enable_filter)

    # Chỉ dùng Baseline/Custom trong môi trường thử nghiệm được kiểm soát.
    CONFIG["ENABLE_RBAC_PRERETRIEVAL"] = enable_rbac
    CONFIG["ENABLE_OUTPUT_FILTER"] = enable_filter

    try:
        components = initialize_system()
        outcome = execute_end_to_end_pipeline(query, role, components)
        if not isinstance(outcome, dict):
            raise TypeError("Pipeline phải trả về dict")

        metadata = load_metadata()
        retrieved_ids = outcome.get("retrieved_doc_ids") or []
        if not isinstance(retrieved_ids, list):
            retrieved_ids = []

        # Quyền được kiểm tra lại cho phần hiển thị nguồn, kể cả khi Baseline.
        authorized_docs = components.rag_engine.retriever.get_authorized_documents(role)
        docs_map = {
            doc["doc_id"]: doc.get("content", "")
            for doc in authorized_docs
            if isinstance(doc, dict) and isinstance(doc.get("doc_id"), str)
        }

        status = str(outcome.get("status") or "UNKNOWN")
        action = str(outcome.get("action_taken") or "UNKNOWN")
        denial_reason = outcome.get("denial_reason")
        is_denied = (
            denial_reason == "UNAUTHORIZED_DOCUMENT"
            or status.upper() in {"DENIED", "BLOCKED", "FORBIDDEN"}
            or action.upper() in {"BLOCKED", "DENIED"}
        )

        # Nếu hậu kiểm đã thay đổi câu trả lời, không mặc định coi các tài liệu
        # truy xuất là bằng chứng cho phần nội dung còn lại.
        allow_sources = not is_denied and action.upper() not in {"REDACTED", "FILTERED"}
        sources = []
        if allow_sources:
            seen = set()
            for doc_id in retrieved_ids:
                if not isinstance(doc_id, str) or doc_id in seen:
                    continue
                seen.add(doc_id)
                if doc_id not in docs_map:
                    continue
                meta = metadata.get(doc_id)
                if not isinstance(meta, dict):
                    continue
                classification = meta.get("classification")
                allowed_roles = meta.get("allowed_roles", [])
                if classification not in CLASSIFICATIONS:
                    continue
                if not isinstance(allowed_roles, list) or role not in allowed_roles:
                    continue
                content = docs_map[doc_id]
                if not isinstance(content, str):
                    content = ""
                sources.append({
                    "doc_id": doc_id,
                    "title": meta.get("title") or doc_id,
                    "classification": classification,
                    "department": meta.get("department") or "Nhà trường",
                    "university": meta.get("university") or "Trường Đại học",
                    "snippet": (content[:350].strip() + "...") if content else ""
                })

        answer = outcome.get("answer") or ""
        if not isinstance(answer, str):
            answer = str(answer)
        if denial_reason == "UNAUTHORIZED_DOCUMENT":
            answer = "Bạn chưa có quyền truy cập tài liệu này. Vui lòng liên hệ bộ phận quản lý nếu cần hỗ trợ."

        emit({
            "answer": answer,
            "status": status,
            "action_taken": action,
            "is_safe": outcome.get("is_safe"),
            "denial_reason": denial_reason,
            "role": role,
            "latency_ms": outcome.get("latency_ms", 0),
            "mode": mode,
            "retrieved_count": len(sources),
            "sources": sources,
            "sources_label": "Tài liệu được truy xuất (chưa xác minh là trích dẫn trực tiếp)",
        })
    except Exception as exc:
        # Không gửi traceback, đường dẫn nội bộ hoặc dữ liệu nhạy cảm về frontend.
        print(f"Runner error: {type(exc).__name__}: {exc}", file=sys.stderr)
        emit({"error": "Hệ thống tạm thời không xử lý được yêu cầu.",
              "status": "ERROR", "sources": [], "retrieved_count": 0})


if __name__ == "__main__":
    main()
