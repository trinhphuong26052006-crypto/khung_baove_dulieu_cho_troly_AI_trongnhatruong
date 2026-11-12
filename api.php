<?php
/**
 * API Gateway cho XAMPP Apache
 * Xử lý các request từ web frontend và gọi logic Python RAG / RBAC
 */
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    exit(0);
}

$action = isset($_GET['action']) ? $_GET['action'] : '';

// Đường dẫn Python và Project (tự động phát hiện python có sẵn trên hệ thống)
$projectDir = __DIR__;

// Danh sách các đường dẫn Python tiềm năng
$possiblePythonPaths = [
    'python',
    'python3',
    'C:\\Users\\tuank\\AppData\\Local\\Programs\\Python\\Python313\\python.exe',
    'C:\\Users\\tuank\\AppData\\Local\\Programs\\Python\\Python312\\python.exe',
    'C:\\Users\\tuank\\AppData\\Local\\Programs\\Python\\Python311\\python.exe',
    'C:\\Users\\tuank\\AppData\\Local\\Programs\\Python\\Python310\\python.exe',
    'C:\\Python313\\python.exe',
    'C:\\Python312\\python.exe',
    'C:\\Python311\\python.exe',
    'C:\\Python310\\python.exe',
    'C:\\Users\\Admin\\AppData\\Local\\Programs\\Python\\Python312\\python.exe'
];

$pythonPath = 'python';
foreach ($possiblePythonPaths as $p) {
    if ($p === 'python' || $p === 'python3') {
        // Kiểm tra xem lệnh python có chạy được không
        $check = shell_exec("$p --version 2>&1");
        if ($check && stripos($check, 'Python') !== false) {
            $pythonPath = $p;
            break;
        }
    } else if (file_exists($p)) {
        $pythonPath = $p;
        break;
    }
}

