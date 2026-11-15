
import time
import sys
import json
from pathlib import Path

# ============================================================
# 1. PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(
            encoding="utf-8",
            errors="replace"
        )
        sys.stderr.reconfigure(
            encoding="utf-8",
            errors="replace"
        )
    except (AttributeError, OSError):
        pass

VALID_ROLES = {
    "SinhVien",
    "GiangVien",
    "QuanTri"
}

CLASSIFICATIONS = {
    "Public",
    "Internal",
    "Restricted"
}


# ============================================================
# 2. JSON OUTPUT
# ============================================================

def emit(payload):
    print("\n---JSON_OUTPUT_START---", flush=True)
    print(
        json.dumps(payload, ensure_ascii=False),
        flush=True
    )


# ============================================================
# 3. LOAD DOCUMENT METADATA
# ============================================================

def load_metadata():
    path = (
        PROJECT_ROOT
        / "data"
        / "metadata"
        / "documents_metadata.json"
    )

    if not path.is_file():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, dict):
        data = data.get("documents", [])

    if not isinstance(data, list):
        return {}

    return {
        item["doc_id"]: item
        for item in data
        if isinstance(item, dict)
        and isinstance(item.get("doc_id"), str)
    }


# ============================================================
# 4. SYSTEM MODE
# ============================================================

def get_mode(rbac, output_filter):
    if rbac and output_filter:
        return "Controlled"

    if not rbac and not output_filter:
        return "Baseline"

    return "Custom"


# ============================================================
# 5. MAIN PIPELINE
# ============================================================

