"""
================================================================================
HỆ THỐNG TRỢ LÝ AI NHÀ TRƯỜNG - KHUNG BẢO VỆ DỮ LIỆU TOÀN DIỆN (END-TO-END)
================================================================================
File: src/main.py
Mục đích:
    Điểm khởi chạy chính (Entry Point) kết nối luồng xử lý toàn trình (End-to-End)
    theo đúng quy trình chuẩn 5 bước:
      1. Thiết lập ngữ cảnh vai trò và tiếp nhận câu hỏi (Role Context & User Input).
      2. PermissionChecker xác định các mức tài liệu được phép truy cập (RBAC Policy).
      3. Retriever chỉ tìm kiếm trong những tài liệu thuộc phạm vi được phép (Authorized Retrieval).
      4. RAG Engine nhận kết quả hợp lệ để tạo câu trả lời (Grounded AI Generation).
      5. Output Filter kiểm tra lại câu trả lời trước khi hiển thị (Output Guardrails).

Bố cục mã nguồn:
    1. CẤU HÌNH HỆ THỐNG (SYSTEM CONFIGURATION).
    2. CÁC HÀM TIỆN ÍCH GIAO DIỆN (UI & FORMATTING HELPERS).
    3. KHỞI TẠO HỆ THỐNG (SYSTEM INITIALIZATION).
    4. CÁC BƯỚC XỬ LÝ TRONG QUY TRÌNH (PIPELINE STEPS 1 - 5).
    5. ĐIỀU PHỐI LUỒNG TOÀN TRÌNH (END-TO-END PIPELINE ORCHESTRATOR).
    6. VÒNG LẶP TƯƠNG TÁC (INTERACTIVE CLI CHAT LOOP).
    7. ĐIỂM KHỞI CHẠY CHÍNH (MAIN FUNCTION & ENTRY POINT).
================================================================================
"""

import os
import sys
import re
import json
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

# Đảm bảo đường dẫn gốc của dự án luôn nằm trong sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Cấu hình encoding UTF-8 cho console Windows tránh lỗi ký tự tiếng Việt
if sys.platform == "win32":
    try:
        if sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if sys.stderr.encoding.lower() != "utf-8":
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        if sys.stdin.encoding.lower() != "utf-8":
            sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Import các module cốt lõi của hệ thống
from src.auth.role_manager import RoleManager
from src.retrieval.permission_checker import PermissionChecker
from src.retrieval.retriever import DocumentRetriever
from src.retrieval.rag_engine import RAGEngine
from src.filtering.output_filter import OutputFilter, FilterResult


# ==============================================================================
# 1. CẤU HÌNH HỆ THỐNG (SYSTEM CONFIGURATION)
#    (Thay đổi các thiết lập tại đây mà không cần sửa sâu vào mã nguồn)
# ==============================================================================

CONFIG: Dict[str, Any] = {
    # Thông tin ứng dụng
    "APP_NAME": "TRỢ LÝ AI HỌC VỤ NHÀ TRƯỜNG",
    "APP_SUBTITLE": "HỆ THỐNG BẢO VỆ DỮ LIỆU & KIỂM SOÁT PHÂN QUYỀN TOÀN TRÌNH",
    "VERSION": "2.0-RBAC-E2E",
    
    # Cấu hình truy xuất (Retrieval)
    "TOP_K_DOCUMENTS": 3,
    
    # Cấu hình mô hình LLM (Ollama)
    "OLLAMA_MODEL": "llama3.2",
    "OLLAMA_BASE_URL": "http://localhost:11434",
    
    # Cấu hình kiểm soát an toàn đầu vào (P2.0)
    "MAX_INPUT_LENGTH": 500,
    "BLOCKED_KEYWORDS": [
        "sql injection", "drop table", "union select", 
        "ignore previous instructions", "bypass security"
    ],
    
    # Cấu hình bộ lọc an toàn đầu ra (P5.0)
    "STRICT_OUTPUT_FILTER": True, # Chặn toàn bộ phản hồi nếu vi phạm nghiêm trọng (lộ tài liệu Mật)

    # Cấu hình nhật ký bảo mật (P6.0)
    "ENABLE_AUDIT_LOG": True,
    "AUDIT_LOG_FILE": os.path.join(PROJECT_ROOT, "data", "logs", "security_audit.log"),
    
    # Tùy chọn hiển thị chi tiết (Debug/Verbose mode)
    "VERBOSE_DEBUG": False
}


