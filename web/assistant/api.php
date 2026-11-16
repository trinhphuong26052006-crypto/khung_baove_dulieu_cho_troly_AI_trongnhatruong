<?php
/**
 * web/assistant/api.php
 * XAMPP gateway for the school AI assistant.
 * Local development only: UI-selected roles are not authenticated identities.
 */
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function respond(array $data, int $code = 200): void {
    http_response_code($code);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
    exit;
}

function readJsonBody(): array {
    $raw = file_get_contents('php://input');
    if (!is_string($raw) || strlen($raw) > 16384) {
        respond(['status' => 'ERROR', 'error' => 'Invalid request size.', 'sources' => []], 400);
    }
    $data = json_decode($raw, true);
    if (!is_array($data) || json_last_error() !== JSON_ERROR_NONE) {
        respond(['status' => 'ERROR', 'error' => 'Invalid JSON body.', 'sources' => []], 400);
    }
    return $data;
}

function readConfig(string $path): array {
    $defaults = ['ENABLE_RBAC_PRERETRIEVAL' => true, 'ENABLE_OUTPUT_FILTER' => true];
    if (!is_file($path)) {
        return $defaults;
    }
    $data = json_decode((string)file_get_contents($path), true);
    if (!is_array($data)) {
        return $defaults;
    }
    return [
        'ENABLE_RBAC_PRERETRIEVAL' => ($data['ENABLE_RBAC_PRERETRIEVAL'] ?? true) === true,
        'ENABLE_OUTPUT_FILTER' => ($data['ENABLE_OUTPUT_FILTER'] ?? true) === true,
    ];
}

$action = isset($_GET['action']) && is_string($_GET['action']) ? $_GET['action'] : '';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
$projectDir = dirname(__DIR__, 2);
$candidatePythons = [
    $projectDir . DIRECTORY_SEPARATOR . '.venv' . DIRECTORY_SEPARATOR . 'Scripts' . DIRECTORY_SEPARATOR . 'python.exe',
    'C:\\Users\\tuank\\AppData\\Local\\Programs\\Python\\Python313\\python.exe',
    'python'
];

$pythonPath = '';
foreach ($candidatePythons as $p) {
    if ($p === 'python' || is_file($p)) {
        $pythonPath = $p;
        break;
    }
}

$runnerPath = __DIR__ . DIRECTORY_SEPARATOR . 'runner.py';
$configFile = $projectDir . DIRECTORY_SEPARATOR . 'data' . DIRECTORY_SEPARATOR . 'xampp_config.json';

// Restrict this demonstration API to requests from the local machine.
// For deployment on a LAN/server, replace with proper authentication and authorization.
$remoteAddress = $_SERVER['REMOTE_ADDR'] ?? '';
if (!in_array($remoteAddress, ['127.0.0.1', '::1'], true)) {
    respond(['status' => 'ERROR', 'error' => 'Local development access only.', 'sources' => []], 403);
}

if ($action === 'roles' && $method === 'GET') {
    respond([
        'SinhVien' => ['name' => 'Sinh viên', 'accessible' => ['Public'], 'description' => 'Chỉ xem các văn bản học vụ, học phí, biểu mẫu công khai.'],
        'GiangVien' => ['name' => 'Giảng viên', 'accessible' => ['Public', 'Internal'], 'description' => 'Xem văn bản công khai và tài liệu chuyên môn nội bộ nhà trường.'],
        'QuanTri' => ['name' => 'Quản trị viên', 'accessible' => ['Public', 'Internal', 'Restricted'], 'description' => 'Vai trò kiểm thử có quyền truy cập tài liệu hạn chế.'],
    ]);
}

if ($action === 'config') {
    if ($method === 'GET') {
        respond(readConfig($configFile));
    }
    // Prevent unauthenticated changes to security configuration.
    respond(['status' => 'ERROR', 'error' => 'Configuration changes are disabled via this API.', 'sources' => []], 403);
}

if ($action === 'sample-queries' && $method === 'GET') {
    $path = $projectDir . DIRECTORY_SEPARATOR . 'tests' . DIRECTORY_SEPARATOR . 'queries' . DIRECTORY_SEPARATOR . 'test_queries.json';
    if (!is_file($path)) {
        respond([]);
    }
    $data = json_decode((string)file_get_contents($path), true);
    respond(is_array($data) ? $data : []);
}

if ($action === 'document') {
    respond([
        'status' => 'DENIED',
        'action_taken' => 'BLOCKED',
        'answer' => 'Chức năng xem toàn văn tài liệu tạm khóa để bảo vệ dữ liệu.',
        'sources' => [],
    ], 403);
}

if ($action === 'chat' && $method === 'POST') {
    $input = readJsonBody();
    $query = $input['query'] ?? null;
    $role = $input['role'] ?? 'SinhVien';
    if (!is_string($query) || trim($query) === '' || mb_strlen($query, 'UTF-8') > 500) {
        respond(['status' => 'ERROR', 'error' => 'Câu hỏi không hợp lệ hoặc vượt quá 500 ký tự.', 'sources' => []], 400);
    }
    if (!is_string($role) || !in_array($role, ['SinhVien', 'GiangVien', 'QuanTri'], true)) {
        respond(['status' => 'ERROR', 'error' => 'Vai trò không hợp lệ.', 'sources' => []], 400);
    }
    if (empty($pythonPath) || !is_file($runnerPath)) {
        respond(['status' => 'ERROR', 'error' => 'Không tìm thấy Python hoặc runner.py.', 'sources' => []], 500);
    }
    $cfg = readConfig($configFile);
    $rbac = $cfg['ENABLE_RBAC_PRERETRIEVAL'] ? 'true' : 'false';
    $filter = $cfg['ENABLE_OUTPUT_FILTER'] ? 'true' : 'false';
    $cmd = escapeshellarg($pythonPath) . ' ' . escapeshellarg($runnerPath) . ' ' . escapeshellarg(trim($query)) . ' ' . escapeshellarg($role) . ' ' . $rbac . ' ' . $filter . ' 2>&1';
    $output = shell_exec($cmd);
    if (!is_string($output)) {
        error_log('Chat gateway: Python produced no output.');
        respond(['status' => 'ERROR', 'error' => 'Không nhận được phản hồi từ Python.', 'sources' => []], 502);
    }
    $marker = '---JSON_OUTPUT_START---';
    $position = strrpos($output, $marker);
    if ($position === false) {
        error_log('Chat gateway: JSON marker missing; output bytes=' . strlen($output));
        respond(['status' => 'ERROR', 'error' => 'Pipeline Python không trả kết quả hợp lệ. Kiểm tra log máy chủ.', 'sources' => []], 502);
    }
    $payload = trim(substr($output, $position + strlen($marker)));
    $decoded = json_decode($payload, true);
    if (!is_array($decoded) || json_last_error() !== JSON_ERROR_NONE) {
        error_log('Chat gateway: Invalid JSON after marker.');
        respond(['status' => 'ERROR', 'error' => 'Phản hồi Python không phải JSON hợp lệ.', 'sources' => []], 502);
    }
    if (($decoded['status'] ?? '') === 'ERROR') {
        respond($decoded, 502);
    }
    respond($decoded);
}

respond(['status' => 'ERROR', 'error' => 'Endpoint hoặc phương thức không được hỗ trợ.', 'sources' => []], 404);
