<?php
session_start();
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
        .user-profile-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: #15161b;
            padding: 8px 12px;
            border-radius: 8px;
            border: 1px solid var(--card-border);
            margin-bottom: 14px;
        }
        .user-name {
            font-size: 0.8rem;
            font-weight: 600;
            color: #f3f4f6;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 130px;
        }
        .btn-logout {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.7rem;
            padding: 2px 6px;
            border-radius: 4px;
            transition: 0.2s;
        }
        .btn-logout:hover {
            color: #ef4444;
            background: rgba(239, 68, 68, 0.1);
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
                <!-- Thông tin người dùng đang đăng nhập -->
                <div class="user-profile-header">
                    <div>
                        <div class="user-name" title="<?= htmlspecialchars($user['full_name']) ?>"><?= htmlspecialchars($user['full_name']) ?></div>
                        <div style="font-size: 0.68rem; color: var(--text-muted);"><?= htmlspecialchars($user['email']) ?></div>
                    </div>
                    <a href="logout.php" class="btn-logout" title="Đăng xuất">Thoát</a>
                </div>

                <!-- Chọn vai trò mô phỏng (Nhiệm vụ Thảo) -->
                <div class="role-select-box">
                    <div class="sidebar-section-title">VAI TRÒ MÔ PHỎNG (RBAC)</div>
                    <select id="roleSelect" class="role-select">
                        <option value="SinhVien" <?= $user['role'] === 'SinhVien' ? 'selected' : '' ?>>🎓 SinhVien (Sinh viên)</option>
                        <option value="GiangVien" <?= $user['role'] === 'GiangVien' ? 'selected' : '' ?>>👨‍🏫 GiangVien (Giảng viên)</option>
                        <option value="QuanTri" <?= $user['role'] === 'QuanTri' ? 'selected' : '' ?>>🔑 QuanTri (Quản trị viên)</option>
                    </select>

                    <div id="rolePermissionCard" class="role-permission-card">
                        <div style="margin-bottom: 4px; display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600;">Quyền truy cập:</span>
                            <span id="roleBadge" class="role-tag <?= htmlspecialchars($user['role']) ?>"><?= htmlspecialchars($user['role']) ?></span>
                        </div>
                        <div id="roleDescription" style="color: var(--text-muted);">
                            Chỉ xem văn bản học vụ, học phí, biểu mẫu công khai.
                        </div>
                        <div style="margin-top: 6px; font-size: 0.7rem; color: #9ca3af;">
                            Tầng dữ liệu: <strong id="roleLevels" style="color: #34d399;">Public</strong>
                        </div>
                    </div>
                </div>

                <!-- Cấu hình chế độ Baseline vs Controlled (Nhiệm vụ Thảo & Nhung) -->
                <div class="mode-switch-card">
                    <div class="sidebar-section-title" style="margin-top: 0; display: flex; justify-content: space-between; align-items: center;">
                        <span>CHẾ ĐỘ THỬ NGHIỆM</span>
                        <a href="setup.php" style="font-size: 0.68rem; color: #3b82f6; text-decoration: none;">Đổi cấu hình</a>
                    </div>
                    <div class="mode-toggle-row">
                        <span style="font-size: 0.8rem; font-weight: 500;">RBAC Pre-retrieval</span>
                        <label class="switch">
                            <input type="checkbox" id="toggleRbac" <?= $config['ENABLE_RBAC_PRERETRIEVAL'] ? 'checked' : '' ?>>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div class="mode-toggle-row">
                        <span style="font-size: 0.8rem; font-weight: 500;">Output Guardrails</span>
                        <label class="switch">
                            <input type="checkbox" id="toggleFilter" <?= $config['ENABLE_OUTPUT_FILTER'] ? 'checked' : '' ?>>
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 4px;" id="modeExplainText">
                        Chế độ: <strong style="color: <?= $isControlled ? '#60a5fa' : '#fbbf24' ?>;"><?= $isControlled ? 'Controlled (Có bảo vệ)' : 'Baseline (Không bảo vệ)' ?></strong>
                    </div>
                </div>

                <!-- Câu hỏi mẫu chuẩn hóa (40 Ca Kiểm thử - Nhiệm vụ Phương) -->
                <div>
                    <div class="sidebar-section-title">CÂU HỎI MẪU (TEST CASES)</div>
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
