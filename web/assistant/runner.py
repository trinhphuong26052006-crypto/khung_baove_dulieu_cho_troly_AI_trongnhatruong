
"""
================================================================================
AI SCHOOL ASSISTANT - PHP/PYTHON INTEGRATION RUNNER
================================================================================
File: web/assistant/runner.py

Chức năng:
    1. Nhận truy vấn từ PHP/XAMPP thông qua command-line arguments.
    2. Nhận vai trò người dùng: SinhVien / GiangVien / QuanTri.
    3. Nhận cấu hình RBAC và Output Filter từ api.php.
    4. Khởi tạo hệ thống thông qua src.main.initialize_system().
    5. Thực thi pipeline thông qua execute_end_to_end_pipeline().
    6. Thu thập tài liệu nguồn thực sự được truy xuất.
    7. Xuất kết quả JSON chuẩn hóa cho PHP/JavaScript.

CLI:
    python runner.py "query" "role" true true

Arguments:
    argv[1]: User query
    argv[2]: User role
    argv[3]: Enable RBAC (optional)
    argv[4]: Enable Output Filter (optional)
    argv[5]: Test ID (optional)

JSON OUTPUT:
    ---JSON_OUTPUT_START---
    {
        "success": true,
        "status": "SUCCESS",
        "answer": "...",
        "role": "SinhVien",
        "mode": "Controlled",
        "sources": [],
        "retrieved_doc_ids": [],
        "action_taken": "PASSED",
        "latency_ms": 1000
    }
================================================================================
"""

import os
import sys
import json
import io
import time
import traceback
from pathlib import Path
from contextlib import redirect_stdout
from typing import Any, Dict, List, Optional


# ==============================================================================
# 1. PROJECT CONFIGURATION
# ==============================================================================

# runner.py nằm tại: project_root/web/assistant/runner.py
WEB_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = next(
    (root for root in (WEB_ROOT, WEB_ROOT.parent) if (root / "src" / "main.py").is_file()),
    None,
)
if PROJECT_ROOT is None:
    print("Missing project root containing src/main.py", file=sys.stderr)
    raise SystemExit(1)

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.chdir(PROJECT_ROOT)

# UTF-8 encoding cho Windows / XAMPP
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass


# ==============================================================================
# 2. IMPORT MAIN PIPELINE
# ==============================================================================

try:
    from src.main import (
        CONFIG,
        initialize_system,
        execute_end_to_end_pipeline,
    )

    from src.auth.role_manager import RoleManager

    IMPORT_ERROR = None

except Exception as exc:
    IMPORT_ERROR = exc


# ==============================================================================
# 3. CONSTANTS
# ==============================================================================

JSON_OUTPUT_MARKER = "---JSON_OUTPUT_START---"

VALID_ROLES = {
    "SinhVien",
    "GiangVien",
    "QuanTri",
}

DEFAULT_ENABLE_RBAC = True
DEFAULT_ENABLE_FILTER = True


# ==============================================================================
# 4. ARGUMENT PARSING
# ==============================================================================

def parse_boolean(value: Optional[str], default: bool = True) -> bool:
    """
    Chuyển đổi chuỗi CLI thành Boolean.

    Hỗ trợ:
        true, 1, yes, on  -> True
        false, 0, no, off -> False
    """

    if value is None:
        return default

    normalized = str(value).strip().lower()

    if normalized in ("true", "1", "yes", "on"):
        return True

    if normalized in ("false", "0", "no", "off"):
        return False

    raise ValueError(
        "Invalid boolean argument. "
        "Accepted values: true/false, 1/0, yes/no, on/off."
    )


