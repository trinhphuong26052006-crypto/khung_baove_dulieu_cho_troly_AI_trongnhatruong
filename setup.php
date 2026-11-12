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
    $configFile = __DIR__ . '/data/xampp_config.json';
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
    <link rel="stylesheet" href="web/static/style.css">
    <style>
        .setup-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            width: 100vw;
            background: radial-gradient(circle at 50% 20%, #1e2029 0%, #111216 70%);
            padding: 24px;
        }
        .setup-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            width: 720px;
            max-width: 95vw;
            padding: 32px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .setup-header {
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 18px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .setup-title {
            font-size: 1.2rem;
            font-weight: 700;
            color: #f3f4f6;
        }
        .user-greeting {
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 0.85rem;
        }
        .config-options {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }
        .option-box {
            background: #15161b;
            border: 2px solid var(--card-border);
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }
        .option-box:hover {
            border-color: #4b5563;
        }
        .option-box.selected {
            border-color: var(--accent-blue);
            background: rgba(59, 130, 246, 0.08);
        }
        .option-title {
            font-size: 1rem;
            font-weight: 700;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .option-desc {
            font-size: 0.8rem;
            color: var(--text-muted);
            line-height: 1.5;
            margin-bottom: 12px;
        }
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 0;
            font-size: 0.75rem;
            color: var(--text-secondary);
        }
        .feature-list li {
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .extra-guardrail {
            background: #15161b;
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .btn-continue {
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #3b82f6, #6366f1);
            border: none;
            border-radius: 8px;
            color: white;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        .btn-continue:hover {
            opacity: 0.9;
        }
        .logout-link {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.75rem;
        }
        .logout-link:hover {
            color: #ef4444;
        }
    </style>
</head>
<body>
    <div class="setup-wrapper">
        <div class="setup-card">
            <div class="setup-header">
                <div>
                    <div style="font-size: 0.75rem; color: #60a5fa; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Bước 2/2: Thiết lập thử nghiệm</div>
                    <div class="setup-title">CẤU HÌNH KIỂM SOÁT PHÂN QUYỀN RBAC & PRE-RETRIEVAL</div>
                </div>
                <div class="user-greeting">
                    <span><?= htmlspecialchars($user['full_name']) ?></span>
                    <span class="role-tag <?= htmlspecialchars($user['role']) ?>"><?= htmlspecialchars($user['role']) ?></span>
                    <a href="logout.php" class="logout-link" title="Đăng xuất">Đổi tài khoản</a>
                </div>
            </div>

            <form method="POST" action="setup.php">
                <input type="radio" name="mode" id="modeControlled" value="controlled" checked style="display:none;">
                <input type="radio" name="mode" id="modeBaseline" value="baseline" style="display:none;">

                <div class="config-options">
                    <!-- Chế độ 1: Controlled -->
                    <div class="option-box selected" id="boxControlled" onclick="selectMode('controlled')">
                        <div class="option-title" style="color: #60a5fa;">
                            <span>🛡️</span> Chế Độ Controlled
                        </div>
                        <div class="option-desc">
                            Mô hình bảo vệ dữ liệu toàn trình có kiểm soát phân quyền RBAC và tiền lọc (Pre-retrieval).
                        </div>
                        <ul class="feature-list">
                            <li><span style="color: #34d399;">✔</span> Phân quyền nghiêm ngặt theo RBAC Matrix</li>
                            <li><span style="color: #34d399;">✔</span> Pre-retrieval: Sinh viên chỉ quét văn bản Public</li>
                            <li><span style="color: #34d399;">✔</span> Lớp phòng vệ Defense-in-depth</li>
                            <li><span style="color: #34d399;">✔</span> Tỷ lệ rò rỉ thông tin mật: 0%</li>
                        </ul>
                    </div>

                    <!-- Chế độ 2: Baseline -->
                    <div class="option-box" id="boxBaseline" onclick="selectMode('baseline')">
                        <div class="option-title" style="color: #fbbf24;">
                            <span>⚠️</span> Chế Độ Baseline
                        </div>
                        <div class="option-desc">
                            Mô hình RAG truyền thống không kiểm soát phân quyền, dùng làm nhóm đối chứng thực nghiệm.
                        </div>
                        <ul class="feature-list">
                            <li><span style="color: #ef4444;">✘</span> Tắt bộ lọc phân quyền Pre-retrieval</li>
                            <li><span style="color: #ef4444;">✘</span> Truy xuất toàn bộ 96 tài liệu trường</li>
                            <li><span style="color: #ef4444;">✘</span> Nguy cơ rò rỉ hồ sơ mật / kỷ luật</li>
                            <li><span style="color: #38bdf8;">ℹ</span> Dùng đo lường hiệu quả trước và sau bảo vệ</li>
                        </ul>
                    </div>
                </div>

                <!-- Bổ sung Output Guardrails (Nhung) -->
                <div class="extra-guardrail">
                    <div>
                        <div style="font-size: 0.85rem; font-weight: 600; color: #f3f4f6;">Kích hoạt bộ lọc an toàn đầu ra (Output Guardrails)</div>
                        <div style="font-size: 0.75rem; color: var(--text-muted);">Tự động phát hiện vi phạm và che dấu thông tin định danh cá nhân (PII: CCCD, SĐT).</div>
                    </div>
                    <label class="switch">
                        <input type="checkbox" name="enable_filter" checked>
                        <span class="slider"></span>
                    </label>
                </div>

                <button type="submit" class="btn-continue">Xác nhận cấu hình & Bắt đầu hỏi đáp AI →</button>
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
