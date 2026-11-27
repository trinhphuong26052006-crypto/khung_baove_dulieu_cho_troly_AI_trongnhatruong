"""
src/filtering
=============
Package hậu kiểm và lọc an toàn đầu ra cho trợ lý AI nhà trường.
"""

from src.filtering.output_filter import (
    OutputFilter,
    FilterResult,
    ViolationDetail,
    filter_ai_response,
    default_output_filter
)

__all__ = [
    "OutputFilter",
    "FilterResult",
    "ViolationDetail",
    "filter_ai_response",
    "default_output_filter"
]