// 1. Lấy danh sách Roles
if ($action === 'roles') {
    echo json_encode([
        "SinhVien" => [
            "name" => "Sinh viên",
            "accessible" => ["Public"],
            "description" => "Chỉ xem các văn bản học vụ, học phí, biểu mẫu công khai."
        ],
        "GiangVien" => [
            "name" => "Giảng viên",
            "accessible" => ["Public", "Internal"],
            "description" => "Xem văn bản công khai và tài liệu chuyên môn nội bộ nhà trường."
        ],
        "QuanTri" => [
            "name" => "Quản trị viên",
            "accessible" => ["Public", "Internal", "Restricted"],
            "description" => "Toàn quyền truy cập cả hồ sơ kỷ luật, kiểm toán và văn bản mật."
        ]
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// 2. Lấy cấu hình
if ($action === 'config') {
    $configFile = $projectDir . '/data/xampp_config.json';
    $cfg = [
        "ENABLE_RBAC_PRERETRIEVAL" => true,
        "ENABLE_OUTPUT_FILTER" => true
    ];
    if (file_exists($configFile)) {
        $cfg = json_decode(file_get_contents($configFile), true) ?: $cfg;
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $input = json_decode(file_get_contents('php://input'), true);
        if (isset($input['ENABLE_RBAC_PRERETRIEVAL'])) {
            $cfg['ENABLE_RBAC_PRERETRIEVAL'] = (bool)$input['ENABLE_RBAC_PRERETRIEVAL'];
        }
        if (isset($input['ENABLE_OUTPUT_FILTER'])) {
            $cfg['ENABLE_OUTPUT_FILTER'] = (bool)$input['ENABLE_OUTPUT_FILTER'];
        }
        file_put_contents($configFile, json_encode($cfg, JSON_PRETTY_PRINT));
    }

    echo json_encode($cfg);
    exit;
}

// 3. Lấy 40 câu hỏi mẫu
if ($action === 'sample-queries') {
    $qPath = $projectDir . '/tests/queries/test_queries.json';
    if (file_exists($qPath)) {
        echo file_get_contents($qPath);
    } else {
        echo json_encode([]);
    }
    exit;
}

// 4. Xem chi tiết tài liệu
if ($action === 'document') {
    $docId = isset($_GET['doc_id']) ? preg_replace('/[^a-zA-Z0-9_-]/', '', $_GET['doc_id']) : '';
    $metaFile = $projectDir . '/data/metadata/documents_metadata.json';
    $foundMeta = null;
    if (file_exists($metaFile)) {
        $metaList = json_decode(file_get_contents($metaFile), true);
        foreach ($metaList as $m) {
            if ($m['doc_id'] === $docId) {
                $foundMeta = $m;
                break;
            }
        }
    }

    // Đọc nội dung file md
    $content = '';
    $filePath = $projectDir . '/' . ($foundMeta['file_path'] ?? '');
    if (file_exists($filePath)) {
        $content = file_get_contents($filePath);
    }

    echo json_encode([
        "doc_id" => $docId,
        "title" => $foundMeta['title'] ?? $docId,
        "classification" => $foundMeta['classification'] ?? 'Public',
        "department" => $foundMeta['department'] ?? '',
        "university" => $foundMeta['university'] ?? '',
        "content" => $content
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

// 5. Chat qua RAG Pipeline
if ($action === 'chat') {
    $input = json_decode(file_get_contents('php://input'), true);
    $query = $input['query'] ?? '';
    $role = $input['role'] ?? 'SinhVien';

    // Đọc cấu hình
    $configFile = $projectDir . '/data/xampp_config.json';
    $enableRbac = 'true';
    $enableFilter = 'true';
    if (file_exists($configFile)) {
        $cfg = json_decode(file_get_contents($configFile), true);
        $enableRbac = empty($cfg['ENABLE_RBAC_PRERETRIEVAL']) ? 'false' : 'true';
        $enableFilter = empty($cfg['ENABLE_OUTPUT_FILTER']) ? 'false' : 'true';
    }

    // Thực thi Python runner
    $cmd = escapeshellarg($pythonPath) . ' ' .
           escapeshellarg($projectDir . '/runner.py') . ' ' .
           escapeshellarg($query) . ' ' .
           escapeshellarg($role) . ' ' .
           $enableRbac . ' ' .
           $enableFilter . ' 2>&1';

    $output = shell_exec($cmd);

    // Bóc tách JSON payload sau marker
    $parts = explode('---JSON_OUTPUT_START---', $output);
    if (count($parts) >= 2) {
        $jsonStr = trim($parts[1]);
        echo $jsonStr;
    } else {
        echo json_encode([
            "status" => "ERROR",
            "action_taken" => "BLOCKED",
            "answer" => "Lỗi thực thi pipeline Python từ XAMPP: " . substr($output, 0, 500),
            "sources" => []
        ], JSON_UNESCAPED_UNICODE);
    }
    exit;
}

// 6. Lấy nhật ký audit logs và số liệu thống kê tích lũy cho Dashboard
if ($action === 'logs') {
    $logPath = $projectDir . '/data/logs/security_audit.log';
    $logs = [];
    $stats = [
        "total" => 0,
        "pass" => 0,
        "block" => 0,
        "redact" => 0,
        "pass_rate" => 0.0,
        "block_rate" => 0.0,
        "redact_rate" => 0.0
    ];

    if (file_exists($logPath)) {
        $lines = file($logPath, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
        if ($lines !== false) {
            // Thống kê tích lũy trên TOÀN BỘ file log
            foreach ($lines as $line) {
                $decoded = json_decode($line, true);
                if ($decoded) {
                    $stats["total"]++;
                    $act = $decoded['action_taken'] ?? '';
                    if ($act === 'PASSED') {
                        $stats["pass"]++;
                    } else if ($act === 'BLOCKED' || $act === 'BLOCKED_INPUT') {
                        $stats["block"]++;
                    } else if ($act === 'REDACTED') {
                        $stats["redact"]++;
                    }
                }
            }

            // Tính tỉ lệ phần trăm
            if ($stats["total"] > 0) {
                $stats["pass_rate"] = round(($stats["pass"] / $stats["total"]) * 100, 1);
                $stats["block_rate"] = round(($stats["block"] / $stats["total"]) * 100, 1);
                $stats["redact_rate"] = round(($stats["redact"] / $stats["total"]) * 100, 1);
            }

            // Lấy 100 sự kiện gần nhất cho danh sách lịch sử
            $recent = array_slice($lines, -100);
            foreach ($recent as $line) {
                $decoded = json_decode($line, true);
                if ($decoded) {
                    $logs[] = $decoded;
                }
            }
        }
    }

    echo json_encode([
        "stats" => $stats,
        "logs" => array_reverse($logs)
    ], JSON_UNESCAPED_UNICODE);
    exit;
}

echo json_encode(["status" => "XAMPP Gateway Ready"]);

