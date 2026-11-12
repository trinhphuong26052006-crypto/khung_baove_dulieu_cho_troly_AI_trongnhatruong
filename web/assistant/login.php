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
            background: radial-gradient(circle at 50% 20%, #1e2029 0%, #111216 70%);
        }
        .login-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            width: 440px;
            max-width: 90vw;
            padding: 36px 32px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .login-header {
            text-align: center;
            margin-bottom: 28px;
        }
        .login-logo {
            font-size: 2.2rem;
            margin-bottom: 8px;
            display: inline-block;
        }
        .login-title {
            font-size: 1.25rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a78bfa, #38bdf8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-sub {
            font-size: 0.8rem;
            color: var(--text-muted);
            margin-top: 4px;
        }
        .form-group {
            margin-bottom: 18px;
        }
        .form-label {
            display: block;
            font-size: 0.8rem;
            font-weight: 500;
            color: var(--text-secondary);
            margin-bottom: 6px;
        }
        .form-input {
            width: 100%;
            padding: 10px 14px;
            background: var(--input-bg);
            border: 1px solid var(--card-border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 0.9rem;
            outline: none;
            transition: border-color 0.2s;
        }
        .form-input:focus {
            border-color: var(--accent-blue);
        }
        .btn-submit {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #3b82f6, #6366f1);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            margin-top: 8px;
        }
        .btn-submit:hover {
            opacity: 0.9;
        }
        .quick-accounts {
            margin-top: 24px;
            padding-top: 20px;
            border-top: 1px solid var(--card-border);
        }
        .quick-title {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-bottom: 10px;
            text-align: center;
        }
        .account-chips {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .account-chip {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            background: #15161b;
            border: 1px solid var(--card-border);
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.2s;
            font-size: 0.78rem;
        }
        .account-chip:hover {
            border-color: #4b5563;
            background: var(--input-bg);
        }
        .error-msg {
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid #ef4444;
            color: #fca5a5;
            padding: 10px;
            border-radius: 8px;
            font-size: 0.8rem;
            margin-bottom: 16px;
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
                    <label class="form-label">Mật khẩu (Mặc định: 123456789)</label>
                    <input type="password" id="password" name="password" class="form-input" placeholder="•••••••••" value="123456789">
                </div>

                <button type="submit" class="btn-submit">Đăng nhập tiếp tục →</button>
            </form>

            <div class="quick-accounts">
                <div class="quick-title">Chọn nhanh tài khoản mẫu từ Database Seed:</div>
                <div class="account-chips">
                    <div class="account-chip" onclick="fillAccount('user1@studyhub.vn')">
                        <span>🎓 Nguyễn Văn An</span>
                        <span class="role-tag SinhVien">SinhVien</span>
                    </div>
                    <div class="account-chip" onclick="fillAccount('user3@studyhub.vn')">
                        <span>👨‍🏫 Lê Hoàng Cường</span>
                        <span class="role-tag GiangVien">GiangVien</span>
                    </div>
                    <div class="account-chip" onclick="fillAccount('admin@studyhub.vn')">
                        <span>🔑 Quản Trị Viên</span>
                        <span class="role-tag QuanTri">QuanTri</span>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function fillAccount(email) {
            document.getElementById('email').value = email;
            document.getElementById('password').value = '123456789';
        }
    </script>
</body>
</html>