def main():

    # --------------------------------------------------------
    # Validate arguments
    # --------------------------------------------------------

    if len(sys.argv) < 3:
        emit({
            "status": "ERROR",
            "error": "Missing query or role",
            "sources": []
        })
        return

    query = sys.argv[1].strip()
    role = sys.argv[2]

    if role not in VALID_ROLES:
        emit({
            "status": "ERROR",
            "error": "Invalid role",
            "sources": []
        })
        return

    if not query:
        emit({
            "status": "ERROR",
            "error": "Question cannot be empty",
            "sources": []
        })
        return

    enable_rbac = (
        sys.argv[3].lower() == "true"
        if len(sys.argv) > 3
        else True
    )

    enable_filter = (
        sys.argv[4].lower() == "true"
        if len(sys.argv) > 4
        else True
    )

    mode = get_mode(
        enable_rbac,
        enable_filter
    )

    try:

        # ----------------------------------------------------
        # Import Python pipeline
        # ----------------------------------------------------

        from src.main import (
            initialize_system,
            execute_end_to_end_pipeline,
            CONFIG
        )

        CONFIG["ENABLE_RBAC_PRERETRIEVAL"] = enable_rbac
        CONFIG["ENABLE_OUTPUT_FILTER"] = enable_filter

        # ----------------------------------------------------
        # PERFORMANCE: Initialize RAG
        # ----------------------------------------------------

        t0 = time.perf_counter()

        components = initialize_system()

        t1 = time.perf_counter()

        # ----------------------------------------------------
        # PERFORMANCE: Execute pipeline
        # ----------------------------------------------------

        outcome = execute_end_to_end_pipeline(
            query,
            role,
            components
        )

        t2 = time.perf_counter()

        print(
            f"[PERF] Khoi tao RAG: {t1 - t0:.2f}s",
            file=sys.stderr,
            flush=True
        )

        print(
            f"[PERF] Xu ly pipeline: {t2 - t1:.2f}s",
            file=sys.stderr,
            flush=True
        )

        # ----------------------------------------------------
        # Validate pipeline response
        # ----------------------------------------------------

        if not isinstance(outcome, dict):
            raise TypeError(
                "Pipeline must return a dictionary"
            )

        # ----------------------------------------------------
        # PERFORMANCE: Load metadata and authorized documents
        # ----------------------------------------------------

        t_sources_start = time.perf_counter()

        metadata = load_metadata()

        retrieved_ids = (
            outcome.get("retrieved_doc_ids") or []
        )

        if not isinstance(retrieved_ids, list):
            retrieved_ids = []

        authorized_docs = (
            components
            .rag_engine
            .retriever
            .get_authorized_documents(role)
        )

        docs_map = {
            doc["doc_id"]: doc.get("content", "")
            for doc in authorized_docs
            if isinstance(doc, dict)
            and isinstance(doc.get("doc_id"), str)
        }

        # ----------------------------------------------------
        # Check status and access denial
        # ----------------------------------------------------

        status = str(
            outcome.get("status") or "UNKNOWN"
        )

        action = str(
            outcome.get("action_taken") or "UNKNOWN"
        )

        denial_reason = outcome.get("denial_reason")

        is_denied = (
            denial_reason == "UNAUTHORIZED_DOCUMENT"
            or status.upper() in {
                "DENIED",
                "BLOCKED",
                "FORBIDDEN"
            }
            or action.upper() in {
                "BLOCKED",
                "DENIED"
            }
        )

        allow_sources = (
            not is_denied
            and action.upper() not in {
                "REDACTED",
                "FILTERED"
            }
        )

        # ----------------------------------------------------
        # Build authorized source list
        # ----------------------------------------------------

        sources = []

        if allow_sources:
            seen = set()

            for doc_id in retrieved_ids:

                if (
                    not isinstance(doc_id, str)
                    or doc_id in seen
                ):
                    continue

                seen.add(doc_id)

                if doc_id not in docs_map:
                    continue

                meta = metadata.get(doc_id)

                if not isinstance(meta, dict):
                    continue

                classification = meta.get(
                    "classification"
                )

                allowed_roles = meta.get(
                    "allowed_roles",
                    []
                )

                if classification not in CLASSIFICATIONS:
                    continue

                if (
                    not isinstance(allowed_roles, list)
                    or role not in allowed_roles
                ):
                    continue

                content = docs_map[doc_id]

                if not isinstance(content, str):
                    content = ""

                sources.append({
                    "doc_id": doc_id,
                    "title": (
                        meta.get("title") or doc_id
                    ),
                    "classification": classification,
                    "department": (
                        meta.get("department")
                        or "Nhà trường"
                    ),
                    "university": (
                        meta.get("university")
                        or "Trường Đại học"
                    ),
                    "snippet": (
                        content[:350].strip() + "..."
                        if content
                        else ""
                    )
                })

        t_sources_end = time.perf_counter()

        print(
            "[PERF] Xu ly metadata va sources: "
            f"{t_sources_end - t_sources_start:.2f}s",
            file=sys.stderr,
            flush=True
        )

        # ----------------------------------------------------
        # Prepare answer
        # ----------------------------------------------------

        answer = outcome.get("answer") or ""

        if not isinstance(answer, str):
            answer = str(answer)

        if denial_reason == "UNAUTHORIZED_DOCUMENT":
            answer = (
                "Bạn chưa có quyền truy cập tài liệu này. "
                "Vui lòng liên hệ bộ phận quản lý "
                "nếu cần hỗ trợ."
            )

        # ----------------------------------------------------
        # Final JSON response
        # ----------------------------------------------------

        emit({
            "answer": answer,
            "status": status,
            "action_taken": action,
            "is_safe": outcome.get("is_safe"),
            "denial_reason": denial_reason,
            "role": role,
            "latency_ms": outcome.get(
                "latency_ms",
                0
            ),
            "mode": mode,
            "retrieved_count": len(sources),
            "sources": sources,
            "sources_label": (
                "Tài liệu được truy xuất "
                "(chưa xác minh là trích dẫn trực tiếp)"
            )
        })

    except Exception as exc:

        print(
            f"Runner error: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
            flush=True
        )

        emit({
            "error": (
                "Python pipeline failed. "
                "Check server logs."
            ),
            "status": "ERROR",
            "action_taken": "ERROR",
            "sources": [],
            "retrieved_count": 0
        })


# ============================================================
# 6. ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
