"""Input guard cơ bản cho prototype.

Không thay thế RBAC/pre-retrieval authorization. Keyword matching có thể gây
false refusal; cần đo trên tập test trước khi thay đổi chính sách.
"""
from __future__ import annotations
from typing import Iterable

DEFAULT_BLOCKED_KEYWORDS = (
    "sql injection", "drop table", "union select",
    "ignore previous instructions", "bypass security",
)


def validate_input(user_input: str, *, max_length: int = 500,
                   blocked_keywords: Iterable[str] = DEFAULT_BLOCKED_KEYWORDS) -> tuple[bool, str]:
    """Trả về (hợp lệ, câu hỏi đã làm sạch hoặc lý do từ chối)."""
    if not isinstance(user_input, str):
        return False, "Câu hỏi phải là chuỗi văn bản."
    if max_length < 1:
        raise ValueError("max_length phải lớn hơn 0")
    cleaned = user_input.strip()
    if not cleaned:
        return False, "Câu hỏi không được để trống."
    if len(cleaned) > max_length:
        return False, f"Câu hỏi quá dài ({len(cleaned)} ký tự). Giới hạn {max_length} ký tự."
    lowered = cleaned.casefold()
    for keyword in blocked_keywords:
        if isinstance(keyword, str) and keyword and keyword.casefold() in lowered:
            # Không phản chiếu nội dung prompt/keyword trong thông báo hoặc log.
            return False, "Câu hỏi chứa mẫu chỉ dẫn không được hỗ trợ bởi chính sách đầu vào."
    return True, cleaned
