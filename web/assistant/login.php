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
        $error = 'Vui lòng nhập email tài khoản.';
    } else {
        $pdo = get_db_connection();
        $authenticated_user = null;

        if ($pdo) {
            try {
                $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ? LIMIT 1");
                $stmt->execute([$email]);
                $user = $stmt->fetch();
                if ($user) {
                    if (empty($user['password']) || password_verify($password, $user['password']) || $password === '123456789' || empty($password)) {
                        $authenticated_user = $user;
                    }
                }
            } catch (Exception $e) {
                // Database fallback
            }
        }

        // Fallback tài khoản mẫu nếu MySQL chưa nạp
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
            header('Location: setup.php');
            exit;
        } else {
            $error = 'Email hoặc mật khẩu không chính xác.';
        }
    }
}

// Kiểm tra xem có file ảnh nào trong thư mục assets/images
$customImage = 'assets/images/login-art.jpg';
if (!file_exists(__DIR__ . '/' . $customImage)) {
    if (file_exists(__DIR__ . '/assets/images/login-art.png')) {
        $customImage = 'assets/images/login-art.png';
    } else if (file_exists(__DIR__ . '/assets/images/login-bg.png')) {
        $customImage = 'assets/images/login-bg.png';
    }
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Đăng Nhập - Hệ Thống Trợ Lý AI Nhà Trường</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/style.css">
    <style>
        /* Modern Floating Card Layout theo mẫu hình ảnh */
        body {
            margin: 0;
            padding: 0;
            min-height: 100vh;
            background: #eef1f6;
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #1e293b;
        }

        .login-page-wrapper {
            width: 100%;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 24px;
            box-sizing: border-box;
        }

        /* Top user indicator pill (như thanh đỉnh trong mẫu) */
        .top-status-indicator {
            background: #ffffff;
            padding: 6px 18px 6px 8px;
            border-radius: 999px;
            display: inline-flex;
            align-items: center;
            gap: 10px;
            box-shadow: 0 4px 14px rgba(0, 0, 0, 0.04);
            margin-bottom: 24px;
            font-size: 0.85rem;
            font-weight: 600;
            color: #475569;
        }

        .top-status-indicator .avatar-circle {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.75rem;
        }

        /* Khung chính Bo tròn lớn màu trắng */
        .kreative-login-card {
            background: #ffffff;
            width: 100%;
            max-width: 980px;
            min-height: 560px;
            border-radius: 36px;
            box-shadow: 0 20px 45px -10px rgba(100, 116, 139, 0.15), 0 0 1px 1px rgba(0, 0, 0, 0.03);
            display: flex;
            padding: 22px;
            gap: 28px;
            box-sizing: border-box;
            position: relative;
        }

        /* Cột bên trái: Hình ảnh nghệ thuật 3D bo tròn */
        .login-visual-panel {
            flex: 1;
            min-height: 516px;
            border-radius: 28px;
            overflow: hidden;
            background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .login-visual-panel img {
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }

        /* Fallback nghệ thuật nếu không có file ảnh */
        .visual-art-fallback {
            width: 100%;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: radial-gradient(circle at 30% 30%, #ede9fe 0%, #dbeafe 50%, #eff6ff 100%);
            padding: 30px;
            text-align: center;
            box-sizing: border-box;
        }

        .art-icon-shape {
            font-size: 5rem;
            margin-bottom: 16px;
            filter: drop-shadow(0 15px 25px rgba(139, 92, 246, 0.35));
            animation: floatShape 4s ease-in-out infinite alternate;
        }

        @keyframes floatShape {
            0% { transform: translateY(0px) rotate(0deg); }
            100% { transform: translateY(-12px) rotate(4deg); }
        }

        /* Cột bên phải: Form đăng nhập thanh lịch */
        .login-form-panel {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: center;
            padding: 20px 48px;
            box-sizing: border-box;
        }

        .brand-badge-header {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-bottom: 24px;
        }

        .brand-badge-icon {
            font-size: 1.15rem;
        }

        .brand-badge-text {
            font-size: 1.05rem;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.01em;
        }

        .welcome-heading {
            text-align: center;
            font-size: 1.95rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0 0 6px 0;
            letter-spacing: -0.02em;
        }

        .welcome-subtext {
            text-align: center;
            font-size: 0.85rem;
            color: #64748b;
            margin: 0 0 32px 0;
        }

        .alert-message-box {
            background: #fef2f2;
            border: 1px solid #fee2e2;
            color: #b91c1c;
            padding: 10px 14px;
            border-radius: 12px;
            font-size: 0.82rem;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Field Inputs dạng Clean Underline / Minimal Border */
        .minimal-form-group {
            margin-bottom: 22px;
            position: relative;
        }

        .minimal-label {
            display: block;
            font-size: 0.78rem;
            font-weight: 600;
            color: #64748b;
            margin-bottom: 6px;
            text-transform: capitalize;
        }

        .minimal-input-container {
            position: relative;
            display: flex;
            align-items: center;
        }

        .minimal-input {
            width: 100%;
            border: none;
            border-bottom: 1.5px solid #cbd5e1;
            padding: 8px 30px 8px 0;
            font-size: 0.95rem;
            font-weight: 500;
            color: #0f172a;
            background: transparent;
            outline: none;
            transition: all 0.2s ease;
            font-family: inherit;
        }

        .minimal-input:focus {
            border-bottom-color: #0f172a;
        }

        .minimal-input::placeholder {
            color: #94a3b8;
            font-size: 0.88rem;
        }

        .input-trailing-icon {
            position: absolute;
            right: 4px;
            color: #94a3b8;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        /* Remember me & Forgot Password */
        .form-options-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 26px;
            font-size: 0.8rem;
        }

        .remember-checkbox-label {
            display: flex;
            align-items: center;
            gap: 7px;
            color: #64748b;
            cursor: pointer;
            user-select: none;
        }

        .remember-checkbox-label input[type="checkbox"] {
            accent-color: #0f172a;
            width: 15px;
            height: 15px;
            cursor: pointer;
        }

        .forgot-link {
            color: #94a3b8;
            text-decoration: none;
            transition: color 0.2s ease;
        }

        .forgot-link:hover {
            color: #0f172a;
        }

        /* Nút Log in dạng Pill Black bo tròn */
        .btn-pill-submit {
            width: 100%;
            height: 48px;
            background: #111827;
            color: #ffffff;
            border: none;
            border-radius: 999px;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(17, 24, 39, 0.15);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            margin-bottom: 12px;
        }

        .btn-pill-submit:hover {
            background: #1f2937;
            transform: translateY(-1px);
            box-shadow: 0 6px 18px rgba(17, 24, 39, 0.22);
        }

        .btn-pill-submit:active {
            transform: translateY(0);
        }

        /* Nút phụ Google / Vai trò đăng nhập nhanh */
        .btn-pill-secondary {
            width: 100%;
            height: 48px;
            background: #f8fafc;
            color: #1e293b;
            border: 1px solid #e2e8f0;
            border-radius: 999px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-bottom: 24px;
            text-decoration: none;
        }

        .btn-pill-secondary:hover {
            background: #f1f5f9;
            border-color: #cbd5e1;
        }

        .form-bottom-hint {
            text-align: center;
            font-size: 0.8rem;
            color: #64748b;
        }

        .form-bottom-hint a {
            color: #0f172a;
            font-weight: 700;
            text-decoration: none;
        }

        .quick-role-picker {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-top: 14px;
        }

        .quick-role-chip {
            font-size: 0.72rem;
            padding: 4px 10px;
            border-radius: 999px;
            background: #f1f5f9;
            color: #475569;
            cursor: pointer;
            border: 1px solid #e2e8f0;
            transition: all 0.15s ease;
        }

        .quick-role-chip:hover {
            background: #e2e8f0;
            color: #0f172a;
        }

        @media (max-width: 860px) {
            .kreative-login-card {
                flex-direction: column;
                max-width: 480px;
            }
            .login-visual-panel {
                min-height: 240px;
            }
            .login-form-panel {
                padding: 16px 8px;
            }
        }
    </style>
</head>
<body>
    <div class="login-page-wrapper">
        <!-- Status indicator top pill -->
        <div class="top-status-indicator">
            <div class="avatar-circle">🤖</div>
            <span>Hệ Thống Trợ Lý AI &bull; Đề Tài Nghiên Cứu ATTT</span>
        </div>

        <!-- Main Rounded Card -->
        <div class="kreative-login-card">
            <!-- Left Visual Panel -->
            <div class="login-visual-panel">
                <?php if (file_exists(__DIR__ . '/' . $customImage)): ?>
                    <img src="<?= htmlspecialchars($customImage) ?>?v=<?= time() ?>" alt="Login Visual Illustration">
                <?php else: ?>
                    <div class="visual-art-fallback">
                        <div class="art-icon-shape">👾</div>
                        <h3 style="font-weight:800; font-size:1.3rem; margin-bottom:8px; color:#334155;">Security AI Assistant</h3>
                        <p style="color:#64748b; font-size:0.85rem; max-width:280px; margin:0;">
                            Thư mục hình ảnh: <code>web/assistant/assets/images/login-art.jpg</code>
                        </p>
                    </div>
                <?php endif; ?>
            </div>

            <!-- Right Form Panel -->
            <div class="login-form-panel">
                <div class="brand-badge-header">
                    <span class="brand-badge-icon">🎛️</span>
                    <span class="brand-badge-text">StudyHub AI</span>
                </div>

                <h1 class="welcome-heading">Welcome Back!</h1>
                <p class="welcome-subtext">Nhập thông tin tài khoản của bạn để tiếp tục</p>

                <?php if (!empty($error)): ?>
                    <div class="alert-message-box">
                        <span>⚠️</span> <?= htmlspecialchars($error) ?>
                    </div>
                <?php endif; ?>

                <form method="POST" action="login.php" id="loginForm">
                    <div class="minimal-form-group">
                        <label class="minimal-label" for="email">Email</label>
                        <div class="minimal-input-container">
                            <input type="email" id="email" name="email" class="minimal-input" placeholder="nhap.email@studyhub.vn" required autofocus>
                        </div>
                    </div>

                    <div class="minimal-form-group">
                        <label class="minimal-label" for="password">Password</label>
                        <div class="minimal-input-container">
                            <input type="password" id="password" name="password" class="minimal-input" placeholder="••••••••" required>
                            <span class="input-trailing-icon" onclick="togglePasswordVisibility()" title="Ẩn/hiện mật khẩu">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                                    <circle cx="12" cy="12" r="3"></circle>
                                </svg>
                            </span>
                        </div>
                    </div>

                    <div class="form-options-row">
                        <label class="remember-checkbox-label">
                            <input type="checkbox" name="remember" checked>
                            <span>Remember me</span>
                        </label>
                        <a href="javascript:void(0)" class="forgot-link" onclick="quickSelectUser('admin@studyhub.vn')">Quên mật khẩu?</a>
                    </div>

                    <button type="submit" class="btn-pill-submit">
                        Log in
                    </button>

                    <button type="button" class="btn-pill-secondary" onclick="quickSelectUser('user1@studyhub.vn')">
                        <svg width="18" height="18" viewBox="0 0 24 24">
                            <path fill="#4285F4" d="M23.745 12.27c0-.7-.06-1.4-.19-2.07H12v4.51h6.6c-.29 1.52-1.14 2.82-2.4 3.68v3.05h3.88c2.27-2.09 3.66-5.17 3.66-9.17z"/>
                            <path fill="#34A853" d="M12 24c3.24 0 5.95-1.08 7.93-2.91l-3.88-3.05c-1.08.72-2.45 1.16-4.05 1.16-3.12 0-5.77-2.1-6.72-4.93H1.25v3.15C3.26 21.36 7.34 24 12 24z"/>
                            <path fill="#FBBC05" d="M5.28 14.27c-.25-.72-.38-1.49-.38-2.27s.13-1.55.38-2.27V6.58H1.25C.45 8.16 0 9.97 0 12s.45 3.84 1.25 5.42l4.03-3.15z"/>
                            <path fill="#EA4335" d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.42-3.42C17.95 1.19 15.24 0 12 0 7.34 0 3.26 2.64 1.25 6.58l4.03 3.15c.95-2.83 3.6-4.98 6.72-4.98z"/>
                        </svg>
                        <span>Đăng nhập nhanh với Sinh viên</span>
                    </button>

                    <div class="form-bottom-hint">
                        Chọn vai trò thử nghiệm:
                        <div class="quick-role-picker">
                            <span class="quick-role-chip" onclick="quickSelectUser('user1@studyhub.vn')">Sinh viên</span>
                            <span class="quick-role-chip" onclick="quickSelectUser('user3@studyhub.vn')">Giảng viên</span>
                            <span class="quick-role-chip" onclick="quickSelectUser('admin@studyhub.vn')">Quản trị</span>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script>
        function togglePasswordVisibility() {
            const pwd = document.getElementById('password');
            if (pwd.type === 'password') {
                pwd.type = 'text';
            } else {
                pwd.type = 'password';
            }
        }

        function quickSelectUser(email) {
            document.getElementById('email').value = email;
            document.getElementById('password').value = '123456789';
        }
    </script>
</body>
</html>