# ==============================================================================
# 2. CÁC HÀM TIỆN ÍCH GIAO DIỆN (UI & FORMATTING HELPERS)
# ==============================================================================

def print_banner() -> None:
    """Hiển thị biểu ngữ chào mừng của hệ thống."""
    width = 76
    print("\n" + "=" * width)
    print(f"{CONFIG['APP_NAME']:^{width}}")
    print(f"{CONFIG['APP_SUBTITLE']:^{width}}")
    print(f"Phiên bản: {CONFIG['VERSION']} | Kiểm soát Pre-retrieval RBAC Active".center(width))
    print("=" * width + "\n")


def print_section_divider(title: str) -> None:
    """In thanh phân cách tiêu đề các giai đoạn."""
    width = 76
    print("\n" + "-" * width)
    print(f" ▶ {title}")
    print("-" * width)


def clear_console() -> None:
    """Xóa màn hình console."""
    os.system("cls" if os.name == "nt" else "clear")


# ==============================================================================
# 3. KHỞI TẠO HỆ THỐNG (SYSTEM INITIALIZATION)
# ==============================================================================

class SystemComponents:
    """Lưu trữ tập trung các đối tượng dịch vụ cốt lõi của hệ thống."""
    def __init__(self, role_manager: RoleManager, 
                 permission_checker: PermissionChecker,
                 retriever: DocumentRetriever,
                 rag_engine: RAGEngine,
                 output_filter: OutputFilter):
        self.role_manager = role_manager
        self.permission_checker = permission_checker
        self.retriever = retriever
        self.rag_engine = rag_engine
        self.output_filter = output_filter


def initialize_system() -> SystemComponents:
    """
    Khởi tạo toàn bộ các module trong hệ sinh thái an toàn thông tin:
    - RoleManager: Quản lý/mô phỏng ngữ cảnh vai trò phục vụ kiểm thử.
    - PermissionChecker: Kiểm tra metadata và danh sách tài liệu được phép.
    - DocumentRetriever: Tìm kiếm và đọc nội dung tài liệu an toàn.
    - RAGEngine: Điều phối RAG và kết nối mô hình sinh ngôn ngữ.
    - OutputFilter: Hậu kiểm và lọc an toàn câu trả lời của AI.
    """
    print("[KHỞI TẠO] Đang nạp các module bảo mật và cơ sở dữ liệu...")
    
    role_manager = RoleManager()
    permission_checker = PermissionChecker()
    retriever = DocumentRetriever()
    rag_engine = RAGEngine(
        ollama_model=CONFIG["OLLAMA_MODEL"],
        ollama_base_url=CONFIG["OLLAMA_BASE_URL"]
    )
    output_filter = OutputFilter(strict_mode=CONFIG.get("STRICT_OUTPUT_FILTER", True))
    
    # Đảm bảo thư mục lưu log tồn tại
    if CONFIG["ENABLE_AUDIT_LOG"]:
        log_dir = os.path.dirname(CONFIG["AUDIT_LOG_FILE"])
        os.makedirs(log_dir, exist_ok=True)
        
    print("[KHỞI TẠO] Hoàn tất nạp cấu hình hệ thống.\n")
    return SystemComponents(role_manager, permission_checker, retriever, rag_engine, output_filter)


# ==============================================================================
# 4. CÁC BƯỚC XỬ LÝ TRONG PIPELINE (PIPELINE PHASES P1.0 - P6.0)
# ==============================================================================

# --- [P1.0] THIẾT LẬP NGỮ CẢNH VAI TRÒ (ROLE CONTEXT) -------------------------

def p1_authenticate_user(role_manager: RoleManager) -> str:
    """
    [P1.0] Xác định vai trò người dùng trong phiên làm việc.
    Hỗ trợ vai trò: SinhVien, GiangVien, QuanTri.
    """
    user_role = role_manager.prompt_select_role()
    return user_role


