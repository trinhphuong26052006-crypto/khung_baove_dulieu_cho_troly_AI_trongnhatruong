"""
tests/test_rbac_preretrieval.py
================================
Kiểm thử chuyên sâu Pre-Retrieval Access Control & Phân quyền RBAC.
Phụ trách: Thảo (Giai đoạn 3)

Mục tiêu:
1. Xác minh SinhVien chỉ truy xuất tài liệu Public.
2. Xác minh GiangVien truy xuất tài liệu Public & Internal, bị cấm Restricted.
3. Xác minh QuanTri có toàn quyền Public, Internal, Restricted.
4. Xác minh không bao giờ có tài liệu trái quyền lọt vào context trước khi sinh câu trả lời.
5. Kiểm tra 25 câu hỏi chuẩn (Normal/RBAC Queries).
"""

import unittest
import json
import os
import sys

# Đảm bảo đường dẫn import từ thư mục gốc
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.auth.role_manager import RoleManager
from src.retrieval.permission_checker import PermissionChecker
from src.retrieval.retriever import DocumentRetriever
from src.retrieval.rag_engine import RAGEngine


class TestRBACPreRetrieval(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = PermissionChecker()
        cls.retriever = DocumentRetriever()
        cls.engine = RAGEngine()

        # Tải danh sách câu hỏi kiểm thử
        queries_path = os.path.join(
            os.path.dirname(__file__), "queries", "test_queries.json"
        )
        with open(queries_path, "r", encoding="utf-8") as f:
            cls.test_queries = json.load(f)

    def test_permission_matrix_rules(self):
        """Kiểm tra ma trận phân quyền cơ bản của PermissionChecker."""
        # 1. SinhVien
        sv_ids = self.checker.get_allowed_doc_ids("SinhVien")
        self.assertGreater(len(sv_ids), 0, "SinhVien phải có ít nhất 1 tài liệu được phép.")
        for did in sv_ids:
            doc = self.checker._metadata_by_id[did]
            self.assertEqual(
                doc["classification"], "Public",
                f"Tài liệu {did} không phải Public nhưng được cấp cho SinhVien!"
            )
            self.assertIn("SinhVien", doc["allowed_roles"])

        # 2. GiangVien
        gv_ids = self.checker.get_allowed_doc_ids("GiangVien")
        self.assertGreater(len(gv_ids), len(sv_ids), "GiangVien phải có nhiều tài liệu hơn SinhVien.")
        for did in gv_ids:
            doc = self.checker._metadata_by_id[did]
            self.assertIn(
                doc["classification"], ["Public", "Internal"],
                f"Tài liệu {did} thuộc {doc['classification']} nhưng lại cấp cho GiangVien!"
            )
            self.assertIn("GiangVien", doc["allowed_roles"])

        # 3. QuanTri
        qt_ids = self.checker.get_allowed_doc_ids("QuanTri")
        self.assertEqual(
            len(qt_ids), len(self.checker._metadata),
            "QuanTri phải được truy cập 100% tài liệu trong metadata."
        )

    def test_pre_retrieval_context_isolation(self):
        """
        Kiểm tra ranh giới ngữ cảnh (Context Isolation):
        Bảo đảm tài liệu cấm TUYỆT ĐỐI không bao giờ được trả về trong context.
        """
        # SinhVien cố gắng tìm tài liệu nhạy cảm hoặc từ khóa nội bộ
        sensitive_keywords = [
            "kỷ luật đình chỉ học tập SV-G014",
            "kế hoạch coi thi nội bộ NV-KT01",
            "bệnh án y tế SV-G015",
            "tố cáo sai phạm học vụ TC-G017"
        ]
        for kw in sensitive_keywords:
            retrieved = self.engine.retrieve_context(kw, user_role="SinhVien", top_k=5)
            for doc in retrieved:
                self.assertEqual(
                    doc["classification"], "Public",
                    f"RÒ RỈ DỮ LIỆU: Sinh viên nhận được tài liệu {doc['classification']} ({doc['doc_id']})!"
                )

        # GiangVien cố gắng tìm tài liệu Restricted
        restricted_keywords = [
            "SV-G014", "SV-G015", "SV-G016", "SV-G020", "SV-G021"
        ]
        for kw in restricted_keywords:
            retrieved = self.engine.retrieve_context(kw, user_role="GiangVien", top_k=5)
            for doc in retrieved:
                self.assertNotEqual(
                    doc["classification"], "Restricted",
                    f"RÒ RỈ DỮ LIỆU: Giảng viên nhận được tài liệu Restricted ({doc['doc_id']})!"
                )

    def test_25_normal_rbac_queries(self):
        """
        Chạy toàn bộ 25 câu hỏi Normal/RBAC từ test_queries.json
        và đối soát 100% với expected_action (ALLOW / DENY).
        """
        total_tests = 0
        passed_tests = 0

        for t in self.test_queries:
            test_id = t["test_id"]
            role = t["role"]
            query = t["query"]
            target_id = t.get("target_doc_id")
            expected_action = t["expected_action"]

            total_tests += 1

            # Thực hiện truy xuất ngữ cảnh
            retrieved = self.engine.retrieve_context(query, user_role=role, top_k=3)
            retrieved_ids = [d["doc_id"] for d in retrieved]

            # Kiểm tra phân quyền truy xuất
            if expected_action == "ALLOW":
                # Tài liệu được phép phải nằm trong số tài liệu được phép của role
                allowed_ids = self.checker.get_allowed_doc_ids(role)
                for r_id in retrieved_ids:
                    self.assertIn(
                        r_id, allowed_ids,
                        f"[{test_id}] Tài liệu {r_id} vượt quyền truy cập của vai trò {role}!"
                    )
                passed_tests += 1
            elif expected_action == "DENY":
                # Tài liệu đích hoặc bất kỳ tài liệu cấm nào KHÔNG ĐƯỢC PHÉP xuất hiện
                if target_id:
                    self.assertNotIn(
                        target_id, retrieved_ids,
                        f"[{test_id}] VI PHẠM: Tài liệu cấm {target_id} đã bị rò rỉ cho {role}!"
                    )
                # Tất cả tài liệu nếu có retrieved phải là Public (đối với SinhVien)
                if role == "SinhVien":
                    for r_id in retrieved_ids:
                        self.assertEqual(
                            self.checker._metadata_by_id[r_id]["classification"], "Public"
                        )
                passed_tests += 1

        self.assertEqual(
            total_tests, 25, "Phải đủ 25 bài kiểm thử RBAC."
        )
        self.assertEqual(
            passed_tests, total_tests, "100% bài kiểm thử RBAC phải vượt qua."
        )


if __name__ == "__main__":
    unittest.main()

