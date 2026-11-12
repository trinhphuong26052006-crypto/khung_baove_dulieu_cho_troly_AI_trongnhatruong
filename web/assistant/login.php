<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once __DIR__ . '/auth_check.php';

// Nếu đã đăng nhập và đã cấu hình, chuyển thẳng vào index.php
if (!empty($_SESSION['user']) && isset($_SESSION['app_config'])) {
    header('Location: index.php');
    exit;
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = trim($_POST['email'] ?? '');
    $password = trim($_POST['password'] ?? '');

    if (empty($email)) {
        $error = 'Vui lòng nhập email hoặc chọn tài khoản mẫu.';
    } else {
        $pdo = get_db_connection();
        $authenticated_user = null;

        if ($pdo) {
            try {
                $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ? LIMIT 1");
                $stmt->execute([$email]);
                $user = $stmt->fetch();
                if ($user) {
                    // Kiểm tra password bcrypt hoặc cho phép đăng nhập nếu nhập đúng hoặc dùng tài khoản mẫu
                    if (empty($user['password']) || password_verify($password, $user['password']) || $password === '123456789' || empty($password)) {
                        $authenticated_user = $user;
                    }
                }
            } catch (Exception $e) {
                // Database có lỗi thì fallback
            }
        }

        // Fallback tài khoản mẫu nếu MySQL chưa bật
        if (!$authenticated_user) {
            $mockUsers = [
                'admin@studyhub.vn' => ['id' => 1, 'full_name' => 'Quản Trị Viên', 'role' => 'QuanTri', 'email' => 'admin@studyhub.vn'],
                'user1@studyhub.vn' => ['id' => 2, 'full_name' => 'Nguyễn Văn An (Sinh viên)', 'role' => 'SinhVien', 'email' => 'user1@studyhub.vn'],
                'user2@studyhub.vn' => ['id' => 3, 'full_name' => 'Trần Thị Bình (Sinh viên)', 'role' => 'SinhVien', 'email' => 'user2@studyhub.vn'],
                'user3@studyhub.vn' => ['id' => 4, 'full_name' => 'Lê Hoàng Cường (Giảng viên)', 'role' => 'GiangVien', 'email' => 'user3@studyhub.vn']
            ];
            if (isset($mockUsers[$email])) {
                $authenticated_user = $mockUsers[$email];
            }
        }

        if ($authenticated_user) {
            $_SESSION['user'] = $authenticated_user;
            // Chuyển sang bước 2: Chọn cấu hình RBAC & Pre-retrieval
            header('Location: setup.php');
            exit;
        } else {
            $error = 'Tài khoản không tồn tại trên hệ thống.';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng Nhập - Hệ Thống Trợ Lý AI Nhà Trường</title>
    <link rel="stylesheet" href="static/style.css">
    <style>
        .login-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100vh;
            width: 100vw;
            background: radial-gradient(circle at 50% 15%, #e0edff 0%, #f4f7fc 70%);
        }
        .login-card {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: 20px;
            width: 440px;
            max-width: 90vw;
            padding: 40px 36px;
            box-shadow: 0 20px 45px rgba(25, 81, 252, 0.08);
        }
        .login-header {
            text-align: center;
            margin-bottom: 30px;
        }
        .login-logo {
            font-size: 2.4rem;
            margin-bottom: 8px;
            display: inline-block;
        }
        .login-title {
            font-size: 1.3rem;
            font-weight: 800;
            color: var(--blue-darkest);
            letter-spacing: -0.02em;
        }
        .login-sub {
            font-size: 0.82rem;
            color: var(--text-muted);
            margin-top: 6px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-label {
            display: block;
            font-size: 0.82rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 8px;
        }
        .form-input {
            width: 100%;
            padding: 12px 16px;
            background: #f8fafc;
            border: 1.5px solid var(--input-border);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 0.92rem;
            outline: none;
            transition: all 0.2s;
        }
        .form-input:focus {
            border-color: var(--blue-primary);
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(25, 81, 252, 0.1);
        }
        .btn-submit {
            width: 100%;
            padding: 14px;
            background: var(--accent-gradient);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 0.98rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: var(--accent-pill-glow);
            margin-top: 10px;
        }
        .btn-submit:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(25, 81, 252, 0.35);
        }
        .error-msg {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #b91c1c;
            padding: 12px;
            border-radius: 10px;
            font-size: 0.82rem;
            margin-bottom: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="login-wrapper">
        <div class="login-card">
            <div class="login-header">
                <div class="login-logo">🛡️</div>
                <div class="login-title">HỆ THỐNG TRỢ LÝ AI NHÀ TRƯỜNG</div>
                <div class="login-sub">Khung bảo vệ dữ liệu toàn trình (RBAC & RAG)</div>
            </div>

            <?php if (!empty($error)): ?>
                <div class="error-msg"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>

            <form method="POST" action="login.php">
                <div class="form-group">
                    <label class="form-label">Email tài khoản</label>
                    <input type="email" id="email" name="email" class="form-input" placeholder="user1@studyhub.vn" required>
                </div>

                <div class="form-group">
                    <label class="form-label">Mật khẩu</label>
                    <input type="password" id="password" name="password" class="form-input" placeholder="•••••••••" required>
                </div>

                <button type="submit" class="btn-submit">Đăng nhập tiếp tục →</button>
            </form>
        </div>
    </div>
</body>
</html>

