<?php
session_start();
require_once __DIR__ . '/auth_check.php';

// Redirect unauthenticated users to the login page
if (empty($_SESSION['user'])) {
    header('Location: login.php');
    exit;
}

$user = $_SESSION['user'];

// Web chat uses a fixed server-side Controlled configuration.
$_SESSION['app_config'] = ['mode' => 'controlled'];
header('Location: index.php');
exit;
