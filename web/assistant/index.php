<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
require_once __DIR__ . '/auth_check.php';

// Kiểm tra phiên đăng nhập và cấu hình
check_auth();

$user = $_SESSION['user'];
$config = $_SESSION['app_config'];
$isControlled = ($config['mode'] === 'controlled');
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hệ Thống Trợ Lý AI Nhà Trường - ATTT RAG</title>
    <link rel="stylesheet" href="static/style.css">
    <style>
        .navbar-user-box {
            display: flex;
            align-items: center;
            gap: 12px;
            padding-left: 12px;
            border-left: 1px solid var(--card-border);
            margin-left: 8px;
        }
        .navbar-user-info {
            display: flex;
            flex-direction: column;
            text-align: right;
        }
        .navbar-user-name {
            font-size: 0.82rem;
            font-weight: 600;
            color: #f3f4f6;
            line-height: 1.2;
        }
        .navbar-user-email {
            font-size: 0.7rem;
            color: var(--text-muted);
        }
        .btn-navbar-logout {
            color: #fca5a5;
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.4);
            text-decoration: none;
            font-size: 0.75rem;
            font-weight: 600;
            padding: 5px 12px;
            border-radius: 6px;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            gap: 4px;
        }
        .btn-navbar-logout:hover {
            background: #ef4444;
            color: white;
            border-color: #ef4444;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar Bên Trái: Cấu hình Role & Danh mục -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <div>
                    <div class="brand-title">
                        <span>🛡️</span> ATTT AI ASSISTANT
                    </div>
                    <div class="brand-subtitle">Khung bảo vệ dữ liệu toàn trình (XAMPP)</div>
                </div>
            </div>

            <div class="sidebar-content">
                <!-- Vai trò người dùng (Lấy trực tiếp từ tài khoản đăng nhập) -->
                <input type="hidden" id="roleSelect" value="<?= htmlspecialchars($user['role']) ?>">

                <!-- Câu hỏi mẫu chuẩn hóa (40 Ca Kiểm thử - Nhiệm vụ Phương) -->
                <div>
                    <div class="sidebar-section-title" style="margin-top: 4px;">CÂU HỎI MẪU (TEST CASES)</div>
                    <div id="sampleQueryList">
                        <div style="font-size: 0.75rem; color: var(--text-muted); padding: 8px;">Đang tải 40 ca test...</div>
                    </div>
                </div>
            </div>
        </aside>

        <!-- Vùng Chat Chính -->
        <main class="chat-main">
            <!-- Header phía trên -->
            <header class="chat-header">
                <div class="chat-header-title">
                    <span>💬 HỘI THOẠI HỎI ĐÁP HỌC VỤ & BẢO MẬT</span>
                </div>
                <div class="header-badges">
                    <span id="currentModeBadge" class="badge-mode <?= $isControlled ? 'controlled' : 'baseline' ?>">
                        <?= $isControlled ? '🛡️ Controlled Mode' : '⚠️ Baseline Mode' ?>
                    </span>
                    <span id="activeRoleBadge" class="role-tag <?= htmlspecialchars($user['role']) ?>"><?= htmlspecialchars($user['role']) ?></span>

                    <!-- Thông tin người dùng đăng nhập & Nút Đăng xuất trên Navbar -->
                    <div class="navbar-user-box">
                        <div class="navbar-user-info">
                            <span class="navbar-user-name"><?= htmlspecialchars($user['full_name']) ?></span>
                            <span class="navbar-user-email"><?= htmlspecialchars($user['email']) ?></span>
                        </div>
                        <a href="logout.php" class="btn-navbar-logout" title="Đăng xuất khỏi hệ thống">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                                <polyline points="16 17 21 12 16 7"></polyline>
                                <line x1="21" y1="12" x2="9" y2="12"></line>
                            </svg>
                            Đăng xuất
                        </a>
                    </div>
                </div>
            </header>

            <!-- Lịch sử tin nhắn -->
            <div id="chatMessages" class="chat-messages">
                <div class="ai-message-container">
                    <div class="ai-avatar">AI</div>
                    <div class="ai-bubble">
                        <div class="ai-meta-header">
                            <strong>Trợ lý Trí tuệ Nhân tạo Nhà trường</strong>
                            <span class="status-pill PASSED">READY</span>
                        </div>
                        <div>
                            Xin chào <strong><?= htmlspecialchars($user['full_name']) ?></strong>! Bạn đang đăng nhập với vai trò <strong class="role-tag <?= htmlspecialchars($user['role']) ?>"><?= htmlspecialchars($user['role']) ?></strong>.
                            <br><br>
                            Hệ thống đang hoạt động ở chế độ <strong><?= $isControlled ? 'Controlled (Kích hoạt đầy đủ RBAC & Guardrails)' : 'Baseline (Tắt kiểm soát phân quyền)' ?></strong>.
                            <br><br>
                            Bạn có thể nhập câu hỏi tự do hoặc click vào các câu hỏi mẫu (Normal & Attack) ở menu bên trái để kiểm nghiệm cơ chế phân quyền bảo vệ dữ liệu.
                        </div>
                    </div>
                </div>
            </div>

            <!-- Khung nhập câu hỏi bên dưới -->
            <div class="chat-input-area">
                <form id="chatForm" class="input-box-wrapper" onsubmit="handleSendMessage(event)">
                    <input 
                        type="text" 
                        id="queryInput" 
                        class="chat-input" 
                        placeholder="Nhập câu hỏi của bạn (hoặc chọn câu hỏi mẫu bên trái)..."
                        autocomplete="off"
                    />
                    <button type="submit" id="sendBtn" class="send-btn" title="Gửi câu hỏi">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="22" y1="2" x2="11" y2="13"></line>
                            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                        </svg>
                    </button>
                </form>
            </div>
        </main>
    </div>

    <!-- Modal Xem Chi Tiết Tài Liệu Nguồn -->
    <div id="docModal" class="modal-overlay" onclick="closeDocModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div>
                    <h4 id="modalDocTitle" style="font-size: 0.95rem; margin-bottom: 4px;">Chi tiết văn bản</h4>
                    <span id="modalDocClassification" class="source-tag Public">Public</span>
                    <span id="modalDocId" style="font-size: 0.75rem; color: var(--text-muted); margin-left: 8px;"></span>
                </div>
                <button class="close-btn" onclick="closeDocModal()">&times;</button>
            </div>
            <div id="modalDocBody" class="modal-body">
                Đang tải nội dung văn bản...
            </div>
        </div>
    </div>

    <script>
        // Cấu hình URL endpoint cho môi trường XAMPP PHP
        window.API_BASE = 'api.php';
    </script>
    <script src="static/app.js"></script>
</body>
</html>