def p1_display_role_permissions(user_role: str, permission_checker: PermissionChecker) -> None:
    """
    [P1.0] Hiển thị tóm tắt phạm vi quyền hạn và số lượng tài liệu được phép truy cập.
    """
    allowed_docs = permission_checker.get_allowed_documents(user_role)
    total_allowed = len(allowed_docs)
    
    # Phân nhóm theo phân loại
    public_count = sum(1 for d in allowed_docs if d.get("classification") == "Public")
    internal_count = sum(1 for d in allowed_docs if d.get("classification") == "Internal")
    restricted_count = sum(1 for d in allowed_docs if d.get("classification") == "Restricted")
    
    print("\n" + "┌" + "─" * 74 + "┐")
    print(f"│ BẢNG PHÂN QUYỀN TRUY CẬP CHO VAI TRÒ: {user_role:<34} │")
    print("├" + "─" * 74 + "┤")
    print(f"│  • Tài liệu Công khai (Public)     : {public_count:>3} tài liệu {'[CHO PHÉP]':>26} │")
    
    status_internal = "[CHO PHÉP]" if user_role in ["GiangVien", "QuanTri"] else "[TỪ CHỐI/CẤM]"
    print(f"│  • Tài liệu Nội bộ (Internal)      : {internal_count:>3} tài liệu {status_internal:>26} │")
    
    status_restricted = "[CHO PHÉP]" if user_role == "QuanTri" else "[TỪ CHỐI/CẤM]"
    print(f"│  • Hồ sơ Mật/Giới hạn (Restricted) : {restricted_count:>3} tài liệu {status_restricted:>26} │")
    print("├" + "─" * 74 + "┤")
    # Không hard-code 96: lấy tổng số tài liệu từ metadata mà PermissionChecker đang quản lý.
    try:
        total_docs = len(permission_checker.get_all_documents())
    except (AttributeError, TypeError):
        # Tương thích với phiên bản PermissionChecker chưa có get_all_documents().
        # Khi đó chỉ hiển thị số tài liệu được phép thay vì đưa ra tổng số sai.
        total_docs = None

    if total_docs is not None:
        print(f"│  ▶ TỔNG SỐ TÀI LIỆU ĐƯỢC PHÉP TRUY CẬP: {total_allowed:>3} / {total_docs:<3} tài liệu             │")
    else:
        print(f"│  ▶ TỔNG SỐ TÀI LIỆU ĐƯỢC PHÉP TRUY CẬP: {total_allowed:>3} tài liệu                   │")
    print("└" + "─" * 74 + "┘\n")


# --- [P2.0] TIẾP NHẬN & KIỂM TRA ĐẦU VÀO (INPUT GUARDRAILS) -------------------

def p2_validate_input(user_input: str) -> Tuple[bool, str]:
    """
    [P2.0] Kiểm tra tính hợp lệ và an toàn của câu hỏi từ người dùng:
    - Loại trừ chuỗi rỗng.
    - Giới hạn độ dài tránh tấn công tràn bối cảnh (Context Overflow).
    - Phát hiện các từ khóa nghi vấn tấn công Prompt Injection cơ bản.
    """
    cleaned = user_input.strip()
    
    if not cleaned:
        return False, "Câu hỏi không được để trống."
        
    if len(cleaned) > CONFIG["MAX_INPUT_LENGTH"]:
        return False, f"Câu hỏi quá dài ({len(cleaned)} ký tự). Vui lòng giới hạn dưới {CONFIG['MAX_INPUT_LENGTH']} ký tự."
        
    cleaned_lower = cleaned.lower()
    for kw in CONFIG["BLOCKED_KEYWORDS"]:
        if kw in cleaned_lower:
            return False, f"Phát hiện ký tự/mẫu câu có nguy cơ mất an toàn thông tin: '{kw}'."
            
    return True, cleaned


# ==============================================================================
# HÀM BẢO VỆ ĐÁNH GIÁ MỨC ĐỘ PHÙ HỢP CỦA TÀI LIỆU TRUY XUẤT (RELEVANCE GATE)
# ==============================================================================

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


