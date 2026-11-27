"""src/auth/role_manager.py
Mô phỏng và quản lý vai trò người dùng phục vụ kiểm thử RBAC.
Không phải hệ thống authentication danh tính thực tế.
"""
from typing import List, Optional

class RoleManager:
    VALID_ROLES: List[str] = ["SinhVien", "GiangVien", "QuanTri"]

    ROLE_DESCRIPTIONS = {
        "SinhVien": "Sinh viên",
        "GiangVien": "Giảng viên",
        "QuanTri": "Quản trị viên / Lãnh đạo",
    }

    def __init__(self, default_role: Optional[str] = None):
        self._current_role: Optional[str] = None
        if default_role is not None and not self.set_role(default_role):
            raise ValueError(f"Vai trò mặc định không hợp lệ: {default_role}")

    @classmethod
    def get_valid_roles(cls) -> List[str]:
        return cls.VALID_ROLES.copy()

    @classmethod
    def normalize_role(cls, role: str) -> Optional[str]:
        if role is None:
            return None
        cleaned = str(role).strip().lower()
        for valid in cls.VALID_ROLES:
            if valid.lower() == cleaned:
                return valid
        return None

    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        return cls.normalize_role(role) is not None

    def set_role(self, role: str) -> bool:
        raw = str(role).strip()
        if raw in {"1", "2", "3"}:
            self._current_role = self.VALID_ROLES[int(raw) - 1]
            return True
        normalized = self.normalize_role(raw)
        if normalized is None:
            return False
        self._current_role = normalized
        return True

    def get_current_role(self) -> Optional[str]:
        return self._current_role

    def clear_role(self) -> None:
        self._current_role = None

    def can_access_document(self, document_metadata: dict) -> bool:
        """Document-level authorization dựa trực tiếp vào allowed_roles."""
        if self._current_role is None:
            return False
        roles = document_metadata.get("allowed_roles", [])
        if isinstance(roles, str):
            roles = [x.strip() for x in roles.split("|") if x.strip()]
        return self._current_role in roles

    def display_roles_menu(self) -> None:
        print("=" * 60)
        print("TRỢ LÝ AI NHÀ TRƯỜNG - MÔ PHỎNG VAI TRÒ KIỂM THỬ RBAC")
        print("=" * 60)
        for idx, role in enumerate(self.VALID_ROLES, 1):
            print(f"[{idx}] {role}: {self.ROLE_DESCRIPTIONS[role]}")

    def prompt_select_role(self) -> str:
        self.display_roles_menu()
        while True:
            user_input = input("Chọn vai trò [1-3] hoặc nhập tên vai trò: ").strip()
            if self.set_role(user_input):
                print(f"[VAI TRÒ ĐÃ ĐƯỢC THIẾT LẬP] {self._current_role}")
                return self._current_role
            print("[LỖI] Vai trò không hợp lệ.")

current_role_manager = RoleManager()

if __name__ == "__main__":
    mgr = RoleManager()
    mgr.prompt_select_role()
