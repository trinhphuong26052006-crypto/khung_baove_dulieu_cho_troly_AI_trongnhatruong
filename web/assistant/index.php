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
    <title>Trợ Lý AI Nhà Trường - ATTT RAG</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/style.css">
    <style>
        /* Font Family toàn cục */
        body, input, button, select, textarea {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        }

        /* Tinh chỉnh Navbar Header */
        .chat-header {
            height: 70px;
            padding: 0 32px;
            background: #ffffff;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }

        .chat-header-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .chat-header-title {
            font-size: 1.05rem;
            font-weight: 800;
            color: #03195b;
            letter-spacing: -0.02em;
        }

        .header-badges {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .btn-change-mode {
            font-size: 0.72rem;
            font-weight: 700;
            color: #1951fc;
            background: #eff6ff;
            border: 1px solid #bfdbfe;
            padding: 4px 10px;
            border-radius: 8px;
            text-decoration: none;
            transition: all 0.2s;
        }

        .btn-change-mode:hover {
            background: #1951fc;
            color: #ffffff;
        }

        /* Sidebar hiện đại hơn */
        .sidebar {
            width: 320px;
            background: #ffffff;
            border-right: 1px solid #e2e8f0;
        }

        .sidebar-header {
            height: 70px;
            padding: 0 24px;
            display: flex;
            align-items: center;
            border-bottom: 1px solid #e2e8f0;
        }

        .sidebar-brand-name {
            font-size: 1.15rem;
            font-weight: 800;
            color: #03195b;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .sidebar-content {
            padding: 20px;
        }

        .sidebar-section-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .sidebar-section-title {
            font-size: 0.75rem;
            font-weight: 800;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin: 0;
        }

        .test-cases-count {
            background: #f1f5f9;
            color: #475569;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 12px;
        }

        /* Zyricon Floating Input Box */
        .chat-input-area {
            padding: 16px 36px 24px;
            background: transparent;
        }

        .input-box-wrapper {
            background: #ffffff;
            border: 1.5px solid #cbd5e1;
            border-radius: 20px;
            padding: 8px 12px 8px 24px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.25s ease;
        }

        .input-box-wrapper:focus-within {
            border-color: #1951fc;
            box-shadow: 0 12px 35px rgba(25, 81, 252, 0.15);
        }

        .input-sparkle-icon {
            font-size: 1.2rem;
            color: #1951fc;
        }

        .chat-input {
            flex: 1;
            border: none;
            outline: none;
            font-size: 0.95rem;
            font-weight: 500;
            color: #1e293b;
            background: transparent;
            padding: 8px 0;
        }

        .chat-input::placeholder {
            color: #94a3b8;
        }

        .send-btn {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            background: linear-gradient(135deg, #1951fc 0%, #3781fc 100%);
            border: none;
            color: #ffffff;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 14px rgba(25, 81, 252, 0.3);
            transition: all 0.2s ease;
        }

        .send-btn:hover {
            transform: scale(1.06);
            box-shadow: 0 6px 18px rgba(25, 81, 252, 0.45);
        }

        .send-btn:disabled {
            background: #cbd5e1;
            box-shadow: none;
            cursor: not-allowed;
            transform: none;
        }
    </style>
</head>
<body>
    <div class="app-container">
        <!-- Sidebar Bên Trái: Danh Sách 40 Ca Test -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <div class="sidebar-brand-name">
                    <span>🛡️</span> ATTT ASSISTANT
                </div>
            </div>

            <div class="sidebar-content">
                <input type="hidden" id="roleSelect" value="<?= htmlspecialchars($user['role']) ?>">

                <div class="sidebar-section-header">
                    <span class="sidebar-section-title">BỘ KIỂM THỬ THỰC NGHIỆM</span>
                    <span class="test-cases-count">40 CA TEST</span>
                </div>

                <div id="sampleQueryList">
                    <div style="font-size: 0.78rem; color: #94a3b8; padding: 12px; text-align: center;">Đang nạp dữ liệu kiểm thử...</div>
                </div>
            </div>
        </aside>

        <!-- Vùng Chat Chính (Khung Hội Thoại) -->
        <main class="chat-main">
            <!-- Header phía trên -->
            <header class="chat-header">
                <div class="chat-header-left">
                    <span class="chat-header-title">Hội Thoại Trợ Lý AI Học Vụ & Bảo Mật</span>
                    <a href="setup.php" class="btn-change-mode" title="Nhấn để đổi chế độ">⚙️ Đổi Chế Độ</a>
                </div>

                <div class="header-badges">
                    <span id="currentModeBadge" class="badge-mode <?= $isControlled ? 'controlled' : 'baseline' ?>">
                        <?= $isControlled ? '🛡️ Controlled (Có bảo vệ)' : '⚠️ Baseline (Không bảo vệ)' ?>
                    </span>
                    <span id="activeRoleBadge" class="role-tag <?= htmlspecialchars($user['role']) ?>"><?= htmlspecialchars($user['role']) ?></span>

                    <!-- Profile & Nút Đăng Xuất -->
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
                            <strong style="color: #03195b; font-weight: 800;">Trợ Lý AI Nhà Trường</strong>
                            <span class="status-pill PASSED">READY</span>
                        </div>
                        <div>
                            Xin chào <strong><?= htmlspecialchars($user['full_name']) ?></strong>! Bạn đang đăng nhập với vai trò <strong class="role-tag <?= htmlspecialchars($user['role']) ?>"><?= htmlspecialchars($user['role']) ?></strong>.
                            <br><br>
                            Hệ thống đang hoạt động ở chế độ <strong style="color: #1951fc;"><?= $isControlled ? 'Controlled (Kích hoạt đầy đủ RBAC Pre-retrieval & Output Guardrails)' : 'Baseline (Tắt tiền lọc phân quyền để đo lường rò rỉ)' ?></strong>.
                            <br><br>
                            <div style="background: #f0f7ff; border: 1px solid #bfdbfe; padding: 14px 18px; border-radius: 12px; margin-top: 10px; font-size: 0.88rem; color: #03195b; line-height: 1.6;">
                                💡 <strong>Gợi ý thao tác:</strong> Nhập câu hỏi tự nhiên về quy chế, học phí, biểu mẫu vào khung chat bên dưới hoặc click chọn nhanh các ca kiểm thử (Normal & Attack) ở danh sách bên trái để kiểm tra phản ứng của hệ thống an toàn thông tin.
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Khung nhập câu hỏi bên dưới (Zyricon Floating Style) -->
            <div class="chat-input-area">
                <form id="chatForm" class="input-box-wrapper" onsubmit="handleSendMessage(event)">
                    <span class="input-sparkle-icon">✨</span>
                    <input 
                        type="text" 
                        id="queryInput" 
                        class="chat-input" 
                        placeholder="Hỏi trợ lý AI về quy chế, học vụ, học phí (hoặc chọn ca test bên trái)..."
                        autocomplete="off"
                    />
                    <button type="submit" id="sendBtn" class="send-btn" title="Gửi câu hỏi">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
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
                    <h4 id="modalDocTitle" style="font-size: 1rem; font-weight: 800; color: #03195b; margin-bottom: 4px;">Chi tiết văn bản</h4>
                    <span id="modalDocClassification" class="source-tag Public">Public</span>
                    <span id="modalDocId" style="font-size: 0.78rem; color: var(--text-muted); margin-left: 8px;"></span>
                </div>
                <button class="close-btn" onclick="closeDocModal()">&times;</button>
            </div>
            <div id="modalDocBody" class="modal-body">
                Đang tải nội dung văn bản...
            </div>
        </div>
    </div>

    <script>
        window.API_BASE = 'api.php';
    </script>
    <script src="static/app.js"></script>
</body>
</html>