def parse_arguments() -> Dict[str, Any]:
    """
    Đọc các tham số được truyền từ PHP hoặc CLI.
    """

    if sys.argv[1:] == ["--web-stdin"]:
        payload = json.loads(sys.stdin.read(16385))
        query = payload.get("query")
        role = payload.get("role")
        if not isinstance(query, str) or not query.strip() or len(query) > 500:
            raise ValueError("Invalid query.")
        if not isinstance(role, str) or role not in VALID_ROLES:
            raise ValueError("Invalid authenticated role.")
        return {"query": query.strip(), "role": role, "enable_rbac": True,
                "enable_filter": True, "test_id": None, "web_request": True}

    if len(sys.argv) < 3:
        raise ValueError(
            'Usage: python runner.py "query" "role" '
            '[enableRbac] [enableFilter] [testId]'
        )

    query = sys.argv[1].strip()
    role = sys.argv[2].strip()

    enable_rbac = parse_boolean(
        sys.argv[3] if len(sys.argv) > 3 else None,
        DEFAULT_ENABLE_RBAC,
    )

    enable_filter = parse_boolean(
        sys.argv[4] if len(sys.argv) > 4 else None,
        DEFAULT_ENABLE_FILTER,
    )

    test_id = (
        sys.argv[5].strip()
        if len(sys.argv) > 5 and sys.argv[5].strip()
        else None
    )

    if not query:
        raise ValueError("Query must not be empty.")

    if role not in VALID_ROLES:
        raise ValueError(
            "Invalid user role. Accepted roles: "
            "SinhVien, GiangVien, QuanTri."
        )

    return {
        "query": query,
        "role": role,
        "enable_rbac": enable_rbac,
        "enable_filter": enable_filter,
        "test_id": test_id,
    }


# ==============================================================================
# 5. SECURITY MODE CONFIGURATION
# ==============================================================================

def configure_security_mode(
    enable_rbac: bool,
    enable_filter: bool,
) -> str:
    """
    Đồng bộ cấu hình bảo mật từ PHP vào main.py.

    Controlled:
        RBAC = ON
        Output Filter = ON

    Baseline:
        RBAC = OFF
        Output Filter = OFF

    Custom:
        Hai thiết lập có trạng thái khác nhau.
    """

    CONFIG["ENABLE_RBAC_PRERETRIEVAL"] = enable_rbac

    # Đồng bộ alias tương thích ngược.
    CONFIG["ENABLE_PERMISSION_CHECK"] = enable_rbac

    CONFIG["ENABLE_OUTPUT_FILTER"] = enable_filter

    if enable_rbac and enable_filter:
        mode = "Controlled"

    elif not enable_rbac and not enable_filter:
        mode = "Baseline"

    else:
        mode = "Custom"

    return mode


# ==============================================================================
# 6. SOURCE DOCUMENT COLLECTOR
# ==============================================================================

def collect_sources(
    components: Any,
    retrieved_doc_ids: List[str],
    user_role: str,
    enable_rbac: bool,
) -> List[Dict[str, Any]]:
    """
    Thu thập metadata của các tài liệu thực sự được truy xuất.

    Nguyên tắc:
        - Không tự tạo nguồn tài liệu.
        - Không trả về toàn bộ tài liệu metadata.
        - Chỉ trả về tài liệu có doc_id nằm trong retrieved_doc_ids.
        - Controlled: chỉ lấy nguồn trong phạm vi vai trò.
        - Baseline: dùng ngữ cảnh QuanTri để tương thích với cơ chế
          mô phỏng truy xuất toàn bộ tài liệu của main.py.
    """

    if not retrieved_doc_ids:
        return []

    try:
        effective_role = user_role if enable_rbac else "QuanTri"

        checker = components.permission_checker
        retrieved_id_set = set(retrieved_doc_ids)
        authorized_docs = checker.get_allowed_documents(effective_role, "read")

        sources = []

        for doc in authorized_docs:

            doc_id = doc.get("doc_id")

            if doc_id not in retrieved_id_set:
                continue

            sources.append({
                "doc_id": doc_id,
                "title": doc.get("title", "Untitled document"),
                "classification": doc.get(
                    "classification",
                    "Unknown"
                ),
                "department": doc.get(
                    "department",
                    "Unknown"
                ),
            })

        return sources

    except Exception as exc:
        print(
            f"[RUNNER SOURCE ERROR] {type(exc).__name__}",
            file=sys.stderr,
            flush=True,
        )

        # Fail closed: không trả về nguồn chưa xác minh.
        return []


# ==============================================================================
# 7. JSON RESPONSE BUILDER
# ==============================================================================

