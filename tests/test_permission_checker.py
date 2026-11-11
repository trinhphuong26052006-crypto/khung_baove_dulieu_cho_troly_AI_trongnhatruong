from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.auth.permission_checker import PermissionChecker

checker = PermissionChecker()

docs = [
    {"doc_id": "DOC-P001", "allowed_roles": ["SinhVien", "GiangVien", "QuanTri"]},
    {"doc_id": "DOC-I001", "allowed_roles": ["GiangVien", "QuanTri"]},
    {"doc_id": "DOC-R001", "allowed_roles": ["QuanTri"]},
]

expected = {
    "SinhVien": ["DOC-P001"],
    "GiangVien": ["DOC-P001", "DOC-I001"],
    "QuanTri": ["DOC-P001", "DOC-I001", "DOC-R001"],
}

for role, expected_ids in expected.items():
    allowed, _ = checker.filter_authorized_metadata(role, docs)
    actual_ids = [d["doc_id"] for d in allowed]
    assert actual_ids == expected_ids, (role, actual_ids, expected_ids)

assert checker.check_document("RoleGia", docs[0]).allowed is False
assert checker.check_document("SinhVien", {"doc_id": "DOC-X001"}).allowed is False

print("PERMISSION CHECKER TEST: PASS")
