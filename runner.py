import sys
import json
from pathlib import Path

# Đảm bảo import được module trong src
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Cấu hình UTF-8 cho console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import src.main as m
from src.main import initialize_system, execute_end_to_end_pipeline, CONFIG

def main():
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Thiếu tham số query hoặc role"}))
        return

    query = sys.argv[1]
    role = sys.argv[2]
    enable_rbac = sys.argv[3].lower() == "true" if len(sys.argv) > 3 else True
    enable_filter = sys.argv[4].lower() == "true" if len(sys.argv) > 4 else True

    CONFIG["ENABLE_RBAC_PRERETRIEVAL"] = enable_rbac
    CONFIG["ENABLE_OUTPUT_FILTER"] = enable_filter

    components = initialize_system()
    outcome = execute_end_to_end_pipeline(query, role, components)

    # Đọc metadata
    meta_path = PROJECT_ROOT / "data" / "metadata" / "documents_metadata.json"
    metadata_by_id = {}
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            for item in json.load(f):
                metadata_by_id[item["doc_id"]] = item

    retrieved_ids = outcome.get("retrieved_doc_ids", [])
    sources = []
    all_docs = components.rag_engine.retriever.get_authorized_documents("QuanTri")
    docs_map = {d["doc_id"]: d.get("content", "") for d in all_docs}

    for doc_id in retrieved_ids:
        meta = metadata_by_id.get(doc_id, {})
        full_content = docs_map.get(doc_id, "")
        preview_snippet = full_content[:350].strip() + "..." if full_content else ""
        sources.append({
            "doc_id": doc_id,
            "title": meta.get("title", doc_id),
            "classification": meta.get("classification", "Public"),
            "department": meta.get("department", "Nhà trường"),
            "university": meta.get("university", "Trường Đại học"),
            "snippet": preview_snippet
        })

    response_payload = {
        "answer": outcome.get("answer", ""),
        "status": outcome.get("status", "SUCCESS"),
        "action_taken": outcome.get("action_taken", "PASSED"),
        "is_safe": outcome.get("is_safe", True),
        "role": role,
        "latency_ms": outcome.get("latency_ms", 0),
        "mode": "Controlled" if enable_rbac else "Baseline",
        "retrieved_count": len(sources),
        "sources": sources,
        "violations": outcome.get("violations", [])
    }

    print("\n---JSON_OUTPUT_START---")
    print(json.dumps(response_payload, ensure_ascii=False))

if __name__ == "__main__":
    main()