def build_response(
    success: bool,
    status: str,
    answer: str = "",
    role: str = "",
    mode: str = "Unknown",
    sources: Optional[List[Dict[str, Any]]] = None,
    retrieved_doc_ids: Optional[List[str]] = None,
    action_taken: str = "NOT_RUN",
    latency_ms: float = 0.0,
    violations: Optional[List[Dict[str, Any]]] = None,
    error: Optional[str] = None,
    enable_rbac: bool = True,
    enable_filter: bool = True,
    test_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Chuẩn hóa dữ liệu trả về cho api.php.
    """

    return {
        "success": success,
        "status": status,
        "answer": answer,
        "role": role,
        "mode": mode,

        "rbac_enabled": enable_rbac,
        "filter_enabled": enable_filter,

        "sources": sources or [],
        "retrieved_doc_ids": retrieved_doc_ids or [],

        "action_taken": action_taken,
        "latency_ms": round(float(latency_ms), 2),

        "violations": violations or [],

        "test_id": test_id,
        "error": error,
    }


# ==============================================================================
# 8. MAIN REQUEST HANDLER
# ==============================================================================

def process_request(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Xử lý một truy vấn hoàn chỉnh từ PHP.

    Luồng:
        PHP
         |
         v
        runner.py
         |
         v
        Configure security mode
         |
         v
        initialize_system()
         |
         v
        execute_end_to_end_pipeline()
         |
         v
        Collect sources
         |
         v
        Build JSON response
         |
         v
        PHP / JavaScript
    """

    start_time = time.perf_counter()

    query = arguments["query"]
    role = arguments["role"]

    enable_rbac = arguments["enable_rbac"]
    enable_filter = arguments["enable_filter"]

    test_id = arguments["test_id"]

    mode = configure_security_mode(
        enable_rbac,
        enable_filter,
    )

    # --------------------------------------------------------------------------
    # STEP 1: INITIALIZE SYSTEM
    # --------------------------------------------------------------------------

    print(
        f"[RUNNER] Initializing system - Mode: {mode}",
        file=sys.stderr,
        flush=True,
    )

    if not arguments.get("web_request"):
        CONFIG["AUDIT_LOG_FILE"] = str(PROJECT_ROOT / "logs" / "experiment_audit.jsonl")
    components = initialize_system()

    # --------------------------------------------------------------------------
    # STEP 2: VALIDATE ROLE
    # --------------------------------------------------------------------------

    if role not in VALID_ROLES:
        raise ValueError("Unauthorized or invalid role.")

    # --------------------------------------------------------------------------
    # STEP 3: EXECUTE END-TO-END PIPELINE
    # --------------------------------------------------------------------------

    print(
        f"[RUNNER] Executing pipeline - Role: {role}",
        file=sys.stderr,
        flush=True,
    )

    pipeline_result = execute_end_to_end_pipeline(
        raw_query=query,
        user_role=role,
        components=components,
        test_id=test_id,
    )

    # --------------------------------------------------------------------------
    # STEP 4: EXTRACT PIPELINE RESULT
    # --------------------------------------------------------------------------

    if not isinstance(pipeline_result, dict):
        raise RuntimeError(
            "Pipeline returned an invalid response."
        )

    answer = pipeline_result.get("answer", "")

    status = pipeline_result.get(
        "status",
        "UNKNOWN",
    )

    action_taken = pipeline_result.get(
        "action_taken",
        "NOT_RUN",
    )

    retrieved_doc_ids = pipeline_result.get(
        "retrieved_doc_ids",
        [],
    )

    violations = pipeline_result.get(
        "violations",
        [],
    )

    # Đảm bảo dữ liệu đầu ra có đúng kiểu.
    if not isinstance(answer, str):
        answer = ""

    if not isinstance(retrieved_doc_ids, list):
        retrieved_doc_ids = []

    if not isinstance(violations, list):
        violations = []

    retrieved_doc_ids = [
        str(doc_id)
        for doc_id in retrieved_doc_ids
        if doc_id
    ]

    # --------------------------------------------------------------------------
    # STEP 5: COLLECT SOURCE DOCUMENTS
    # --------------------------------------------------------------------------

    blocked = action_taken in {"BLOCKED", "BLOCKED_INPUT", "DENIED"} or (
        pipeline_result.get("is_safe") is not True
    )
    sources = [] if blocked else collect_sources(
        components, retrieved_doc_ids, role, enable_rbac
    )
    retrieved_doc_ids = [source["doc_id"] for source in sources]
    if arguments.get("web_request"):
        violations = []

    # --------------------------------------------------------------------------
    # STEP 6: BUILD RESPONSE
    # --------------------------------------------------------------------------

    elapsed_ms = (
        time.perf_counter() - start_time
    ) * 1000

    response = build_response(
        success=True,
        status=status,
        answer=answer,
        role=role,
        mode=mode,
        sources=sources,
        retrieved_doc_ids=retrieved_doc_ids,
        action_taken=action_taken,
        latency_ms=elapsed_ms,
        violations=violations,
        enable_rbac=enable_rbac,
        enable_filter=enable_filter,
        test_id=test_id,
    )

    print(
        f"[RUNNER] Request completed - "
        f"Status: {status} - "
        f"Latency: {elapsed_ms:.2f}ms",
        file=sys.stderr,
        flush=True,
    )

    if arguments.get("web_request"):
        response["access_status"] = "AUTHORIZED" if sources else "NOT_VERIFIED"
        response["output_filter_status"] = (
            action_taken if action_taken in {"PASSED", "BLOCKED", "REDACTED"} else "NOT_RUN"
        )

    return response


# ==============================================================================
# 9. ERROR HANDLING
# ==============================================================================

def handle_error(
    exc: Exception,
    arguments: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Xử lý lỗi an toàn.

    Không đưa stack trace, prompt hoặc nội dung tài liệu vào JSON trả về.
    Chi tiết kỹ thuật được ghi vào stderr.
    """

    print(
        f"[RUNNER ERROR] {type(exc).__name__}: {str(exc)}",
        file=sys.stderr,
        flush=True,
    )

    

    args = arguments or {}

    return build_response(
        success=False,
        status="ERROR",
        answer="",
        role=args.get("role", ""),
        mode="Unknown",
        sources=[],
        retrieved_doc_ids=[],
        action_taken="ERROR",
        latency_ms=0,
        error=(
            "The request could not be processed. "
            "Please check the Python service logs."
        ),
        enable_rbac=args.get(
            "enable_rbac",
            DEFAULT_ENABLE_RBAC,
        ),
        enable_filter=args.get(
            "enable_filter",
            DEFAULT_ENABLE_FILTER,
        ),
        test_id=args.get("test_id"),
    )


# ==============================================================================
# 10. ENTRY POINT
# ==============================================================================

def main() -> None:
    """
    Điểm khởi chạy chính.

    QUAN TRỌNG:
        stdout chỉ chứa marker và JSON.
        Các thông tin khởi tạo, debug và pipeline được giữ trong buffer
        hoặc chuyển sang stderr để không phá vỡ JSON của PHP.
    """

    arguments = None
    response = None

    # Capture toàn bộ print() từ main.py và các module được gọi.
    captured_output = io.StringIO()

    try:

        if IMPORT_ERROR is not None:
            raise RuntimeError(
                f"Module import failed: {type(IMPORT_ERROR).__name__}"
            ) from IMPORT_ERROR

        # ----------------------------------------------------------------------
        # Parse CLI arguments
        # ----------------------------------------------------------------------

        arguments = parse_arguments()

        # ----------------------------------------------------------------------
        # Execute system pipeline
        # ----------------------------------------------------------------------

        with redirect_stdout(captured_output):

            response = process_request(arguments)

        # Chuyển log pipeline sang stderr, không làm nhiễu JSON stdout.
        pipeline_logs = captured_output.getvalue()

        if pipeline_logs:
            print(
                pipeline_logs,
                file=sys.stderr,
                flush=True,
            )

    except Exception as exc:

        response = handle_error(
            exc,
            arguments,
        )

        # Không đưa nội dung log chứa câu hỏi hoặc context ra JSON.
        captured_output.close()

    # --------------------------------------------------------------------------
    # OUTPUT JSON FOR PHP
    # --------------------------------------------------------------------------

    try:

        json_output = json.dumps(
            response,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )

        print(JSON_OUTPUT_MARKER, flush=True)
        print(json_output, flush=True)

    except (TypeError, ValueError) as exc:

        print(
            f"[JSON SERIALIZATION ERROR] {type(exc).__name__}",
            file=sys.stderr,
            flush=True,
        )

        fallback = build_response(
            success=False,
            status="ERROR",
            error="Unable to serialize the system response.",
            action_taken="ERROR",
        )

        print(JSON_OUTPUT_MARKER, flush=True)
        print(
            json.dumps(
                fallback,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
            flush=True,
        )


if __name__ == "__main__":
    main()
