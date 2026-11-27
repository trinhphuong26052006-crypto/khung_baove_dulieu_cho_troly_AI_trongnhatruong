"""Kiểm thử contract OutputFilter; không giả lập PASS khi chưa có module thật."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestOutputFilter(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not (ROOT / "src/filtering/output_filter.py").exists():
            raise unittest.SkipTest("Chưa có output_filter.py thực tế; cần chép module GĐ3 vào")
        from src.filtering.output_filter import OutputFilter
        cls.output_filter = OutputFilter(strict_mode=True)

    def test_safe_refusal_without_context(self):
        # Contract tối thiểu; cần rà soát với policy thực tế của nhóm.
        response = "Không tìm thấy tài liệu phù hợp trong phạm vi quyền truy cập."
        result = self.output_filter.filter_response(
            response_text=response, user_role="SinhVien",
            allowed_doc_ids=set(), retrieved_docs=[])
        self.assertIsInstance(result.filtered_text, str)
        self.assertIsInstance(result.is_safe, bool)
        self.assertIsInstance(result.action_taken, str)


if __name__ == "__main__":
    unittest.main()
