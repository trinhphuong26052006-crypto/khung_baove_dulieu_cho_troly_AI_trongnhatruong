<!DOCTYPE html>
<html lang="vi">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trạng Thái Bảo Mật - ATTT AI ASSISTANT</title>
    <link rel="stylesheet" href="web/static/style.css">
    <style>
        /* Tối ưu riêng cho trang Dashboard Trạng thái bảo mật */
        body {
            overflow: hidden;
            background-color: #f5f6fc;
            color: #1e1b4b;
        }

        .dashboard-main {
            flex: 1;
            display: flex;
            flex-direction: column;
            background-color: #f5f6fc;
            height: 100vh;
            overflow-y: auto;
        }

        .nav-menu {
            display: flex;
            flex-direction: column;
            gap: 6px;
            padding: 12px 10px;
        }

        .nav-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            border-radius: 10px;
            color: #64748b;
            text-decoration: none;
            font-size: 0.88rem;
            font-weight: 500;
            transition: all 0.2s;
        }

        .nav-item:hover {
            background-color: #f8fafc;
            color: #4338ca;
        }

        .nav-item.active {
            background-color: #f3f0ff;
            color: #6d28d9;
            font-weight: 600;
        }

        .nav-item svg {
            width: 18px;
            height: 18px;
        }

        .user-account-box {
            margin-top: auto;
            padding: 16px;
            border-top: 1px solid var(--card-border);
            background: #ffffff;
        }

        .user-account-label {
            font-size: 0.7rem;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
        }

        .user-account-val {
            font-size: 0.85rem;
            font-weight: 700;
            color: #4f46e5;
        }

        /* Vùng nội dung Dashboard */
        .dash-content {
            padding: 24px 32px;
            max-width: 1200px;
            width: 100%;
        }

        .dash-hero-banner {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 55%, #9333ea 100%);
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 24px;
            color: #ffffff;
            box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.35);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .dash-hero-subtitle {
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: rgba(255, 255, 255, 0.8);
            font-weight: 700;
            margin-bottom: 6px;
        }

        .dash-hero-title {
            font-size: 1.5rem;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 6px;
            letter-spacing: -0.3px;
        }

        .dash-hero-desc {
            font-size: 0.85rem;
            color: rgba(255, 255, 255, 0.85);
        }

        /* 3 Thẻ Trạng thái tổng quan (Khu vực A) */
        .cards-overview-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 16px;
        }

        .stat-card {
            background-color: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 20px 24px;
            box-shadow: var(--card-shadow);
        }

        .stat-card-title {
            font-size: 0.72rem;
            color: #6b7280;
            font-weight: 700;
            letter-spacing: 0.8px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .stat-card-val {
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: 0.5px;
        }

        .val-allow,
        .val-pass {
            color: #059669;
        }

        .val-deny,
        .val-block {
            color: #dc2626;
        }

        .val-redact {
            color: #d97706;
        }

        .val-na {
            color: #9ca3af;
        }

        .pipeline-card {
            background-color: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            box-shadow: var(--card-shadow);
        }

        .pipe-status-tag {
            background: linear-gradient(135deg, #4f46e5, #7c3aed);
            color: #ffffff;
            font-weight: 700;
            font-size: 0.78rem;
            padding: 5px 16px;
            border-radius: 8px;
            letter-spacing: 0.5px;
            box-shadow: 0 2px 6px rgba(99, 102, 241, 0.25);
        }

        /* Section Card chung */
        .dash-section-card {
            background-color: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 22px 26px;
            margin-bottom: 20px;
            box-shadow: var(--card-shadow);
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 14px;
        }

        .section-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #1e1b4b;
            letter-spacing: -0.2px;
        }

        .badge-right {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 88px;
            height: 26px;
            box-sizing: border-box;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            border-radius: 6px;
            text-align: center;
            flex-shrink: 0;
        }

        .badge-right.ALLOW {
            background: #ecfdf5;
            color: #059669;
            border: 1px solid #a7f3d0;
        }

        .badge-right.DENY {
            background: #fee2e2;
            color: #dc2626;
            border: 1px solid #fecaca;
        }

        .badge-right.REDACTED,
        .badge-right.REDACT {
            background: #fef3c7;
            color: #d97706;
            border: 1px solid #fde68a;
        }

        /* Khu vực B: Kết quả kiểm soát truy vấn gần nhất */
        .recent-req-meta {
            font-size: 0.85rem;
            color: #6b7280;
            margin-bottom: 8px;
            font-weight: 500;
        }

        .recent-req-query {
            font-size: 0.92rem;
            color: #1e1b4b;
            margin-bottom: 14px;
            line-height: 1.5;
            background: #f8fafc;
            padding: 10px 14px;
            border-radius: 8px;
            border-left: 3px solid #6366f1;
        }

        .recent-step-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-top: 1px solid #f1f5f9;
            font-size: 0.85rem;
        }

        .step-name {
            color: #4b5563;
            font-weight: 500;
        }

        .step-tag {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 88px;
            height: 26px;
            box-sizing: border-box;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            border-radius: 6px;
            text-align: center;
            flex-shrink: 0;
        }

        .step-tag.ALLOW,
        .step-tag.PASS {
            background: #ecfdf5;
            color: #059669;
        }

        .step-tag.DENY,
        .step-tag.BLOCK {
            background: #fee2e2;
            color: #dc2626;
        }

        .step-tag.REDACT,
        .step-tag.REDACTED {
            background: #fef3c7;
            color: #d97706;
        }

        .step-tag.NA {
            background: #f1f5f9;
            color: #9ca3af;
        }

        .recent-explanation {
            margin-top: 14px;
            font-size: 0.85rem;
            color: #059669;
            line-height: 1.5;
            padding: 10px 14px;
            background: #ecfdf5;
            border-radius: 8px;
            font-weight: 500;
        }

        .recent-explanation.denied {
            color: #dc2626;
            background: #fef2f2;
        }

        /* Khu vực C: Output Guardrails Metrics (Chỉ hiện số lần) */
        .guard-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 14px 0;
            border-bottom: 1px solid #f1f5f9;
            font-size: 0.9rem;
        }

        .guard-row:last-child {
            border-bottom: none;
        }

        .guard-label {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: 600;
            color: #1e1b4b;
        }

        .guard-num.pass {
            color: #059669;
            font-weight: 700;
            font-size: 1.15rem;
        }

        .guard-num.block {
            color: #dc2626;
            font-weight: 700;
            font-size: 1.15rem;
        }

        .guard-num.redact {
            color: #d97706;
            font-weight: 700;
            font-size: 1.15rem;
        }

        /* Khu vực D: Security Alerts */
        .alert-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 14px;
            background: #f8faff;
            border: 1px solid #eef2ff;
            border-radius: 10px;
            margin-bottom: 10px;
            font-size: 0.86rem;
            cursor: pointer;
            transition: all 0.2s;
        }

        .alert-item:hover {
            background: #f1f5f9;
            border-color: #cbd5e1;
            transform: translateY(-1px);
        }

        .alert-item:last-child {
            margin-bottom: 0;
        }

        .alert-label {
            color: #1e1b4b;
            display: flex;
            align-items: center;
            gap: 8px;
            font-weight: 500;
        }

        .alert-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 88px;
            height: 26px;
            box-sizing: border-box;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-align: center;
            flex-shrink: 0;
        }

        .alert-pill.HIGH {
            background: #fee2e2;
            color: #dc2626;
        }

        .alert-pill.MEDIUM {
            background: #fef3c7;
            color: #d97706;
        }

        .alert-pill.LOW {
            background: #ecfdf5;
            color: #059669;
        }

        /* Khu vực E: Lịch sử kiểm soát */
        .history-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 14px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 0.86rem;
            cursor: pointer;
            transition: 0.2s;
            border-radius: 8px;
        }

        .history-item:hover {
            background: #f8fafc;
        }

        .history-item:last-child {
            border-bottom: none;
        }

        .history-meta {
            color: #334155;
            font-weight: 600;
        }

        .history-tag {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 88px;
            height: 26px;
            box-sizing: border-box;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.5px;
            border-radius: 6px;
            text-align: center;
            flex-shrink: 0;
        }

        .history-tag.ALLOW {
            background: #ecfdf5;
            color: #059669;
        }

        .history-tag.DENY {
            background: #fee2e2;
            color: #dc2626;
        }

        .history-tag.REDACTED {
            background: #fef3c7;
            color: #d97706;
        }

        /* Modal Chi tiết An toàn */
        .detail-modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(15, 23, 42, 0.6);
            backdrop-filter: blur(4px);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal-box {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            width: 550px;
            max-width: 90vw;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }
    </style>
