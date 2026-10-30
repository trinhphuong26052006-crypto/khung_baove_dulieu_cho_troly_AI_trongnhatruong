"""
src/auth/role_manager.py
========================
Module xác thực và quản lý vai trò người dùng trong hệ thống trợ lý AI nhà trường.

Vai trò kiến trúc:
- Cổng vào (Entry point) của toàn bộ hệ thống phân quyền (RBAC).
- Mọi quyết định "được xem tài liệu nào" trong pipeline truy xuất RAG đều phụ thuộc
  vào vai trò mà module này trả về.
- Cung cấp giao diện tương tác (CLI) lẫn API để các module khác import và sử dụng.
"""

from typing import List, Optional, Set
import sys


class RoleManager:
    """
    Quản lý các vai trò người dùng hợp lệ và trạng thái phiên đăng nhập.
    
    Quy tắc phân quyền nhà trường:
    - SinhVien: Chỉ được truy cập tài liệu công khai (Public).
    - GiangVien: Được truy cập tài liệu công khai (Public) và nội bộ (Internal).
    - QuanTri: Có toàn quyền truy cập (Public, Internal, Restricted).
    """

    # Danh sách các vai trò hợp lệ trong hệ thống
    VALID_ROLES: List[str] = ["SinhVien", "GiangVien", "QuanTri"]

    # Ánh xạ mô tả vai trò
    ROLE_DESCRIPTIONS = {
        "SinhVien": "Sinh viên (Xem quy chế, lịch thi, thông báo công khai)",
        "GiangVien": "Giảng viên (Xem tài liệu công khai và tài liệu chuyên môn, kế hoạch nội bộ)",
        "QuanTri": "Quản trị viên / Lãnh đạo (Toàn quyền tra cứu hồ sơ và hệ thống)"
    }

    def __init__(self, default_role: Optional[str] = None):
        """
        Khởi tạo RoleManager.
        :param default_role: Vai trò mặc định nếu được chỉ định trước (tùy chọn)
        """
        self._current_role: Optional[str] = None
        if default_role:
            self.set_role(default_role)

    @classmethod
    def get_valid_roles(cls) -> List[str]:
        """Trả về danh sách các vai trò hợp lệ."""
        return cls.VALID_ROLES.copy()

    @classmethod
    def is_valid_role(cls, role: str) -> bool:
        """
        Kiểm tra tính hợp lệ của vai trò.
        Không phân biệt hoa thường khi kiểm tra chuỗi đầu vào.
        """
        if not role:
            return False
        role_cleaned = role.strip().lower()
        return any(valid.lower() == role_cleaned for valid in cls.VALID_ROLES)

    @classmethod
    def normalize_role(cls, role: str) -> Optional[str]:
        """Chuẩn hóa tên vai trò về định dạng chuẩn (ví dụ: 'sinhvien' -> 'SinhVien')."""
        if not role:
            return None
        role_cleaned = role.strip().lower()
        for valid in cls.VALID_ROLES:
            if valid.lower() == role_cleaned:
                return valid
        return None

    def set_role(self, role: str) -> bool:
        """
        Gán vai trò hiện tại cho phiên làm việc.
        :param role: Tên vai trò (hoặc số thứ tự tương ứng khi chọn menu)
        :return: True nếu gán thành công, False nếu vai trò không hợp lệ.
        """
        # Hỗ trợ nhập số thứ tự 1, 2, 3
        if str(role).strip() in ["1", "2", "3"]:
            idx = int(str(role).strip()) - 1
            self._current_role = self.VALID_ROLES[idx]
            return True

        normalized = self.normalize_role(role)
        if normalized:
            self._current_role = normalized
            return True
        return False

    def get_current_role(self) -> Optional[str]:
        """
        Lưu trữ và trả về vai trò hiện tại cho các module khác (như DocumentFilter / RAG retriever).
        """
        return self._current_role

    def clear_role(self) -> None:
        """Đăng xuất / xóa vai trò hiện tại."""
        self._current_role = None

    def display_roles_menu(self) -> None:
        """Hiển thị menu danh sách vai trò cho người dùng lựa chọn trên CLI."""
        print("=" * 60)
        print("   HỆ THỐNG TRỢ LÝ AI NHÀ TRƯỜNG - XÁC THỰC VAI TRÒ (RBAC)")
        print("=" * 60)
        print("Vui lòng chọn vai trò làm việc của bạn:")
        for idx, role in enumerate(self.VALID_ROLES, start=1):
            desc = self.ROLE_DESCRIPTIONS.get(role, "")
            print(f"  [{idx}] {role.ljust(12)} : {desc}")
        print("=" * 60)

    def prompt_select_role(self) -> str:
        """
        Hiển thị giao diện tương tác cho phép người dùng nhập và chọn vai trò,
        tự động kiểm tra tính hợp lệ cho đến khi người dùng nhập đúng.
        """
        self.display_roles_menu()
        while True:
            try:
                user_input = input("Nhập số thứ tự [1-3] hoặc tên vai trò: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nHủy thao tác xác thực.")
                sys.exit(0)

            if self.set_role(user_input):
                print(f"[XÁC THỰC THÀNH CÔNG] Vai trò hiện tại của bạn: >> {self._current_role} <<")
                print("Mọi truy vấn tài liệu sẽ được áp dụng quyền tương ứng.\n")
                return self._current_role
            else:
                print(f"[LỖI] Lựa chọn '{user_input}' không hợp lệ! Vui lòng chọn lại (1, 2, 3 hoặc SinhVien, GiangVien, QuanTri).")

    def can_access_classification(self, classification: str) -> bool:
        """
        Hàm tiện ích kiểm tra nhanh xem vai trò hiện tại có được phép truy cập
        mức phân loại (Public, Internal, Restricted) hay không.
        """
        if not self._current_role:
            return False
            
        cls = classification.strip().capitalize()
        if cls == "Public":
            return True
        elif cls == "Internal":
            return self._current_role in ["GiangVien", "QuanTri"]
        elif cls == "Restricted":
            return self._current_role == "QuanTri"
        return False


# Singleton instance tiện dụng để các module khác có thể import dùng chung nếu cần
current_role_manager = RoleManager()


if __name__ == "__main__":
    # Chạy trực tiếp file để kiểm thử module xác thực
    mgr = RoleManager()
    selected_role = mgr.prompt_select_role()
    
    print("--- KIỂM TRA PHÂN QUYỀN VỚI VAI TRÒ VỪA CHỌN ---")
    for cls_level in ["Public", "Internal", "Restricted"]:
        permitted = mgr.can_access_classification(cls_level)
        status_text = "ĐƯỢC PHÉP TRUY CẬP" if permitted else "BỊ TỪ CHỐI (CẤM)"
        print(f"  - Mức [{cls_level.ljust(10)}]: {status_text}")

