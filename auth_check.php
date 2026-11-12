<?php
/**
 * Helper kết nối CSDL MySQL và xác thực tài khoản
 */
session_start();

function get_db_connection() {
    $configFile = __DIR__ . '/web/config/database.local.php';
    if (!file_exists($configFile)) {
        $configFile = __DIR__ . '/web/config/database.example.php';
    }
    require_once $configFile;

    try {
        $dsn = "mysql:host=" . DB_HOST . ";port=" . DB_PORT . ";dbname=" . DB_NAME . ";charset=" . DB_CHARSET;
        $pdo = new PDO($dsn, DB_USER, DB_PASS, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC
        ]);
        return $pdo;
    } catch (Exception $e) {
        return null;
    }
}

function check_auth() {
    if (empty($_SESSION['user'])) {
        header('Location: login.php');
        exit;
    }
    if (!isset($_SESSION['app_config'])) {
        header('Location: setup.php');
        exit;
    }
}