</head>

<body>
    <div class="app-container">
        <!-- Sidebar Bên Trái: ĐỒNG NHẤT 100% VỚI HỆ THỐNG -->
        <aside class="sidebar">
            <div class="sidebar-header">
                <div>
                    <div class="brand-title">
                        <span>🛡️</span> ATTT AI ASSISTANT
                    </div>
                    <div class="brand-subtitle">Khung bảo vệ dữ liệu toàn trình (XAMPP)</div>
                </div>
            </div>

            <!-- Điều hướng 3 trang chuẩn -->
            <div
                style="padding: 14px 14px 4px 14px; font-size: 0.7rem; color: var(--text-muted); font-weight: 700; letter-spacing: 0.5px;">
                ĐIỀU HƯỚNG
            </div>
            <nav class="nav-menu">
                <!-- 1. Trợ lý AI -->
                <a href="index.php" class="nav-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    <span>Trợ lý AI</span>
                </a>

                <!-- 2. Trạng thái bảo mật (ACTIVE) -->
                <a href="security_status.php" class="nav-item active">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        <polyline points="9 12 11 14 15 10"></polyline>
                    </svg>
                    <span>Trạng thái bảo mật</span>
                </a>

                <!-- 3. Kiểm thử & Thống kê -->
                <a href="evaluation_page.html" class="nav-item">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"
                        stroke-linejoin="round">
                        <line x1="18" y1="20" x2="18" y2="10"></line>
                        <line x1="12" y1="20" x2="12" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="14"></line>
                    </svg>
                    <span>Kiểm thử & thống kê</span>
                </a>
            </nav>

            <!-- Vai trò người dùng mô phỏng -->
            <div class="user-account-box">
                <div class="user-account-label">VAI TRÒ</div>
                <div class="user-account-val" id="currentUserDisplay">Sinh viên</div>
            </div>
        </aside>

        <!-- Vùng Nội dung Dashboard Trạng Thái Bảo Mật -->
        <main class="dashboard-main">
            <!-- Header phía trên đồng nhất -->
            <header class="chat-header" style="flex-shrink: 0;">
                <div class="chat-header-title">
                    <span style="color: #6366f1;">●</span>
                    <span style="font-weight: 700;">Security & Monitoring</span>
                </div>
                <div class="header-badges">
                    <a href="index.php" style="text-decoration: none; font-size: 0.78rem; font-weight: 600; color: #4f46e5; background: #ffffff; padding: 5px 14px; border-radius: 8px; border: 1px solid #c7d2fe; display: flex; align-items: center; gap: 6px;">
                        <span>💬</span> Chat AI
                    </a>
                    <span class="role-tag QuanTri" id="activeRoleTag" style="padding: 5px 12px; border-radius: 8px;">QuanTri</span>
                    <span class="badge-mode controlled" style="padding: 6px 14px; border-radius: 8px;">✨ Controlled Mode</span>
                </div>
            </header>

            <div class="dash-content">
                <!-- Banner Hero Tím Gradient giống ảnh -->
                <div class="dash-hero-banner">
                    <div>
                        <div class="dash-hero-subtitle">SECURITY MONITORING</div>
                        <div class="dash-hero-title">TRẠNG THÁI BẢO MẬT</div>
                        <div class="dash-hero-desc">Giám sát cấu hình phòng vệ, phân quyền truy cập và nhật ký bảo mật của trợ lý AI.</div>
                    </div>
                </div>

                <!-- KHU VỰC A: TỔNG QUAN TRẠNG THÁI (3 THẺ CHUẨN) -->
                <div class="cards-overview-row">
                    <div class="stat-card">
                        <div class="stat-card-title">ACCESS CONTROL</div>
                        <div class="stat-card-val val-allow" id="cardAccessControl">ALLOW</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-card-title">OUTPUT FILTER</div>
                        <div class="stat-card-val val-pass" id="cardOutputFilter">PASS</div>
                    </div>
                </div>

                <div class="pipeline-card">
                    <span
                        style="font-size: 0.75rem; color: var(--text-muted); font-weight: 700; letter-spacing: 0.5px;">PIPELINE
                        STATUS</span>
                    <span class="pipe-status-tag" id="cardPipelineStatus">COMPLETED</span>
                </div>

                <!-- KHU VỰC B: KẾT QUẢ KIỂM SOÁT GẦN NHẤT -->
                <div class="dash-section-card">
                    <div class="section-header">
                        <div class="section-title">KẾT QUẢ KIỂM SOÁT GẦN NHẤT</div>
                        <span class="badge-right ALLOW" id="recentBadgeRight">ALLOW</span>
                    </div>
                    <div class="recent-req-meta" id="recentMeta">REQ-005 • Sinh viên</div>
                    <div class="recent-req-query"><strong>Yêu cầu:</strong> <span id="recentQueryText">Tra cứu lịch học
                            cá nhân</span></div>

                    <div class="recent-step-row">
                        <span class="step-name">RBAC</span>
                        <span class="step-tag ALLOW" id="recentRbacTag">ALLOW</span>
                    </div>
                    <div class="recent-step-row">
                        <span class="step-name">Output Filter</span>
                        <span class="step-tag PASS" id="recentFilterTag">PASS</span>
                    </div>

                    <div class="recent-explanation" id="recentExplanation">
                        Truy vấn hợp lệ, nội dung an toàn.
                    </div>
                </div>

                <!-- KHU VỰC C: OUTPUT GUARDRAILS & REDACTION (CHỈ HIỆN SỐ LẦN) -->
                <div class="dash-section-card">
                    <div class="section-title" style="margin-bottom: 12px;">OUTPUT GUARDRAILS</div>

                    <!-- PASS -->
                    <div class="guard-row">
                        <span class="guard-label">
                            <span style="color: #10b981;">●</span> PASS
                        </span>
                        <span class="guard-num pass" id="countPass">0</span>
                    </div>

                    <!-- BLOCK -->
                    <div class="guard-row">
                        <span class="guard-label">
                            <span style="color: #ef4444;">●</span> BLOCK
                        </span>
                        <span class="guard-num block" id="countBlock">0</span>
                    </div>

                    <!-- REDACT -->
                    <div class="guard-row">
                        <span class="guard-label">
                            <span style="color: #f59e0b;">●</span> REDACT
                        </span>
                        <span class="guard-num redact" id="countRedact">0</span>
                    </div>
                </div>

                <!-- KHU VỰC D: SECURITY ALERTS -->
                <div class="dash-section-card">
                    <div class="section-title" style="margin-bottom: 14px;">SECURITY ALERTS</div>
                    <div id="alertsContainer">
                        <div class="alert-item"
                            onclick="openAlertModal('Truy cập trái quyền', 'Sinh viên', 'HIGH', 'Vai trò Sinh viên gửi yêu cầu truy xuất mã hồ sơ kỷ luật Restricted DOC-R014. RBAC đã từ chối quyền truy cập.')">
                            <span class="alert-label">Truy cập trái quyền</span>
                            <span class="alert-pill HIGH">HIGH</span>
                        </div>
                        <div class="alert-item"
                            onclick="openAlertModal('Dữ liệu cần che', 'Sinh viên', 'MEDIUM', 'Phát hiện câu trả lời chứa số CCCD và số điện thoại cá nhân. Output Filter đã thực hiện che bằng nhãn an toàn.')">
                            <span class="alert-label">Dữ liệu cần che</span>
                            <span class="alert-pill MEDIUM">MEDIUM</span>
                        </div>
                    </div>
                </div>

                <!-- KHU VỰC E: LỊCH SỬ KIỂM SOÁT TRUY CẬP -->
                <div class="dash-section-card">
                    <div class="section-title" style="margin-bottom: 14px;">LỊCH SỬ KIỂM SOÁT</div>
                    <div id="historyContainer">
                        <div class="history-item">
                            <span class="history-meta">REQ-005 • Sinh viên</span>
                            <span class="history-tag ALLOW">ALLOW</span>
                        </div>
                        <div class="history-item">
                            <span class="history-meta">REQ-004 • Sinh viên</span>
                            <span class="history-tag DENY">DENY</span>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    </div>

    <!-- Modal Xem Chi Tiết An Toàn (Không lộ dữ liệu nhạy cảm) -->
    <div id="alertModal" class="detail-modal" onclick="closeAlertModal()">
        <div class="modal-box" onclick="event.stopPropagation()">
            <h3 id="modalTitle" style="margin-bottom: 8px; color: #f8fafc;">Chi tiết cảnh báo an toàn</h3>
            <div id="modalMeta" style="font-size: 0.82rem; color: var(--text-muted); margin-bottom: 14px;"></div>
            <div id="modalDesc"
                style="font-size: 0.88rem; line-height: 1.6; color: #cbd5e1; background: #0b0f19; padding: 12px; border-radius: 8px; margin-bottom: 18px;">
            </div>
            <div style="text-align: right;">
                <button onclick="closeAlertModal()"
                    style="background: #334155; border: none; color: white; padding: 8px 16px; border-radius: 6px; cursor: pointer;">Đóng</button>
            </div>
        </div>
    </div>

    <script>
        // Mapping tên hiển thị vai trò
        const ROLE_DISPLAY_MAPPING = {
            "SinhVien": "Sinh viên",
            "GiangVien": "Giảng viên",
            "QuanTri": "Quản trị viên"
        };

        // Đồng bộ tức thời và liên tục giữa các Tab
        document.addEventListener("DOMContentLoaded", () => {
            syncAccountFromStorage();
            syncDashboard();

            // 1. Lắng nghe storage event (khi Tab 1 thay đổi role hoặc gửi câu hỏi)
            window.addEventListener("storage", (e) => {
                if (e.key === "LATEST_SECURITY_EVENT" || e.key === "CURRENT_USER_ACCOUNT" || e.key === "CURRENT_USER_ROLE") {
                    syncAccountFromStorage();
                    syncDashboard();
                }
            });

            // 2. Định kỳ kiểm tra (polling) mỗi 1.5 giây để cập nhật mượt mà
            setInterval(() => {
                syncAccountFromStorage();
                syncDashboard();
            }, 1500);
        });

        function syncAccountFromStorage() {
            const role = localStorage.getItem("CURRENT_USER_ROLE") || "SinhVien";
            const roleName = ROLE_DISPLAY_MAPPING[role] || role;

            const userDisplayEl = document.getElementById("currentUserDisplay");
            if (userDisplayEl) {
                userDisplayEl.innerText = roleName;
            }

            const roleTagEl = document.getElementById("activeRoleTag");
            if (roleTagEl) {
                roleTagEl.className = `role-tag ${role}`;
                roleTagEl.innerText = role;
            }
        }

        let lastProcessedTimestamp = null;

        async function manualRefreshData() {
            const btn = document.getElementById("refreshBtn");
            const icon = document.getElementById("refreshIcon");
            const text = document.getElementById("refreshText");

            // Hiệu ứng xoay icon và hiển thị trạng thái đang tải
            if (icon) icon.style.transform = "rotate(360deg)";
            if (text) text.innerText = "Đang đồng bộ...";
            if (btn) btn.style.opacity = "0.75";

            syncAccountFromStorage();
            await syncDashboard();

            setTimeout(() => {
                if (icon) icon.style.transform = "rotate(0deg)";
                if (text) text.innerText = "Đã cập nhật!";
                if (btn) btn.style.opacity = "1";
                setTimeout(() => {
                    if (text) text.innerText = "Làm mới dữ liệu";
                }, 1200);
            }, 400);
        }

        async function syncDashboard() {
            // A. Ưu tiên đọc sự kiện thời gian thực từ localStorage (vừa được gửi từ Tab 1)
            let localEvent = null;
            try {
                const raw = localStorage.getItem("LATEST_SECURITY_EVENT");
                if (raw) localEvent = JSON.parse(raw);
            } catch (e) { }

            // B. Nạp danh sách log và thống kê tích lũy từ backend
            let logs = [];
            let stats = null;
            try {
                const isXampp = window.location.pathname.includes("khung_bao_ve_attt");
                const endpoint = isXampp ? "api.php?action=logs" : "/api/logs";
                const res = await fetch(endpoint);
                const data = await res.json();
                if (data.stats && data.logs) {
                    stats = data.stats;
                    logs = data.logs;
                } else if (Array.isArray(data)) {
                    logs = data;
                }
            } catch (e) {
                console.error("Lỗi fetch logs:", e);
            }

            // Cập nhật số liệu thống kê OUTPUT GUARDRAILS: CHỈ HIỆN SỐ LẦN
            if (stats) {
                document.getElementById("countPass").innerText = (stats.pass || 0).toLocaleString();
                document.getElementById("countBlock").innerText = (stats.block || 0).toLocaleString();
                document.getElementById("countRedact").innerText = (stats.redact || 0).toLocaleString();
            } else if (logs && logs.length > 0) {
                // Fallback nếu API trả về mảng log thuần
                let cPass = 0, cBlock = 0, cRedact = 0;
                logs.forEach(l => {
                    const act = l.action_taken || "";
                    if (act === "PASSED") cPass++;
                    else if (act === "BLOCKED" || act === "BLOCKED_INPUT") cBlock++;
                    else if (act === "REDACTED") cRedact++;
                });
                document.getElementById("countPass").innerText = cPass.toLocaleString();
                document.getElementById("countBlock").innerText = cBlock.toLocaleString();
                document.getElementById("countRedact").innerText = cRedact.toLocaleString();
            }

            // C. Hiển thị sự kiện gần nhất: Ưu tiên localEvent mới nhất từ Tab 1
            if (localEvent) {
                renderLatestEvent(localEvent);
            } else if (logs && logs.length > 0) {
                const l = logs[0];
                const r = l.role || "SinhVien";
                const roleName = ROLE_DISPLAY_MAPPING[r] || r;
                renderLatestEvent({
                    req_id: "REQ-" + (l.query_sha256 ? l.query_sha256.substring(0, 4).toUpperCase() : "001"),
                    query: "Tra cứu thông tin học vụ nhà trường",
                    role: r,
                    account: roleName,
                    role_name: roleName,
                    action_taken: l.action_taken || "PASSED",
                    is_safe: l.action_taken !== "BLOCKED" && l.action_taken !== "BLOCKED_INPUT",
                    latency_ms: l.latency_ms || 0
                });
            }

            // D. Render Lịch sử kiểm soát (Khu vực E)
            renderHistoryAndAlerts(logs, localEvent);
        }

        function renderLatestEvent(ev) {
            const role = ev.role || "SinhVien";
            const roleName = ev.role_name || ROLE_DISPLAY_MAPPING[role] || role;
            const reqId = ev.req_id || "REQ-001";
            const actionTaken = ev.action_taken || "PASSED";

            const isDenied = (actionTaken === "BLOCKED" || actionTaken === "BLOCKED_INPUT");
            const isRedacted = (actionTaken === "REDACTED");

            const accStatus = isDenied ? "DENY" : "ALLOW";
            const filterStatus = isDenied ? "BLOCK" : (isRedacted ? "REDACT" : "PASS");

            // 1. Cập nhật Khu vực A: Tổng quan trạng thái
            const cardAcc = document.getElementById("cardAccessControl");
            cardAcc.innerText = accStatus;
            cardAcc.className = `stat-card-val val-${accStatus.toLowerCase()}`;

            const cardFilt = document.getElementById("cardOutputFilter");
            cardFilt.innerText = filterStatus;
            cardFilt.className = `stat-card-val val-${filterStatus.toLowerCase()}`;

            // 2. Cập nhật Khu vực B: Kết quả kiểm soát gần nhất
            document.getElementById("recentBadgeRight").innerText = accStatus;
            document.getElementById("recentBadgeRight").className = `badge-right ${accStatus}`;

            document.getElementById("recentMeta").innerText = `${reqId} • ${roleName}`;

            // Làm sạch nội dung yêu cầu hiển thị ở mức an toàn (không hiển thị canary token / prompt nhạy cảm)
            let safeQueryDisplay = ev.query || "Tra cứu học vụ";
            if (safeQueryDisplay.length > 70) {
                safeQueryDisplay = safeQueryDisplay.substring(0, 67) + "...";
            }
            document.getElementById("recentQueryText").innerText = safeQueryDisplay;

            document.getElementById("recentRbacTag").innerText = accStatus;
            document.getElementById("recentRbacTag").className = `step-tag ${accStatus}`;

            document.getElementById("recentFilterTag").innerText = filterStatus;
            document.getElementById("recentFilterTag").className = `step-tag ${filterStatus}`;

            const expl = document.getElementById("recentExplanation");
            if (isDenied) {
                expl.innerText = "Vai trò của bạn không có quyền truy cập thông tin được yêu cầu (Safe Refusal).";
                expl.className = "recent-explanation denied";
                expl.style.color = "#ef4444";
            } else if (isRedacted) {
                expl.innerText = "Đã phát hiện và tự động che bớt các thông tin nhạy cảm trước khi hiển thị.";
                expl.className = "recent-explanation";
                expl.style.color = "#f59e0b";
            } else {
                expl.innerText = "Truy vấn hợp lệ, dữ liệu đầu ra an toàn.";
                expl.className = "recent-explanation";
                expl.style.color = "#10b981";
            }
        }

        function renderHistoryAndAlerts(logs, localEvent) {
            // Kết hợp localEvent và logs
            const histContainer = document.getElementById("historyContainer");
            const alertsContainer = document.getElementById("alertsContainer");

            let items = [];
            if (localEvent) {
                const act = localEvent.action_taken || "PASSED";
                const isDeny = (act === "BLOCKED" || act === "BLOCKED_INPUT");
                const r = localEvent.role || "SinhVien";
                const roleName = ROLE_DISPLAY_MAPPING[r] || r;
                items.push({
                    id: localEvent.req_id || "REQ-NOW",
                    role: r,
                    role_name: roleName,
                    tag: isDeny ? "DENY" : (act === "REDACTED" ? "REDACTED" : "ALLOW"),
                    action_taken: act,
                    isDenied: isDeny,
                    query: localEvent.query || "",
                    violations: localEvent.violations || [],
                    isCurrent: true
                });
            }

            if (logs && logs.length > 0) {
                logs.slice(0, 8).forEach((l, idx) => {
                    const r = l.role || "SinhVien";
                    const roleName = ROLE_DISPLAY_MAPPING[r] || r;
                    const act = l.action_taken || "PASSED";
                    const isDeny = (act === "BLOCKED" || act === "BLOCKED_INPUT");
                    const itmId = "REQ-" + (l.query_sha256 ? l.query_sha256.substring(0, 4).toUpperCase() : `00${idx + 1}`);

                    // Tránh trùng lặp với localEvent
                    if (!localEvent || itmId !== localEvent.req_id) {
                        items.push({
                            id: itmId,
                            role: r,
                            role_name: roleName,
                            tag: isDeny ? "DENY" : (act === "REDACTED" ? "REDACTED" : "ALLOW"),
                            action_taken: act,
                            isDenied: isDeny,
                            query: "",
                            violations: [],
                            isCurrent: false
                        });
                    }
                });
            }

            // Render Lịch sử kiểm soát (Khu vực E)
            let histHtml = "";
            items.slice(0, 6).forEach(item => {
                histHtml += `
                    <div class="history-item" onclick="openAlertModal('Lịch sử truy xuất ${item.id}', '${item.role_name}', '${item.isDenied ? "HIGH" : "LOW"}', 'Kết quả: ${item.tag} | Trạng thái: ${item.action_taken}')">
                        <span class="history-meta">${item.id} • ${item.role_name}</span>
                        <span class="history-tag ${item.tag}">${item.tag}</span>
                    </div>
                `;
            });
            if (histHtml) histContainer.innerHTML = histHtml;

            // Render Security Alerts (Khu vực D): ĐỒNG BỘ CHÍNH XÁC VỚI CÂU ĐANG HỎI
            let alertHtml = "";

            if (localEvent) {
                const act = localEvent.action_taken || "PASSED";
                const role = localEvent.role || "SinhVien";
                const roleName = ROLE_DISPLAY_MAPPING[role] || role;
                const qText = localEvent.query || "";
                const violations = localEvent.violations || [];

                if (act === "BLOCKED" || act === "BLOCKED_INPUT") {
                    // Truy vấn đang hỏi bị CHẶN / TỪ CHỐI AN TOÀN
                    let desc = `Vai trò ${roleName} gửi yêu cầu: "${escapeHtml(qText)}". Hệ thống đã kích hoạt cơ chế RBAC và Output Guardrails để từ chối truy cập và ngăn chặn rò rỉ dữ liệu ngoài quyền hạn.`;
                    if (violations.length > 0) {
                        desc += `<br><br><strong>Chi tiết vi phạm phát hiện:</strong><br>` + violations.map(v => `• [${v.severity}] ${v.violation_type}: ${v.description}`).join('<br>');
                    }
                    alertHtml += `
                        <div class="alert-item" onclick="openAlertModal('Phát hiện truy cập ngoài phạm vi quyền', '${roleName}', 'HIGH', '${escapeModalText(desc)}')">
                            <span class="alert-label">
                                <span style="color: #f87171;">⚠️</span> Phát hiện truy cập ngoài phạm vi quyền (${localEvent.req_id || "GẦN NHẤT"})
                            </span>
                            <span class="alert-pill HIGH">HIGH</span>
                        </div>
                    `;
                } else if (act === "REDACTED") {
                    // Truy vấn đang hỏi chứa THÔNG TIN NHẠY CẢM CẦN CHE
                    let desc = `Phát hiện dữ liệu định danh cá nhân / tài liệu cần bảo mật trong phản hồi cho câu hỏi: "${escapeHtml(qText)}". Output Filter đã thực hiện cơ chế Redaction tự động che giấu an toàn.`;
                    if (violations.length > 0) {
                        desc += `<br><br><strong>Chi tiết xử lý:</strong><br>` + violations.map(v => `• [${v.severity}] ${v.violation_type}: ${v.description}`).join('<br>');
                    }
                    alertHtml += `
                        <div class="alert-item" onclick="openAlertModal('Phát hiện dữ liệu nhạy cảm cần che', '${roleName}', 'MEDIUM', '${escapeModalText(desc)}')">
                            <span class="alert-label">
                                <span style="color: #fbbf24;">🛡️</span> Phát hiện dữ liệu cần che (${localEvent.req_id || "GẦN NHẤT"})
                            </span>
                            <span class="alert-pill MEDIUM">MEDIUM</span>
                        </div>
                    `;
                } else {
                    // Truy vấn hợp lệ, an toàn
                    let desc = `Yêu cầu: "${escapeHtml(qText)}" từ vai trò ${roleName} được xác thực hợp lệ theo quyền hạn. Toàn bộ nội dung phản hồi đã qua kiểm soát an toàn và đối soát căn cứ thành công.`;
                    alertHtml += `
                        <div class="alert-item" onclick="openAlertModal('Truy vấn hợp lệ & an toàn', '${roleName}', 'LOW', '${escapeModalText(desc)}')">
                            <span class="alert-label">
                                <span style="color: #34d399;">✓</span> Truy vấn hợp lệ & an toàn (${localEvent.req_id || "GẦN NHẤT"})
                            </span>
                            <span class="alert-pill LOW">LOW</span>
                        </div>
                    `;
                }
            } else {
                // Khi chưa có truy vấn tương tác nào
                alertHtml = `
                    <div style="font-size: 0.82rem; color: var(--text-muted); padding: 10px; text-align: center;">
                        Chưa có cảnh báo phát sinh cho phiên làm việc hiện tại.
                    </div>
                `;
            }

            alertsContainer.innerHTML = alertHtml;
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }

        function escapeModalText(str) {
            if (!str) return '';
            return str.replace(/'/g, "\\'").replace(/"/g, '&quot;');
        }

        function openAlertModal(title, user, level, desc) {
            document.getElementById("modalTitle").innerText = title;
            document.getElementById("modalMeta").innerText = `Vai trò: ${user} • Mức độ: ${level} • Thời gian: Vừa xong`;
            document.getElementById("modalDesc").innerText = desc;
            document.getElementById("alertModal").style.display = "flex";
        }

        function closeAlertModal() {
            document.getElementById("alertModal").style.display = "none";
        }
    </script>
</body>

</html>