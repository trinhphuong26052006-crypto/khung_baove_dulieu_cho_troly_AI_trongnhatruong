<?php
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
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
    <link rel="stylesheet" href="static/style.css">
    <style>
        .setup-wrapper {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            width: 100vw;
            background: radial-gradient(circle at 50% 15%, #e0edff 0%, #f4f7fc 70%);
            padding: 24px;
        }
        .setup-card {
            background: #ffffff;
            border: 1px solid var(--card-border);
            border-radius: 20px;
            width: 740px;
            max-width: 95vw;
            padding: 36px;
            box-shadow: 0 20px 45px rgba(25, 81, 252, 0.08);
        }
        .setup-header {
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 20px;
            margin-bottom: 26px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .setup-title {
            font-size: 1.25rem;
            font-weight: 800;
            color: var(--blue-darkest);
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
            gap: 18px;
            margin-bottom: 24px;
        }
        .option-box {
            background: #f8fafc;
            border: 2px solid var(--card-border);
            border-radius: 14px;
            padding: 22px;
            cursor: pointer;
            transition: all 0.2s;
            position: relative;
        }
        .option-box:hover {
            border-color: var(--blue-soft);
            background: #ffffff;
            transform: translateY(-2px);
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.04);
        }
        .option-box.selected {
            border-color: var(--blue-primary);
            background: #eff6ff;
            box-shadow: 0 6px 20px rgba(25, 81, 252, 0.12);
        }
        .option-title {
            font-size: 1.05rem;
            font-weight: 800;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .option-desc {
            font-size: 0.82rem;
            color: var(--text-secondary);
            line-height: 1.5;
            margin-bottom: 14px;
        }
        .feature-list {
            list-style: none;
            padding: 0;
            margin: 0;
            font-size: 0.78rem;
            color: var(--text-secondary);
        }
        .feature-list li {
            margin-bottom: 7px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .extra-guardrail {
            background: #f8fafc;
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 16px 20px;
            margin-bottom: 26px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .btn-continue {
            width: 100%;
            padding: 15px;
            background: var(--accent-gradient);
            border: none;
            border-radius: 12px;
            color: white;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: var(--accent-pill-glow);
        }
        .btn-continue:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 20px rgba(25, 81, 252, 0.35);
        }
        .logout-link {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.78rem;
            font-weight: 600;
        }
        .logout-link:hover {
            color: #ef4444;
        }
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

