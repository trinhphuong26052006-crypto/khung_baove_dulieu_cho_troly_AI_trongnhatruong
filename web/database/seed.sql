-- =============================================================
-- AI_ASSISTANTB — DỮ LIỆU MẪU (SEED)
-- File: database/seed.sql
-- Mật khẩu chuẩn Bcrypt cho các tài khoản mẫu: 123456789
-- =============================================================

USE AI_ASSISTANT;

-- 1. Tài khoản người dùng mẫu
INSERT INTO users (id, full_name, email, password, role, status) VALUES
(1, 'Quản Trị Viên', 'admin@aiassistant.vn', '/.fduOJNdK5EB/AbfiNwF0fp7zjEzzUZ6DdC', 'QuanTri', 'active'),
(2, 'Nguyễn Văn An', 'user1@aiassistant.vn', '/.fduOJNdK5EB/AbfiNwF0fp7zjEzzUZ6DdC', 'SinhVien', 'active'),
(3, 'Trần Thị Bình', 'user2@aiassistant.vn', '/.fduOJNdK5EB/AbfiNwF0fp7zjEzzUZ6DdC', 'SinhVien', 'active'),
(4, 'Lê Hoàng Cường', 'user3@aiassistant.vn', '/.fduOJNdK5EB/AbfiNwF0fp7zjEzzUZ6DdC', 'GiangVien', 'active')
ON DUPLICATE KEY UPDATE 
    password = VALUES(password), 
    role = VALUES(role), 
    status = VALUES(status);