# --- [P3.0] TRUY XUẤT TÀI LIỆU CÓ PHÂN QUYỀN (RBAC-AWARE RETRIEVAL) ----------

def p3_retrieve_authorized_documents(
    query: str, 
    user_role: str, 
    rag_engine: RAGEngine
) -> List[Dict[str, Any]]:
    """
    [P3.0] Truy xuất tài liệu liên quan áp dụng Pre-retrieval Access Control:
    - Tìm kiếm tài liệu thuộc quyền hạn của user_role.
    - Áp dụng Relevance Gate: Lọc bỏ triệt để các tài liệu không liên quan đến câu hỏi.
    """
    candidate_docs = rag_engine.retrieve_context(
        query=query, 
        user_role=user_role, 
        top_k=CONFIG["TOP_K_DOCUMENTS"]
    )
    
    # Lọc chỉ giữ lại các tài liệu thực sự phù hợp với câu hỏi
    relevant_docs = [doc for doc in candidate_docs if is_document_relevant(query, doc, user_role)]
    return relevant_docs


# --- [P4.0] XỬ LÝ SINH CÂU TRẢ LỜI BẰNG AI / RAG (SAFE AI GENERATION) ---------

def p4_generate_safe_answer(
    query: str, 
    user_role: str, 
    retrieved_docs: List[Dict[str, Any]], 
    rag_engine: RAGEngine
) -> str:
    """
    [P4.0] Lắp ráp ngữ cảnh an toàn vào Prompt và gửi tới mô hình AI (Ollama).
    Nếu không tìm thấy tài liệu phù hợp trong phạm vi quyền, hệ thống tự động từ chối
    một cách lịch sự theo đúng nguyên tắc bảo vệ dữ liệu.
    """
    prompt = rag_engine.build_prompt(
        query=query,
        user_role=user_role,
        retrieved_docs=retrieved_docs
    )
    
    if CONFIG["VERBOSE_DEBUG"]:
        print("\n--- [DEBUG] NỘI DUNG PROMPT GỬI ĐẾN LLM ---")
        print(prompt[:300] + "... (đã rút gọn)")
        print("-------------------------------------------\n")
        
    answer = rag_engine.query_ollama(prompt)
    return answer


# --- [P5.0] HẬU KIỂM VÀ LỌC AN TOÀN ĐẦU RA (OUTPUT GUARDRAILS) ----------------

def p5_validate_and_format_output(
    answer: str, 
    user_role: str, 
    retrieved_docs: List[Dict[str, Any]],
    output_filter: OutputFilter,
    allowed_doc_ids: Optional[Set[str]] = None
) -> Tuple[str, FilterResult]:
    """
    [Bước 5] Hậu kiểm câu trả lời bằng module OutputFilter trước khi gửi cho người dùng:
    - Đối chiếu mã tài liệu với danh mục được cấp phép (allowed_doc_ids) theo vai trò (RBAC).
    - Ngăn chặn rò rỉ mã tài liệu cấm (DOC-Ixxx, DOC-Rxxx) và mã hồ sơ kỷ luật (SV-Gxxx...).
    - Phát hiện và che giấu thông tin định danh cá nhân (CCCD, SĐT, Email cá nhân).
    - ĐÁNH GIÁ TÍNH CĂN CỨ TỪ NGUỒN (Groundedness Check): Ngăn chặn việc AI tự bịa thông tin
      hoặc viện dẫn tên trường ngoài tài liệu tham khảo.
    - Cơ chế phòng thủ nghiêm ngặt (Fail-Closed): Nếu bộ lọc lỗi hoặc từ chối, chặn ngay lập tức.
    """
    filter_result = output_filter.filter_response(
        response_text=answer,
        user_role=user_role,
        allowed_doc_ids=allowed_doc_ids,
        retrieved_docs=retrieved_docs
    )

    if filter_result.is_safe:
        if filter_result.source_grounded:
            print("[Bước 5 - Output Filter]: Phản hồi đạt chuẩn an toàn thông tin và có căn cứ nguồn đối soát (PASSED).")
        else:
            print("[Bước 5 - Output Filter]: Phản hồi đạt chuẩn an toàn thông tin (Xác nhận từ chối an toàn, KHÔNG có tài liệu căn cứ nguồn hỗ trợ).")
    else:
        if filter_result.action_taken == "BLOCKED":
            print("[Bước 5 - CẢNH BÁO BẢO MẬT]: Đã CHẶN câu trả lời do vi phạm an toàn hoặc không có căn cứ từ nguồn (BLOCKED)!")
        elif filter_result.action_taken == "REDACTED":
            print("[Bước 5 - LỌC DỮ LIỆU]: Đã CHE các thông tin nhạy cảm/PII hoặc thông tin chưa kiểm chứng trong câu trả lời (REDACTED).")

        for v in filter_result.violations:
            print(f"   ! [{v.severity}] {v.violation_type}: {v.description}")

    return filter_result.filtered_text, filter_result


