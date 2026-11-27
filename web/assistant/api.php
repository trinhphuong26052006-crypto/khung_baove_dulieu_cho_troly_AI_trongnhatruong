<?php
declare(strict_types=1);

header('Content-Type: application/json; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');

function respond(array $payload, int $status = 200): void {
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_UNICODE | JSON_INVALID_UTF8_SUBSTITUTE);
    exit;
}

function fail_request(string $message, int $status): void {
    respond(['status' => 'ERROR', 'error' => $message, 'sources' => []], $status);
}

if (!in_array($_SERVER['REMOTE_ADDR'] ?? '', ['127.0.0.1', '::1'], true)) {
    fail_request('API chỉ phục vụ nguyên mẫu cục bộ.', 403);
}

require_once __DIR__ . '/auth_check.php';
$roles = [
    'SinhVien' => ['name' => 'Sinh viên', 'accessible' => ['Public'], 'description' => 'Truy xuất tài liệu công khai.'],
    'GiangVien' => ['name' => 'Giảng viên', 'accessible' => ['Public', 'Internal'], 'description' => 'Truy xuất tài liệu công khai và nội bộ.'],
    'QuanTri' => ['name' => 'Quản trị viên', 'accessible' => ['Public', 'Internal', 'Restricted'], 'description' => 'Truy xuất cả ba mức tài liệu.'],
];
$user = $_SESSION['user'] ?? null;
$role = is_array($user) ? ($user['role'] ?? null) : null;
session_write_close();

if ($user === null) {
    fail_request('Phiên đăng nhập không còn hiệu lực.', 401);
}
if (!is_string($role) || !array_key_exists($role, $roles)) {
    fail_request('Tài khoản không có vai trò hợp lệ.', 403);
}

$action = $_GET['action'] ?? '';
$method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
require_once __DIR__ . '/project_paths.php';
$root = attt_project_root();

if ($action === 'roles' && $method === 'GET') {
    respond($roles);
}
if ($action === 'config' && $method === 'GET') {
    respond(['ENABLE_RBAC_PRERETRIEVAL' => true, 'ENABLE_OUTPUT_FILTER' => true]);
}
if ($action === 'sample-queries' && $method === 'GET') {
    if ($root === null) {
        fail_request('Không tìm thấy thư mục dự án chứa src/main.py.', 503);
    }
    $path = $root . '/tests/queries/test_queries.json';
    $samples = is_file($path) ? json_decode((string) file_get_contents($path), true) : [];
    respond(is_array($samples) ? $samples : []);
}
if ($action === 'document') {
    fail_request('Chức năng xem toàn văn đang khóa.', 403);
}
if ($action !== 'chat' || $method !== 'POST') {
    fail_request('Tác vụ không được hỗ trợ.', 404);
}

$contentType = strtolower(trim(explode(';', $_SERVER['CONTENT_TYPE'] ?? '', 2)[0]));
if ($contentType !== 'application/json') {
    fail_request('Yêu cầu phải dùng application/json.', 415);
}
$raw = file_get_contents('php://input', false, null, 0, 16385);
if (!is_string($raw) || strlen($raw) > 16384) {
    fail_request('Yêu cầu quá lớn.', 400);
}
$input = json_decode($raw, true);
$query = is_array($input) ? ($input['query'] ?? null) : null;
if (!is_string($query) || trim($query) === '' || preg_match('/^.{1,500}$/usD', trim($query)) !== 1) {
    fail_request('Câu hỏi không hợp lệ hoặc vượt quá 500 ký tự.', 400);
}

if ($root === null) {
    fail_request('Không tìm thấy thư mục dự án chứa src/main.py.', 503);
}
if (!function_exists('proc_open')) {
    fail_request('PHP chưa bật proc_open để khởi chạy Python.', 503);
}

$python = getenv('ATTT_PYTHON');
if ($python === false || $python === '') {
    $venvPython = PHP_OS_FAMILY === 'Windows' ? '/.venv/Scripts/python.exe' : '/.venv/bin/python';
    $python = is_file($root . $venvPython) ? $root . $venvPython : 'python';
}
$payload = json_encode(['query' => trim($query), 'role' => $role], JSON_UNESCAPED_UNICODE);
$process = proc_open(
    [$python, __DIR__ . '/runner.py', '--web-stdin'],
    [0 => ['pipe', 'r'], 1 => ['pipe', 'w'], 2 => ['file', PHP_OS_FAMILY === 'Windows' ? 'NUL' : '/dev/null', 'a']],
    $pipes,
    $root,
    null,
    ['bypass_shell' => true]
);
if (!is_resource($process)) {
    fail_request('Không thể khởi động pipeline Python.', 502);
}
fwrite($pipes[0], $payload);
fclose($pipes[0]);
$output = stream_get_contents($pipes[1]);
fclose($pipes[1]);
$exitCode = proc_close($process);
$marker = "---JSON_OUTPUT_START---\n";
$start = is_string($output) ? strpos(str_replace("\r\n", "\n", $output), $marker) : false;
if ($exitCode !== 0 || $start === false) {
    fail_request('Pipeline Python không trả kết quả hợp lệ.', 502);
}
$output = str_replace("\r\n", "\n", $output);
$result = json_decode(trim(substr($output, $start + strlen($marker))), true);
if (!is_array($result) || ($result['status'] ?? 'ERROR') === 'ERROR') {
    fail_request('Không thể xử lý câu hỏi.', 502);
}
respond($result);
