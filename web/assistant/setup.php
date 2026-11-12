<?php
session_start();
require_once __DIR__ . '/auth_check.php';

// Chưa đăng nhập thì quay về trang Login
if (empty($_SESSION['user'])) {
    header('Location: login.php');
    exit;
}

$user = $_SESSION['user'];

// Xử lý lưu cấu hình thử nghiệm
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $mode = $_POST['mode'] ?? 'controlled';
    $enable_rbac = ($mode === 'controlled');
    $enable_filter = isset($_POST['enable_filter']);

    $config = [
        'mode' => $mode,
        'ENABLE_RBAC_PRERETRIEVAL' => $enable_rbac,
        'ENABLE_OUTPUT_FILTER' => $enable_filter,
        'configured_at' => date('Y-m-d H:i:s')
    ];

    $_SESSION['app_config'] = $config;

    // Lưu vào file JSON cấu hình XAMPP
    $configFile = dirname(dirname(__DIR__)) . '/data/xampp_config.json';
    file_put_contents($configFile, json_encode($config, JSON_PRETTY_PRINT));

    header('Location: index.php');
    exit;
}
?>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cấu Hình Phân Quyền RBAC & RAG - Bước 2</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="static/style.css">
    <style>
        .setup-page-bg {
            min-height: 100vh;
            width: 100vw;
            background: #f4f7fc;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px 20px;
        }

        .setup-main-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            width: 820px;
            max-width: 95vw;
            padding: 40px 48px;
            box-shadow: 0 16px 40px rgba(25, 81, 252, 0.06);
        }

        .setup-header-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding-bottom: 24px;
            border-bottom: 1.5px solid #f1f5f9;
            margin-bottom: 30px;
        }

        .step-pill {
            display: inline-block;
            background: #eff6ff;
            color: #1951fc;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            margin-bottom: 8px;
            border: 1px solid #bfdbfe;
        }

        .setup-title-h2 {
            font-size: 1.4rem;
            font-weight: 800;
            color: #03195b;
            letter-spacing: -0.02em;
        }

        .user-badge-profile {
            display: flex;
            align-items: center;
            gap: 12px;
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            padding: 8px 16px;
            border-radius: 12px;
        }

        .user-text-col {
            display: flex;
            flex-direction: column;
            text-align: right;
        }

        .user-text-name {
            font-size: 0.82rem;
            font-weight: 700;
            color: #1e293b;
        }

        .user-text-role {
            font-size: 0.7rem;
            color: #64748b;
        }

        /* 2 Option Cards */
        .mode-selection-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 26px;
        }

        .mode-choice-card {
            background: #ffffff;
            border: 2px solid #e2e8f0;
            border-radius: 18px;
            padding: 24px;
            cursor: pointer;
            transition: all 0.25s ease;
            position: relative;
        }

        .mode-choice-card:hover {
            border-color: #7cb2fd;
            transform: translateY(-3px);
            box-shadow: 0 10px 25px rgba(25, 81, 252, 0.08);
        }

        .mode-choice-card.selected {
            border-color: #1951fc;
            background: #eff6ff;
            box-shadow: 0 10px 30px rgba(25, 81, 252, 0.15);
        }

        .mode-choice-icon {
            font-size: 2rem;
            margin-bottom: 12px;
        }

        .mode-choice-title {
            font-size: 1.15rem;
            font-weight: 800;
            margin-bottom: 6px;
        }

        .mode-choice-desc {
            font-size: 0.82rem;
            color: #475569;
            line-height: 1.5;
            margin-bottom: 16px;
        }

        .feature-bullets {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 0.78rem;
            color: #334155;
            font-weight: 500;
        }

        .feature-bullets li {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Guardrail Toggle */
        .guardrail-toggle-panel {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            padding: 16px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }

        .btn-start-chat {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #1951fc 0%, #3781fc 100%);
            border: none;
            border-radius: 14px;
            color: #ffffff;
            font-size: 1.05rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.25s ease;
            box-shadow: 0 6px 20px rgba(25, 81, 252, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }

        .btn-start-chat:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 28px rgba(25, 81, 252, 0.4);
        }
    </style>
</head>
<body>
    <div class="setup-page-bg">
        <div class="setup-main-card">
            <div class="setup-header-row">
                <div>
                    <span class="step-pill">BƯỚC 2: THIẾT LẬP THỰC NGHIỆM</span>
                    <h2 class="setup-title-h2">Chọn Cơ Chế Kiểm Soát Dữ Liệu</h2>
                </div>
                <div class="user-badge-profile">
                    <div class="user-text-col">
                        <span class="user-text-name"><?= htmlspecialchars($user['full_name']) ?></span>
                        <span class="user-text-role"><?= htmlspecialchars($user['email']) ?></span>
                    </div>
                    <span class="role-tag <?= htmlspecialchars($user['role']) ?>"><?= htmlspecialchars($user['role']) ?></span>
                </div>
            </div>

            <form method="POST" action="setup.php">
                <input type="radio" name="mode" id="modeControlled" value="controlled" checked style="display:none;">
                <input type="radio" name="mode" id="modeBaseline" value="baseline" style="display:none;">

                <div class="mode-selection-grid">
                    <!-- Controlled -->
                    <div class="mode-choice-card selected" id="boxControlled" onclick="selectMode('controlled')">
                        <div class="mode-choice-icon">🛡️</div>
                        <h3 class="mode-choice-title" style="color: #1951fc;">Chế Độ Controlled</h3>
                        <p class="mode-choice-desc">Hệ thống kích hoạt toàn bộ cơ chế phân quyền RBAC và kiểm duyệt dữ liệu an toàn.</p>
                        <ul class="feature-bullets">
                            <li><span style="color: #059669;">✔</span> <strong>Pre-retrieval RBAC:</strong> Lọc tài liệu theo vai trò</li>
                            <li><span style="color: #059669;">✔</span> Sinh viên không thể quét tài liệu Mật/Nội bộ</li>
                            <li><span style="color: #059669;">✔</span> Phòng thủ 2 lớp (Defense-in-depth)</li>
                            <li><span style="color: #059669;">✔</span> <strong>Đạt chuẩn ATTT:</strong> Ngăn chặn 100% rò rỉ</li>
                        </ul>
                    </div>

                    <!-- Baseline -->
                    <div class="mode-choice-card" id="boxBaseline" onclick="selectMode('baseline')">
                        <div class="mode-choice-icon">⚠️</div>
                        <h3 class="mode-choice-title" style="color: #d97706;">Chế Độ Baseline</h3>
                        <p class="mode-choice-desc">Mô hình RAG truyền thống tắt kiểm soát phân quyền để làm nhóm đối chứng thực nghiệm.</p>
                        <ul class="feature-bullets">
                            <li><span style="color: #dc2626;">✘</span> <strong>Không phân quyền:</strong> Tìm trên toàn bộ 96 văn bản</li>
                            <li><span style="color: #dc2626;">✘</span> Sinh viên có thể bị lọt dữ liệu kỷ luật/tài chính</li>
                            <li><span style="color: #0284c7;">ℹ</span> Phục vụ đo lường tỷ lệ rò rỉ dữ liệu (Data Leakage)</li>
                        </ul>
                    </div>
                </div>

                <div class="guardrail-toggle-panel">
                    <div>
                        <div style="font-size: 0.88rem; font-weight: 700; color: #1e293b; margin-bottom: 3px;">Kích hoạt bộ lọc an toàn đầu ra (Output Guardrails)</div>
                        <div style="font-size: 0.78rem; color: #64748b;">Tự động che giấu thông tin định danh cá nhân (PII: CCCD, Số điện thoại, Điểm số).</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" name="enable_filter" checked>
                        <span class="slider"></span>
                    </label>
                </div>

                <button type="submit" class="btn-start-chat">
                    Xác nhận cấu hình & Bắt đầu hỏi đáp
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="5" y1="12" x2="19" y2="12"></line>
                        <polyline points="12 5 19 12 12 19"></polyline>
                    </svg>
                </button>
            </form>
        </div>
    </div>

    <script>
        function selectMode(mode) {
            if (mode === 'controlled') {
                document.getElementById('modeControlled').checked = true;
                document.getElementById('boxControlled').classList.add('selected');
                document.getElementById('boxBaseline').classList.remove('selected');
            } else {
                document.getElementById('modeBaseline').checked = true;
                document.getElementById('boxBaseline').classList.add('selected');
                document.getElementById('boxControlled').classList.remove('selected');
            }
        }
    </script>
</body>
</html>