# --- GHI NHẬT KÝ BẢO MẬT (SECURITY AUDIT LOGGING) ------------------------------

def p6_audit_log(
    user_role: str, 
    query: str, 
    retrieved_docs: List[Dict[str, Any]], 
    status: str,
    filter_result: Optional[FilterResult] = None
) -> None:
    """
    Ghi nhận lịch sử truy vấn vào tệp log phục vụ công tác thanh tra và kiểm toán an toàn.
    """
    if not CONFIG["ENABLE_AUDIT_LOG"]:
        return
        
    log_entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "user_role": user_role,
        # Data minimization: không lưu nguyên văn prompt/query vào security log.
        "query_sha256": hashlib.sha256(query.encode("utf-8")).hexdigest(),
        "query_length": len(query),
        "retrieved_doc_count": len(retrieved_docs),
        "retrieved_doc_ids": [d.get("doc_id") for d in retrieved_docs],
        "status": status,
        "output_safety": {
            "is_safe": filter_result.is_safe if filter_result else True,
            "action_taken": filter_result.action_taken if filter_result else "PASSED",
            "violations_count": len(filter_result.violations) if filter_result else 0
        }
    }
    
    try:
        with open(CONFIG["AUDIT_LOG_FILE"], "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as ex:
        if CONFIG["VERBOSE_DEBUG"]:
            print(f"[CẢNH BÁO] Không thể ghi log bảo mật: {ex}")


# ==============================================================================
# 5. ĐIỀU PHỐI LUỒNG TOÀN TRÌNH (END-TO-END PIPELINE ORCHESTRATOR)
#    Quy trình xử lý 5 bước chính + bước 6 ghi Audit Log:
#    1. Tiếp nhận câu hỏi trong ngữ cảnh vai trò đã thiết lập.
#    2. PermissionChecker xác định các mức tài liệu được phép truy cập.
#    3. Retriever chỉ tìm kiếm trong những tài liệu thuộc phạm vi được phép.
#    4. RAG Engine nhận kết quả hợp lệ để tạo câu trả lời.
#    5. Output Filter kiểm tra lại câu trả lời trước khi hiển thị.
    6. Audit Logger ghi sự kiện tối thiểu phục vụ kiểm toán.
# ==============================================================================

def execute_end_to_end_pipeline(
    raw_query: str, 
    user_role: str, 
    components: SystemComponents
) -> None:
    """
    Điều phối toàn bộ quy trình theo 5 bước chuẩn hóa từ khi tiếp nhận câu hỏi đến khi hiển thị.
    """
    start_time = time.time()
    print_section_divider(f"QUY TRÌNH XỬ LÝ TRUY VẤN - VAI TRÒ: [{user_role}]")
    
    # -------------------------------------------------------------------------
    # Bước 1: Người dùng gửi câu hỏi và vai trò
    # -------------------------------------------------------------------------
    is_valid, validated_or_error = p2_validate_input(raw_query)
    if not is_valid:
        print(f"[Bước 1 - LỖI ĐẦU VÀO]: {validated_or_error}")
        p6_audit_log(user_role, raw_query, [], status=f"REJECTED_INPUT: {validated_or_error}")
        return
        
    query = validated_or_error
    print(f"[Bước 1]: Tiếp nhận câu hỏi ({len(query)} ký tự) từ vai trò [{user_role}].")
    
    # -------------------------------------------------------------------------
    # Bước 2: PermissionChecker xác định các mức tài liệu được phép truy cập
    # -------------------------------------------------------------------------
    allowed_classifications = components.permission_checker.get_allowed_classifications(user_role)
    allowed_doc_ids = components.permission_checker.get_allowed_doc_ids(user_role)
    cls_str = ", ".join(allowed_classifications) if allowed_classifications else "Không có"
    print(f"[Bước 2 - PermissionChecker]: Mức tài liệu được phép truy cập: [{cls_str}] ({len(allowed_doc_ids)} tài liệu hợp lệ)")
    
    # -------------------------------------------------------------------------
    # Bước 3: Retriever chỉ tìm kiếm trong những tài liệu thuộc phạm vi được phép
    # -------------------------------------------------------------------------
    print(f"[Bước 3 - Retriever]: Đang tìm kiếm tài liệu trong phạm vi được phép [{cls_str}]...")
    retrieved_docs = p3_retrieve_authorized_documents(
        query=query, 
        user_role=user_role, 
        rag_engine=components.rag_engine
    )

    # Defense-in-depth: dù Retriever phải lọc quyền trước retrieval, main.py vẫn
    # kiểm tra lại ID tài liệu trước khi đưa context sang LLM.
    unauthorized_docs = [
        d for d in retrieved_docs
        if d.get("doc_id") not in allowed_doc_ids
    ]
    if unauthorized_docs:
        blocked_ids = [d.get("doc_id") for d in unauthorized_docs]
        print(f"[CẢNH BÁO RBAC] Retriever trả về tài liệu ngoài quyền: {blocked_ids}. Đã loại bỏ.")
        retrieved_docs = [
            d for d in retrieved_docs
            if d.get("doc_id") in allowed_doc_ids
        ]
    
    # -------------------------------------------------------------------------
    # Bước 4: RAG Engine nhận kết quả hợp lệ để tạo câu trả lời
    # -------------------------------------------------------------------------
    if not retrieved_docs:
        print("[Bước 3 - Retriever]: Không tìm thấy tài liệu phù hợp trong danh mục được cấp phép.")
        print("[Bước 4 - RAG Engine]: Không gọi AI suy đoán khi không có tài liệu căn cứ.")
        
        # Tạo thông báo từ chối an toàn có căn cứ theo vai trò
        if user_role == "SinhVien":
            transcript_terms = ["bảng điểm", "điểm của tôi", "kết quả học tập", "điểm số", "xem điểm", "điểm thi của"]
            restricted_terms = [
                "kiểm toán", "kỷ luật", "khiếu nại", "mật", "đình chỉ", 
                "nội bộ", "hội đồng khoa học", "quyền truy cập"
            ]
            q_lower = query.lower()
            if any(term in q_lower for term in transcript_terms):
                raw_answer = (
                    f"[THÔNG BÁO HỆ THỐNG]\n"
                    f"Không tìm thấy dữ liệu bảng điểm cá nhân trong danh mục Công khai (Public) dành cho vai trò [SinhVien].\n"
                    f"Thông tin bảng điểm cá nhân và kết quả học tập chi tiết của người học thuộc diện dữ liệu cá nhân/bảo mật, "
                    f"không được cung cấp trên hệ thống trợ lý AI theo quy chế bảo vệ dữ liệu của nhà trường.\n"
                    f"Sinh viên vui lòng đăng nhập vào Cổng thông tin đào tạo (Portal sinh viên) hoặc liên hệ Phòng Đào tạo để tra cứu bảng điểm chính thức.\n"
                    f"Hệ thống từ chối suy đoán hoặc sử dụng kiến thức bên ngoài khi không có căn cứ từ tài liệu chính thức."
                )
            elif any(term in q_lower for term in restricted_terms):
                raw_answer = (
                    f"[THÔNG BÁO HỆ THỐNG]\n"
                    f"Không tìm thấy tài liệu phù hợp trong danh mục Công khai (Public) dành cho vai trò [SinhVien].\n"
                    f"Chủ đề bạn tra cứu ('{query}') có thể thuộc danh mục Tài liệu Nội bộ hoặc Hồ sơ Mật "
                    f"mà vai trò Sinh viên không được phép truy cập theo quy chế bảo vệ dữ liệu."
                )
            else:
                raw_answer = (
                    f"[THÔNG BÁO HỆ THỐNG]\n"
                    f"Không tìm thấy tài liệu học vụ nào phù hợp với câu hỏi '{query}' trong phạm vi quyền hạn của vai trò [SinhVien]."
                )
        elif user_role == "GiangVien":
            raw_answer = (
                f"[THÔNG BÁO HỆ THỐNG]\n"
                f"Không tìm thấy tài liệu phù hợp với câu hỏi '{query}' trong danh mục tài liệu Công khai và Nội bộ của vai trò [GiangVien]."
            )
        else:
            raw_answer = (
                f"[THÔNG BÁO HỆ THỐNG]\n"
                f"Không tìm thấy tài liệu phù hợp với câu hỏi '{query}' trong cơ sở dữ liệu."
            )
    else:
        print(f"[Bước 3 - Retriever]: Đã trích xuất {len(retrieved_docs)} tài liệu hợp lệ trong phạm vi [{cls_str}]:")
        for idx, doc in enumerate(retrieved_docs, start=1):
            cls_badge = f"[{doc.get('classification')}]"
            print(f"   ({idx}) {cls_badge:<12} {doc.get('doc_id')}: {doc.get('title')}")
            
        print("[Bước 4 - RAG Engine]: Đang tổng hợp ngữ cảnh hợp lệ và tạo câu trả lời...")
        raw_answer = p4_generate_safe_answer(
            query=query,
            user_role=user_role,
            retrieved_docs=retrieved_docs,
            rag_engine=components.rag_engine
        )
    
    # -------------------------------------------------------------------------
    # Bước 5: Output Filter kiểm tra lại câu trả lời trước khi hiển thị
    # -------------------------------------------------------------------------
    print("[Bước 5 - Output Filter]: Đang rà soát an toàn thông tin, quyền tiết lộ và căn cứ...")
    final_answer, filter_result = p5_validate_and_format_output(
        answer=raw_answer, 
        user_role=user_role, 
        retrieved_docs=retrieved_docs,
        output_filter=components.output_filter,
        allowed_doc_ids=allowed_doc_ids
    )
    elapsed_time = time.time() - start_time
    
    print("\n" + "=" * 76)
    print(f"🤖 TRỢ LÝ AI TRẢ LỜI (Thời gian xử lý: {elapsed_time:.2f}s):")
    print("=" * 76)
    print(final_answer)
    
    # CHỈ HIỂN THỊ NGUỒN THAM KHẢO KHI CÓ TÀI LIỆU PHÙ HỢP VÀ ĐƯỢC OUTPUT FILTER CHẤP THUẬN
    if retrieved_docs and filter_result.is_safe and filter_result.action_taken != "BLOCKED":
        print("\n" + "-" * 76)
        print("📚 TÀI LIỆU THAM KHẢO HỢP LỆ ĐÃ SỬ DỤNG:")
        for doc in retrieved_docs:
            print(f"  • [{doc.get('classification')}] {doc.get('doc_id')} - {doc.get('title')} ({doc.get('department')})")
    print("=" * 76)
    
    # Ghi log kiểm toán an toàn
    audit_status = "SUCCESS" if filter_result.is_safe else f"ALERT_{filter_result.action_taken}"
    p6_audit_log(
        user_role=user_role, 
        query=query, 
        retrieved_docs=retrieved_docs, 
        status=audit_status,
        filter_result=filter_result
    )


# ==============================================================================
# 6. VÒNG LẶP TƯƠNG TÁC (INTERACTIVE CLI CHAT LOOP)
# ==============================================================================

def display_help_menu() -> None:
    """Hiển thị bảng trợ giúp các lệnh thao tác nhanh."""
    print("\n" + "┌" + "─" * 74 + "┐")
    print("│                     CÁC LỆNH TIỆN ÍCH HỆ THỐNG                           │")
    print("├" + "─" * 74 + "┤")
    print("│  /role      : Đổi vai trò người dùng (SinhVien, GiangVien, QuanTri)       │")
    print("│  /docs      : Xem lại danh sách quyền & số lượng tài liệu được xem        │")
    print("│  /clear     : Xóa sạch màn hình console                                  │")
    print("│  /help      : Hiển thị bảng trợ giúp này                                 │")
    print("│  exit, quit : Thoát ứng dụng                                             │")
    print("└" + "─" * 74 + "┘\n")


def interactive_chat_session(components: SystemComponents, initial_role: str) -> None:
    """
    Vòng lặp tương tác chính với người dùng:
    - Nhận câu hỏi và chuyển qua pipeline xử lý.
    - Hỗ trợ các lệnh điều khiển hệ thống nhanh mà không cần khởi động lại.
    """
    current_role = initial_role
    display_help_menu()
    
    while True:
        try:
            prompt_label = f"[{current_role}] Nhập câu hỏi (hoặc /help): "
            user_input = input(prompt_label).strip()
            
            # Xử lý lệnh thoát
            if user_input.lower() in ["exit", "quit", ":q"]:
                print("\n[HỆ THỐNG] Đã kết thúc phiên làm việc. Tạm biệt!")
                break
                
            # Xử lý lệnh rỗng
            if not user_input:
                continue
                
            # Xử lý các lệnh tiện ích (Slash Commands)
            if user_input.startswith("/"):
                cmd = user_input.lower().split()[0]
                
                if cmd == "/role":
                    print("\n[ĐỔI VAI TRÒ]:")
                    new_role = components.role_manager.prompt_select_role()
                    if new_role:
                        current_role = new_role
                        p1_display_role_permissions(current_role, components.permission_checker)
                    continue
                    
                elif cmd == "/docs":
                    p1_display_role_permissions(current_role, components.permission_checker)
                    continue
                    
                elif cmd in ["/clear", "/cls"]:
                    clear_console()
                    print_banner()
                    continue
                    
                elif cmd == "/help":
                    display_help_menu()
                    continue
                    
                else:
                    print(f"[HỆ THỐNG] Lệnh '{cmd}' không xác định. Gõ /help để xem hướng dẫn.")
                    continue
                    
            # Thực thi luồng xử lý truy vấn toàn trình (P2.0 -> P6.0)
            execute_end_to_end_pipeline(
                raw_query=user_input,
                user_role=current_role,
                components=components
            )
            print() # Dòng trống phân cách lượt chat
            
        except (KeyboardInterrupt, EOFError):
            print("\n\n[HỆ THỐNG] Nhận tín hiệu ngắt (Ctrl+C). Đang thoát chương trình an toàn...")
            break
        except Exception as e:
            print(f"\n[LỖI HỆ THỐNG]: Đã xảy ra lỗi không mong muốn: {e}")
            if CONFIG["VERBOSE_DEBUG"]:
                import traceback
                traceback.print_exc()


# ==============================================================================
# 7. ĐIỂM KHỞI CHẠY CHÍNH (MAIN FUNCTION & ENTRY POINT)
# ==============================================================================

def main() -> None:
    """
    Hàm thực thi khởi đầu của toàn bộ chương trình:
    1. In biểu ngữ khởi động.
    2. Khởi tạo các module dịch vụ (RoleManager, PermissionChecker, Retriever, RAGEngine).
    3. Thiết lập ngữ cảnh vai trò ban đầu (P1.0).
    4. Hiển thị bảng phân quyền truy cập.
    5. Bắt đầu phiên trò chuyện tương tác end-to-end.
    """
    # Xóa màn hình và in banner
    clear_console()
    print_banner()
    
    # 1. Khởi tạo các thành phần hệ thống
    components = initialize_system()
    
    # 2. [P1.0] Thiết lập ngữ cảnh vai trò ban đầu
    current_role = p1_authenticate_user(components.role_manager)
    if not current_role:
        print("[LỖI] Không thể thiết lập vai trò người dùng. Dừng chương trình.")
        return
        
    # 3. Hiển thị quyền truy cập của vai trò đã chọn
    p1_display_role_permissions(current_role, components.permission_checker)
    
    # 4. Bước vào vòng lặp tương tác toàn trình
    interactive_chat_session(components, current_role)


if __name__ == "__main__":
    main()
