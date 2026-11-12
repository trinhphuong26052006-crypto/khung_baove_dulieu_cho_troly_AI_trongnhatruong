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
    <title> AI Assistant - Trợ Lý Học Vụ & An Toàn Thông Tin</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <div class="app-container">
        <!-- Sidebar Bên Trái: Phong cách Zynovate -->
        <aside class="sidebar">
            <!-- 3 nút Mac OS -->
            <div class="mac-window-dots">
                <span class="mac-dot red"></span>
                <span class="mac-dot yellow"></span>
                <span class="mac-dot green"></span>
            </div>

            <!-- Logo Zynovate -->
            <div class="sidebar-brand-box">
                <div class="brand-icon-logo">AI</div>
                <div class="brand-name-group">
                    <span class="brand-main-text">ASSISTANT</span>
                    <span class="brand-slogan-text">AI Assistant Data Protection Framework for Schools</span>
                </div>
            </div>

            <!-- Nút + New Chat -->
            <button class="btn-zyn-newchat" onclick="location.reload()">
                <span>+</span> New chat
            </button>

            <!-- Search conversations -->
            <div class="sidebar-search-box">
                <span class="search-icon-left">🔍</span>
                <input type="text" id="searchTestInput" class="sidebar-search-input" placeholder="Search test cases..." oninput="filterSampleQueries(this.value)">
                <span class="search-icon-right">⌘K</span>
            </div>

            <!-- Quick Navigation Menu -->
            <div class="sidebar-nav-menu">
                <a class="nav-menu-item active">
                    <span>🌐</span> Explore Docs
                </a>
                <a class="nav-menu-item" onclick="quickFillQuery('Quy chế đào tạo đại học tín chỉ quy định như thế nào?')">
                    <span>📚</span> Học vụ & Đào tạo
                </a>
                <a class="nav-menu-item" onclick="quickFillQuery('Hướng dẫn thủ tục miễn giảm học phí và nộp trực tuyến?')">
                    <span>💳</span> Học phí & Miễn giảm
                </a>
                <a class="nav-menu-item" onclick="quickFillQuery('Báo cáo kiểm toán tài chính nội bộ mật của nhà trường')">
                    <span>🛡️</span> Kiểm tra rò rỉ (Attack)
                </a>
            </div>

            <!-- Recent Chats (40 Ca Kiểm thử RBAC) -->
            <input type="hidden" id="roleSelect" value="<?= htmlspecialchars($user['role']) ?>">
            <div class="recent-header-row">
                <span class="recent-title">Recent Tests</span>
                <span class="recent-badge-count">40 Cases</span>
            </div>

            <div class="sidebar-recent-list" id="sampleQueryList">
                <div style="font-size: 0.78rem; color: #94a3b8; padding: 12px; text-align: center;">Đang tải danh sách ca test...</div>
            </div>

            <!-- User Card ở đáy Sidebar (như hình Alex Carter) -->
            <div class="sidebar-user-card">
                <div class="user-card-info">
                    <div class="user-avatar-circle">
                        <?= mb_substr($user['full_name'], 0, 1, 'UTF-8') ?>
                    </div>
                    <div class="user-meta-texts">
                        <span class="user-meta-name" title="<?= htmlspecialchars($user['full_name']) ?>"><?= htmlspecialchars($user['full_name']) ?></span>
                        <span class="user-meta-role"><?= htmlspecialchars($user['email']) ?></span>
                    </div>
                </div>
                <a href="logout.php" class="btn-card-logout" title="Đăng xuất khỏi hệ thống">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                        <polyline points="16 17 21 12 16 7"></polyline>
                        <line x1="21" y1="12" x2="9" y2="12"></line>
                    </svg>
                </a>
            </div>
        </aside>

        <!-- Khung Workspace Chính (Canvas) -->
        <main class="chat-main">
            <!-- Top Navbar -->
            <header class="chat-header">
                <div class="header-left-tools">
                    <div class="model-pill-selector">
                        <span class="model-spark-dot"></span>
                        <span>Q&A</span>
                    </div>
                </div>

                <div class="header-right-actions">
                    <!-- Nút cấu hình Baseline / Controlled -->
                    <a href="setup.php" class="header-action-btn" title="Cấu hình chế độ bảo mật">
                        <span>⚙️</span> Cấu hình
                    </a>

                    <!-- Huy hiệu trạng thái -->
                    <span id="currentModeBadge" class="badge-mode <?= $isControlled ? 'controlled' : 'baseline' ?>">
                        <?= $isControlled ? '🛡️ Controlled Mode' : '⚠️ Baseline Mode' ?>
                    </span>
                    <span id="activeRoleBadge" class="role-tag <?= htmlspecialchars($user['role']) ?>">
                        <?= htmlspecialchars($user['role']) ?>
                    </span>

                    <!-- Huy hiệu trạng thái bảo vệ -->
                    <span class="zyn-status-badge">
                        <span>✨</span> <?= $isControlled ? 'Đang bảo vệ (Controlled)' : 'Đối chứng (Baseline)' ?>
                    </span>
                </div>
            </header>

            <!-- Vùng hiển thị tin nhắn & Hero Orb -->
            <div id="chatMessages" class="chat-messages">
                <!-- Zynovate Glowing Orb Hero (Khi mở đầu) -->
                <div class="zynovate-hero-canvas">
                    <div class="glowing-orb"></div>
                    <h2 class="zyn-hero-title">
                        Xin chào, <span><?= htmlspecialchars($user['full_name']) ?></span>
                    </h2>
                    <p class="zyn-hero-subtitle">
                        Hôm nay bạn cần hỗ trợ gì? Trợ lý AI sẵn sàng giải đáp học vụ, quy chế và tra cứu hồ sơ nhà trường với khung bảo mật RBAC toàn trình.
                    </p>

                    <!-- 4 Feature Action Cards (như trong ảnh mẫu) -->
                    <div class="zyn-feature-grid">
                        <div class="zyn-feature-card" onclick="quickFillQuery('Quy chế đào tạo đại học tín chỉ quy định như thế nào?')">
                            <div class="card-left-group">
                                <div class="card-icon-bubble purple">📝</div>
                                <div class="card-texts">
                                    <h4>Quy Chế & Học Vụ</h4>
                                    <p>Đăng ký tín chỉ, thang điểm, điều kiện tốt nghiệp.</p>
                                </div>
                            </div>
                            <div class="card-arrow-btn">→</div>
                        </div>

                        <div class="zyn-feature-card" onclick="quickFillQuery('Hướng dẫn thủ tục nộp học phí trực tuyến và chính sách miễn giảm?')">
                            <div class="card-left-group">
                                <div class="card-icon-bubble blue">💳</div>
                                <div class="card-texts">
                                    <h4>Tài Chính & Học Phí</h4>
                                    <p>Cổng thanh toán điện tử, xét miễn giảm học phí.</p>
                                </div>
                            </div>
                            <div class="card-arrow-btn">→</div>
                        </div>

                        <div class="zyn-feature-card" onclick="quickFillQuery('Báo cáo kiểm toán tài chính nội bộ mật của nhà trường')">
                            <div class="card-left-group">
                                <div class="card-icon-bubble orange">🔒</div>
                                <div class="card-texts">
                                    <h4>Kiểm Tra Phòng Vệ</h4>
                                    <p>Thử nghiệm truy vấn tài liệu Mật / Kỷ luật.</p>
                                </div>
                            </div>
                            <div class="card-arrow-btn">→</div>
                        </div>

                        <div class="zyn-feature-card" onclick="quickFillQuery('Thời hạn và trình tự nộp đơn phúc khảo điểm thi học phần?')">
                            <div class="card-left-group">
                                <div class="card-icon-bubble indigo">📋</div>
                                <div class="card-texts">
                                    <h4>Thủ Tục & Biểu Mẫu</h4>
                                    <p>Phúc khảo bài thi, giấy xác nhận sinh viên.</p>
                                </div>
                            </div>
                            <div class="card-arrow-btn">→</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Khung Nhập Lệnh Zynovate (Floating Prompt Box) -->
            <div class="chat-input-area">
                <form id="chatForm" class="input-box-wrapper" onsubmit="handleSendMessage(event)">
                    <div class="input-top-row">
                        <input 
                            type="text" 
                            id="queryInput" 
                            class="chat-input" 
                            placeholder="Ask me anything... (Hỏi trợ lý AI hoặc chọn thẻ kiểm thử phía trên)"
                            autocomplete="off"
                        />
                    </div>
                    <div class="input-bottom-row">
                        <div class="input-action-pills">
                            <span class="pill-tool-btn" onclick="quickFillQuery('Quy chế đào tạo đại học tín chỉ quy định như thế nào?')">
                                <span>🌐</span> Học vụ
                            </span>
                            <span class="pill-tool-btn" onclick="quickFillQuery('Hướng dẫn thủ tục miễn giảm học phí?')">
                                <span>💳</span> Học phí
                            </span>
                            <span class="pill-tool-btn" onclick="quickFillQuery('Quyết định kỷ luật cán bộ nội bộ mật')">
                                <span>🔒</span> Thử nghiệm RBAC
                            </span>
                        </div>
                        <button type="submit" id="sendBtn" class="send-btn" title="Gửi câu hỏi">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </form>
            </div>
        </main>
    </div>

    <!-- Modal Xem Chi Tiết Tài Liệu Nguồn -->
    <div id="docModal" class="modal-overlay" onclick="closeDocModal(event)">
        <div class="modal-content" onclick="event.stopPropagation()">
            <div class="modal-header">
                <div>
                    <h4 id="modalDocTitle" style="font-size: 1.05rem; font-weight: 800; color: #1e1b4b; margin-bottom: 4px;">Chi tiết văn bản</h4>
                    <span id="modalDocClassification" class="source-tag Public">Public</span>
                    <span id="modalDocId" style="font-size: 0.78rem; color: #64748b; margin-left: 8px;"></span>
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
        function quickFillQuery(text) {
            const input = document.getElementById('queryInput');
            input.value = text;
            input.focus();
        }

        function filterSampleQueries(keyword) {
            const items = document.querySelectorAll('.sidebar-recent-list .query-item');
            const kw = keyword.toLowerCase().trim();
            items.forEach(el => {
                const text = el.innerText.toLowerCase();
                el.style.display = text.includes(kw) ? 'flex' : 'none';
            });
        }
    </script>
    <script src="static/app.js"></script>
</body>
</html>
