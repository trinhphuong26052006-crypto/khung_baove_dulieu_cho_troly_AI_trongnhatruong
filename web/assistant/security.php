<?php

/** Security Dashboard – module Phương. Read-only; QuanTri only. */

if (session_status() !== PHP_SESSION_ACTIVE) { session_start(); }

require_once __DIR__ . '/auth_check.php';

check_auth();

$user = $_SESSION['user'] ?? [];

if (($user['role'] ?? '') !== 'QuanTri') {

    http_response_code(403);

    header('Content-Type: text/html; charset=utf-8');

    exit('403 – You are not authorized to access the security dashboard.');

}

header('Cache-Control: no-store, private');

header('X-Content-Type-Options: nosniff');

header('Referrer-Policy: same-origin');

header('X-Frame-Options: DENY');

function esc($s) { return htmlspecialchars((string)$s, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8'); }

$root = dirname(__DIR__, 2);

$cfgPath = $root . '/data/xampp_config.json';

$cfg = ['ENABLE_RBAC_PRERETRIEVAL'=>true, 'ENABLE_OUTPUT_FILTER'=>true];

if (is_file($cfgPath)) {

    $loaded = json_decode((string)@file_get_contents($cfgPath), true);

    if (is_array($loaded)) {

        foreach ($cfg as $key=>$default) {

            if (array_key_exists($key,$loaded)) $cfg[$key] = ($loaded[$key] === true);

        }

    }

}

$rbac = $cfg['ENABLE_RBAC_PRERETRIEVAL'];

$filter = $cfg['ENABLE_OUTPUT_FILTER'];

$mode = $rbac && $filter ? 'Controlled' : (!$rbac && !$filter ? 'Baseline' : 'Custom');

$logPath = $root . '/logs/security_audit.jsonl';

/** Normalize status and action together so cards, charts and history use one rule. */
function normalizeAuditStatus(array $entry): string {
    $status = strtoupper(trim((string)($entry['status'] ?? '')));
    $action = strtoupper(trim((string)($entry['action_taken'] ?? $entry['action'] ?? '')));
    $values = [$status, $action];

    // Preserve distinct security outcomes. This precedence also matches Control History.
    if (array_intersect($values, ['REDACTED', 'REDACT']) !== []) return 'REDACTED';
    if (array_intersect($values, ['DENIED', 'DENY', 'ACCESS_DENIED']) !== []) return 'DENIED';
    if (array_intersect($values, ['BLOCKED', 'BLOCKED_INPUT', 'BLOCK']) !== []) return 'BLOCKED';
    if (array_intersect($values, ['PASSED', 'PASS', 'ALLOWED', 'ALLOW', 'SUCCESS']) !== []) return 'PASSED';
    return 'OTHER';
}

$events = []; $total = 0; $counts = ['PASSED'=>0,'REDACTED'=>0,'BLOCKED'=>0,'DENIED'=>0,'OTHER'=>0];

$logState = 'Audit log file not found';

if (is_file($logPath) && is_readable($logPath)) {

    $fh = @fopen($logPath, 'rb');

    if ($fh) {

        $logState = 'Audit log connected';

        // Scan log without loading entire file into RAM. Latest 50 valid records only.

        while (($line = fgets($fh, 1048576)) !== false) {

            $entry = json_decode($line, true);

            if (!is_array($entry)) continue;

            $total++;

            $status = normalizeAuditStatus($entry);

            $counts[$status]++;

            $events[] = [

                'time' => (string)($entry['timestamp'] ?? $entry['time'] ?? $entry['created_at'] ?? ''),

                'role' => (string)($entry['role'] ?? '—'),

                'status' => $status,

                'action' => (string)($entry['action_taken'] ?? '—'),

                'latency' => $entry['latency_ms'] ?? null,

            ];

            if (count($events) > 50) array_shift($events);

        }

        fclose($fh);

        $events = array_reverse($events);

    } else { $logState = 'Unable to open audit log'; }

}

// Aggregate last seven calendar days from valid log timestamps (no synthetic events).

$daily = [];

for ($i = 6; $i >= 0; $i--) {

    $day = date('Y-m-d', strtotime("-$i days"));

    $daily[$day] = ['PASSED'=>0, 'REDACTED'=>0, 'BLOCKED'=>0, 'DENIED'=>0, 'OTHER'=>0];

}

if (is_file($logPath) && is_readable($logPath)) {

    $fh = @fopen($logPath, 'rb');

    if ($fh) {

        while (($line = fgets($fh, 1048576)) !== false) {

            $entry = json_decode($line, true);

            if (!is_array($entry)) continue;

            $rawTime = $entry['timestamp'] ?? $entry['time'] ?? $entry['created_at'] ?? null;

            if (!is_string($rawTime) || trim($rawTime) === '') continue;

            $stamp = strtotime($rawTime);

            if ($stamp === false) continue;

            $day = date('Y-m-d', $stamp);

            if (!isset($daily[$day])) continue;

            $status = normalizeAuditStatus($entry);
            if (!isset($daily[$day][$status])) $status = 'OTHER';

            $daily[$day][$status]++;

        }

        fclose($fh);

    }

}

$dailyMax = 0;

foreach ($daily as $v) $dailyMax = max($dailyMax, array_sum($v));

$palette = ['PASSED'=>'#17b68d','REDACTED'=>'#7d68f6','BLOCKED'=>'#f59c53','DENIED'=>'#ee647d','OTHER'=>'#aab4c8'];

$segments = []; $offset = 0;

foreach ($counts as $name=>$number) {

    if ($total === 0 || $number <= 0) continue;

    $next = $offset + 100 * $number / $total;

    $segments[] = $palette[$name].' '.round($offset, 3).'% '.round($next, 3).'%';

    $offset = $next;

}

$donutGradient = $segments ? 'conic-gradient('.implode(', ', $segments).')' : 'conic-gradient(#e9edfa 0% 100%)';


// --- Security Status integration: derive only from actual audit records ---
$guardCounts = ['PASS'=>0, 'REDACTED'=>0, 'BLOCKED'=>0, 'DENIED'=>0, 'UNKNOWN'=>0];
$statusHistory = [];
$securityAlerts = [];
foreach ($events as $event) {
    $raw = strtoupper(trim((string)($event['action'] ?? '')));
    $stat = strtoupper(trim((string)($event['status'] ?? '')));
    if (in_array($stat, ['REDACTED', 'REDACT'], true) || in_array($raw, ['REDACTED', 'REDACT'], true)) {
        $guard = 'REDACTED';
    } elseif (in_array($stat, ['DENIED', 'DENY'], true) || in_array($raw, ['DENIED', 'DENY'], true)) {
        $guard = 'DENIED';
    } elseif (in_array($stat, ['BLOCKED', 'BLOCKED_INPUT', 'BLOCK'], true) || in_array($raw, ['BLOCKED', 'BLOCKED_INPUT', 'BLOCK'], true)) {
        $guard = 'BLOCKED';
    } elseif (in_array($stat, ['PASSED', 'PASS', 'ALLOWED', 'ALLOW', 'SUCCESS'], true) || in_array($raw, ['PASSED', 'PASS', 'ALLOWED', 'ALLOW', 'SUCCESS'], true)) {
        $guard = 'PASS';
    } else {
        $guard = 'UNKNOWN';
    }
    $guardCounts[$guard]++;
    $statusHistory[] = [
        'time'=>$event['time'], 'role'=>$event['role'], 'guard'=>$guard,
        'status'=>$stat, 'action'=>$raw, 'latency'=>$event['latency']
    ];
    if (in_array($guard, ['BLOCKED', 'DENIED', 'REDACTED'], true)) {
        $securityAlerts[] = [
            'time'=>$event['time'],
            'role'=>$event['role'],
            'level'=>in_array($guard, ['BLOCKED', 'DENIED'], true) ? 'HIGH' : 'MEDIUM',
            'label'=>$guard === 'BLOCKED'
                ? 'Request blocked by a security control'
                : ($guard === 'DENIED' ? 'Access denied by RBAC policy' : 'Sensitive output redacted'),
            'detail'=>$guard === 'BLOCKED'
                ? 'A security control blocked this request. Review pipeline logs to identify the enforcing control.'
                : ($guard === 'DENIED'
                    ? 'The access control policy did not authorize the requested resource.'
                    : 'Sensitive content was removed or masked before display.')
        ];
    }
}
$latestStatus = $statusHistory[0] ?? null;
$pipelineStatus = $latestStatus === null ? 'NO DATA' : 'LOGS AVAILABLE';
$accessStatus = $latestStatus === null ? 'N/A' : (in_array($latestStatus['status'], ['DENIED'], true) ? 'DENIED' : 'UNVERIFIED');
$filterStatus = $latestStatus === null ? 'N/A' : $latestStatus['guard'];

?>



<!doctype html>

<html lang="en">

<head>

<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">

<title>Security Dashboard | AI Assistant</title>

<link rel="preconnect" href="https://fonts.googleapis.com">

<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>

<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">

<style>

:root {

    --purple:#6252ec;

    --purple-deep:#5140dd;

    --ink:#191b43;

    --muted:#8290ad;

    --line:#e4e9f6;

    --soft:#f7f9ff;

    --sidebar:#f7f9ff;

    --shadow:0 20px 60px rgba(78,65,162,.09)

}

* {

    box-sizing:border-box

}

html,body {

    margin:0;

    min-height:100%;

    font-family:'Plus Jakarta Sans',sans-serif;

    color:var(--ink)

}

body {

    background:linear-gradient(135deg,#e3e9ff 0%,#f6f0ff 55%,#f0f1ff 100%);

    padding:26px 22px

}

button,a {

    font:inherit

}

button {

    cursor:pointer

}

.app {

    width:min(1370px,100%);

    min-height:calc(100vh - 52px);

    margin:auto;

    background:#fff;

    border-radius:27px;

    overflow:hidden;

    display:flex;

    box-shadow:var(--shadow)

}

.sidebar {

    width:283px;

    flex-shrink:0;

    background:var(--sidebar);

    border-right:1px solid #e3e9f7;

    display:flex;

    flex-direction:column;

    padding:20px 16px 18px;

    min-height:inherit

}

.mac {

    display:flex;

    gap:7px;

    margin:1px 0 19px 4px

}

.mac i {

    width:10px;

    height:10px;

    border-radius:50%;

    display:block

}

.mac i:nth-child(1) {

    background:#ff625d

}

.mac i:nth-child(2) {

    background:#ffbb39

}

.mac i:nth-child(3) {

    background:#28c94d

}

.brand {

    display:flex;

    align-items:center;

    gap:10px;

    margin:0 4px 27px

}

.logo {

    width:38px;

    height:38px;

    border-radius:12px;

    background:linear-gradient(135deg,#00b6fa,#4e51f2);

    box-shadow:0 4px 11px #5362e344;

    color:white;

    display:grid;

    place-items:center;

    font-size:17px;

    font-weight:800

}

.brand strong {

    display:block;

    font-size:16px;

    letter-spacing:-.7px;

    line-height:1.1

}

.brand small {

    display:block;

    font-size:9px;

    font-weight:600;

    line-height:1.4;

    color:#8b9bb6;

    margin-top:4px

}

.nav-caption {

    font-size:10px;

    font-weight:800;

    color:#8d9ab4;

    letter-spacing:1px;

    margin:14px 10px 10px

}

.nav {

    display:flex;

    flex-direction:column;

    gap:7px

}

.nav a {

    display:flex;

    align-items:center;

    gap:11px;

    padding:12px 13px;

    border-radius:12px;

    text-decoration:none;

    color:#63718e;

    font-size:12px;

    font-weight:700;

    transition:background .2s,transform .2s

}

.nav a:hover {

    background:#ecebff;

    transform:translateX(2px)

}

.nav a.active {

    background:#ebe9ff;

    color:var(--purple-deep)

}

.nav .nav-ico {

    width:20px;

    text-align:center;

    font-size:16px

}

.nav .nav-note {

    font-size:9px;

    color:#a3aac3;

    margin-left:auto

}

.sidebar-spacer {

    flex:1;

    min-height:30px

}

.profile-wrap {

    position:relative

}

.profile-trigger {

    width:100%;

    border:1px solid #dce4fa;

    background:#fff;

    display:flex;

    align-items:center;

    text-align:left;

    gap:10px;

    border-radius:14px;

    padding:10px 9px;

    box-shadow:0 2px 5px #606db00b

}

.avatar {

    width:33px;

    height:33px;

    flex-shrink:0;

    border-radius:50%;

    background:linear-gradient(135deg,#7c5cff,#a044ed);

    color:#fff;

    display:grid;

    place-items:center;

    font-weight:800;

    font-size:13px

}

.profile-info {

    min-width:0;

    flex:1

}

.profile-info strong {

    display:block;

    font-size:11px;

    white-space:nowrap;

    overflow:hidden;

    text-overflow:ellipsis

}

.profile-info small {

    display:block;

    color:#8693ae;

    font-size:9px;

    white-space:nowrap;

    overflow:hidden;

    text-overflow:ellipsis;

    margin-top:4px

}

.chevron {

    font-size:12px;

    color:#7d89a8;

    transition:transform .2s

}

.profile-trigger[aria-expanded="true"] .chevron {

    transform:rotate(180deg)

}

.profile-menu {

    position:absolute;

    bottom:calc(100% + 9px);

    left:0;

    right:0;

    background:#fff;

    border:1px solid #e0e5f3;

    border-radius:14px;

    padding:8px;

    box-shadow:0 15px 35px #343b7930;

    z-index:20

}

.profile-menu[hidden] {

    display:none

}

.profile-menu .profile-head {

    padding:9px 10px;

    border-bottom:1px solid var(--line);

    margin-bottom:5px;

    overflow-wrap:anywhere

}

.profile-head strong {

    display:block;

    font-size:12px

}

.profile-head span {

    font-size:10px;

    color:var(--muted)

}

.profile-menu a {

    display:block;

    padding:10px;

    border-radius:8px;

    color:#495573;

    font-size:11px;

    text-decoration:none;

    font-weight:700

}

.profile-menu a:hover {

    background:#f1efff;

    color:var(--purple)

}

.profile-menu a.logout {

    color:#cf4761

}

.workspace {

    min-width:0;

    flex:1;

    display:flex;

    flex-direction:column

}

.topbar {

    height:65px;

    flex-shrink:0;

    border-bottom:1px solid #edf0f8;

    display:flex;

    align-items:center;

    justify-content:space-between;

    padding:0 30px;

    gap:10px

}

.topbar-left {

    display:flex;

    align-items:center;

    gap:8px

}

.top-dot {

    width:7px;

    height:7px;

    background:var(--purple);

    border-radius:50%

}

.topbar-label {

    font-size:12px;

    font-weight:800

}

.topbar-actions {

    display:flex;

    align-items:center;

    gap:9px;

    flex-wrap:wrap

}

.outline-btn {

    border:1px solid #dfe6fa;

    border-radius:9px;

    background:white;

    text-decoration:none;

    padding:9px 12px;

    color:#45516f;

    font-size:11px;

    font-weight:800

}

.role-badge {

    font-size:10px;

    border:1px solid #ffd9dd;

    color:#e44c5b;

    background:#fff4f5;

    padding:8px 10px;

    border-radius:9px;

    font-weight:800

}

.mode-badge {

    border-radius:11px;

    background:linear-gradient(110deg,#7761ff,#5943df);

    color:#fff;

    font-size:10px;

    font-weight:800;

    padding:10px 14px;

    box-shadow:0 4px 12px #6453ef3b

}

.content {

    padding:34px clamp(20px,3vw,40px) 40px;

    overflow:auto;

    background:#fff;

    flex:1

}

.eyebrow {

    font-size:10px;

    color:var(--purple);

    font-weight:800;

    letter-spacing:1.2px;

    text-transform:uppercase

}

.intro {

    display:flex;

    align-items:flex-start;

    justify-content:space-between;

    gap:16px;

    flex-wrap:wrap;

    margin-bottom:25px

}

.intro h1 {

    font-size:27px;

    letter-spacing:-1px;

    margin:9px 0 7px;

    font-weight:800

}

.intro p {

    font-size:12px;

    color:#8592ad;

    line-height:1.7;

    margin:0

}

.refresh {

    font-size:11px;

    text-decoration:none;

    color:var(--purple);

    border:1px solid #e1defc;

    padding:10px 14px;

    border-radius:10px;

    font-weight:800

}

.refresh:hover {

    background:#f2f0ff

}

.stats {

    display:grid;

    grid-template-columns:repeat(4,minmax(0,1fr));

    gap:13px;

    margin-bottom:18px

}

.stat {

    border:1px solid var(--line);

    border-radius:16px;

    padding:19px 17px;

    min-width:0;

    background:#fff;

    box-shadow:0 5px 14px #7c80b40a;

    transition:transform .2s,box-shadow .2s

}

.stat:hover,.panel:hover {

    box-shadow:0 9px 25px #7679b315

}

.stat:hover {

    transform:translateY(-2px)

}

.stat-label {

    font-size:11px;

    font-weight:700;

    color:#7e8baa

}

.stat-value {

    font-size:24px;

    font-weight:800;

    margin:10px 0 4px

}

.stat-hint {

    font-size:10px;

    line-height:1.6;

    color:#9aa5ba

}

.green {

    color:#12906e

}

.orange {

    color:#cb8138

}

.violet {

    color:var(--purple)

}

.panels {

    display:grid;

    grid-template-columns:1fr 1fr;

    gap:17px

}

.panel {

    border:1px solid var(--line);

    border-radius:17px;

    background:#fff;

    padding:22px;

    min-width:0;

    transition:box-shadow .2s

}

.panel h2 {

    font-size:14px;

    font-weight:800;

    margin:0 0 17px

}

.panel-sub {

    font-size:10px;

    color:#9aa5bb;

    line-height:1.65;

    margin:13px 0 0

}

.setting {

    display:flex;

    justify-content:space-between;

    align-items:center;

    gap:10px;

    padding:13px 0;

    border-bottom:1px solid #edf0f7;

    font-size:11px;

    font-weight:600

}

.setting:last-of-type {

    border-bottom:0

}

.flag {

    padding:6px 9px;

    border-radius:7px;

    font-size:10px;

    font-weight:800

}

.flag.on {

    color:#108866;

    background:#eaf8f2

}

.flag.off {

    color:#b47a2d;

    background:#fff5e7

}

.matrix {

    border-collapse:collapse;

    width:100%;

    font-size:11px

}

.matrix th,.matrix td {

    text-align:center;

    padding:12px 7px;

    border-bottom:1px solid #edf0f7

}

.matrix th:first-child,.matrix td:first-child {

    text-align:left

}

.matrix th {

    font-weight:700;

    color:#8490aa

}

.check {

    color:#6454ed;

    font-weight:800

}

.dash {

    color:#b7bed0

}

.audit {

    margin-top:17px

}

.audit-head {

    display:flex;

    justify-content:space-between;

    align-items:center;

    gap:10px;

    flex-wrap:wrap

}

.audit-head h2 {

    margin-bottom:9px

}

.log-state {

    font-size:10px;

    padding:7px 9px;

    background:#f1f3fa;

    color:#53607d;

    border-radius:8px;

    font-weight:700

}

.counts {

    display:flex;

    gap:7px;

    flex-wrap:wrap;

    margin:6px 0

}

.counts span {

    background:#f6f6fc;

    color:#58637e;

    padding:7px 9px;

    border-radius:8px;

    font-size:10px;

    font-weight:800

}

.table-wrap {

    overflow-x:auto;

    margin-top:12px

}

.logs {

    border-collapse:collapse;

    width:100%;

    min-width:620px;

    font-size:11px

}

.logs th,.logs td {

    text-align:left;

    padding:12px 10px;

    border-bottom:1px solid #edf0f7

}

.logs th {

    color:#8a96b0;

    font-weight:700

}

.logs td {

    color:#515b76

}

.empty {

    color:#98a2b8;

    text-align:center!important;

    padding:23px!important

}

.footer-note {

    font-size:10px;

    color:#a1aac0;

    line-height:1.7;

    margin-top:15px

}

@media(max-width:1100px) {

    .sidebar {

        width:240px

    }

    .stats {

        grid-template-columns:repeat(2,minmax(0,1fr))

    }

    .panels {

        grid-template-columns:1fr

    }

}

@media(max-width:700px) {

    body {

        padding:0

    }

    .app {

        border-radius:0;

        min-height:100vh;

        display:block

    }

    .sidebar {

        width:100%;

        min-height:auto;

        padding:13px

    }

    .mac {

        display:none

    }

    .brand {

        margin-bottom:12px

    }

    .nav {

        flex-direction:row;

        flex-wrap:wrap

    }

    .nav a {

        padding:9px

    }

    .nav-caption {

        margin:4px 0

    }

    .sidebar-spacer {

        display:none

    }

    .profile-wrap {

        margin-top:10px

    }

    .profile-menu {

        bottom:auto;

        top:calc(100% + 6px)

    }

    .topbar {

        padding:12px 15px;

        height:auto;

        min-height:60px

    }

    .topbar-actions {

        gap:5px

    }

    .mode-badge {

        padding:8px

    }

    .content {

        padding:24px 15px

    }

    .intro h1 {

        font-size:23px

    }

    .stats {

        gap:9px

    }

    .stat {

        padding:14px

    }

    .stat-value {

        font-size:21px

    }

    .panel {

        padding:15px

    }

}

/* Visual refinement: same Jakarta font and purple palette as Chat */

.stat,.panel {

    position:relative;

    isolation:isolate;

    transition:transform .24s ease,box-shadow .24s ease,border-color .24s ease,background .24s ease

}

.stat::before {

    content:"";

    position:absolute;

    inset:0;

    border-radius:inherit;

    pointer-events:none;

    background:linear-gradient(145deg,rgba(255,255,255,.68),transparent 65%);

    z-index:-1;

}

.stat:nth-child(1) {

    background:linear-gradient(140deg,#f1fbf8,#fff 70%);

    border-color:#d7f1e9

}

.stat:nth-child(2) {

    background:linear-gradient(140deg,#f3f0ff,#fff 72%);

    border-color:#e5defd

}

.stat:nth-child(3) {

    background:linear-gradient(140deg,#f1f5ff,#fff 72%);

    border-color:#dfe7ff

}

.stat:nth-child(4) {

    background:linear-gradient(140deg,#fff3f5,#fff 72%);

    border-color:#f8dfe7

}

.stat:hover {

    transform:translateY(-5px);

    border-color:#c7bcff;

    box-shadow:0 15px 32px rgba(99,82,236,.16),0 0 0 1px rgba(99,82,236,.07)

}

.panel:hover {

    transform:translateY(-2px);

    border-color:#d7ceff;

    box-shadow:0 13px 34px rgba(92,78,192,.10)

}

.stat-value {

    font-family:'Plus Jakarta Sans',Arial,sans-serif;
    font-size:29px;
    font-weight:700;
    font-style:normal;
    font-variant-numeric:lining-nums tabular-nums;
    font-feature-settings:'lnum' 1,'tnum' 1;
    letter-spacing:0;
    line-height:1.2;
    text-shadow:none;
    transform:none;

}

.stat-label {

    color:#566486

}

.stat-hint {

    color:#8d99b3

}

.flag.on {

    box-shadow:0 0 0 3px rgba(20,171,128,.07)

}

.counts span {

    transition:transform .2s,box-shadow .2s;

    background:#f5f3ff;

    color:#5d4cba;

    border:1px solid #ece8ff

}

.counts span:hover {

    transform:translateY(-2px);

    box-shadow:0 5px 12px #7463d522

}

.logs tbody tr {

    transition:background .2s

}

.logs tbody tr:hover {

    background:#f7f5ff

}

.charts {

    display:grid;

    grid-template-columns:1fr 1fr;

    gap:17px;

    margin-top:17px

}

.chart-panel {

    min-height:300px

}

.chart-title {

    display:flex;

    align-items:center;

    justify-content:space-between;

    gap:10px

}

.chart-title h2 {

    margin-bottom:8px

}

.chart-sub {

    font-size:10px;

    color:#95a1b8;

    line-height:1.6

}

.donut-layout {

    display:flex;

    align-items:center;

    gap:24px;

    flex-wrap:wrap;

    margin-top:19px

}

.donut {

    width:170px;

    height:170px;

    border-radius:50%;

    display:grid;

    place-items:center;

    flex-shrink:0;

    position:relative;

    box-shadow:0 12px 30px rgba(96,78,194,.09)

}

.donut::after {

    content:"";

    position:absolute;

    inset:28px;

    border-radius:50%;

    background:white;

    box-shadow:inset 0 0 0 1px #f0f1fa

}

.donut-center {

    z-index:1;

    text-align:center

}

.donut-center strong {

    display:block;

    font-size:26px;

    letter-spacing:-1px

}

.donut-center small {

    font-size:10px;

    color:#91a0b8

}

.legend {

    display:grid;

    gap:10px;

    flex:1;

    min-width:145px

}

.legend-item {

    display:flex;

    align-items:center;

    justify-content:space-between;

    gap:8px;

    font-size:11px;

    font-weight:700;

    color:#596581

}

.legend-name {

    display:flex;

    align-items:center;

    gap:8px

}

.legend-dot {

    width:9px;

    height:9px;

    border-radius:3px;

    flex-shrink:0

}

.trend-chart {

    display:flex;

    align-items:flex-end;

    justify-content:space-between;

    gap:10px;

    height:184px;

    padding:12px 8px 0;

    margin-top:14px;

    border-bottom:1px solid #e5eafa;

    background:repeating-linear-gradient(to top,transparent 0,transparent 44px,#edf0f8 45px,#edf0f8 46px)

}

.trend-col {

    flex:1;

    min-width:0;

    display:flex;

    flex-direction:column;

    align-items:center;

    justify-content:flex-end;

    height:100%;

    position:relative

}

.trend-stack {

    width:min(42px,90%);

    min-height:0;

    display:flex;

    flex-direction:column-reverse;

    overflow:hidden;

    border-radius:7px 7px 0 0;

    transition:filter .2s,transform .2s;

    box-shadow:0 3px 9px #6050c01c

}

.trend-col:hover .trend-stack {

    filter:brightness(1.08);

    transform:scaleX(1.08)

}

.trend-segment {

    width:100%;

    min-height:0

}

.trend-total {

    font-size:10px;

    color:#65708f;

    font-weight:800;

    margin-bottom:6px

}

.trend-label {

    font-size:10px;

    color:#8e9bb6;

    margin-top:10px;

    text-align:center

}

.trend-empty {

    color:#96a1b9;

    font-size:12px;

    text-align:center;

    padding:45px 10px

}

.chart-note {

    font-size:10px;

    color:#a0abc1;

    line-height:1.6;

    margin-top:16px

}

@media(max-width:1100px) {

    .charts {

        grid-template-columns:1fr

    }

}

@media(max-width:700px) {

    .donut {

        width:140px;

        height:140px

    }

    .donut::after {

        inset:24px

    }

    .charts {

        gap:12px

    }

    .chart-panel {

        min-height:0

    }

    .trend-chart {

        gap:5px

    }

}

/* Stable, readable metric numerals on desktop, laptop and mobile. */
.stat-value,.guard-counter strong,.status-result {
    font-family:'Plus Jakarta Sans',Arial,sans-serif;
    font-variant-numeric:lining-nums tabular-nums;
    font-feature-settings:'lnum' 1,'tnum' 1;
    font-style:normal;
    text-shadow:none;
}

@media(prefers-reduced-motion:reduce) {

    .stat,.panel,.trend-stack,.counts span {

        transition:none!important

    }

}

/* V3 – saturated accents while preserving Chat typography and existing PHP data */

:root {

    --purple:#6550ee;

    --ink:#191b43;

    --line:#e4e5f7

}

.content {

    background:linear-gradient(180deg,#f8f7ff 0%,#ffffff 45%);

}

.intro {

    position:relative;

    isolation:isolate;

    overflow:hidden;

    background:linear-gradient(118deg,#4030b8 0%,#6b4ef0 57%,#9870fa 100%);

    border-radius:22px;

    padding:27px 30px;

    margin-bottom:22px;

    box-shadow:0 15px 35px rgba(91,66,210,.25);

    color:#fff;

    align-items:center

}

.intro:before {

    content:'';

    position:absolute;

    right:-55px;

    top:-95px;

    width:310px;

    height:310px;

    border:55px solid rgba(255,255,255,.075);

    border-radius:50%;

    z-index:-1;

}

.intro:after {

    content:'';

    position:absolute;

    right:26%;

    bottom:-115px;

    width:240px;

    height:240px;

    background:radial-gradient(circle,rgba(255,255,255,.13),transparent 72%);

    z-index:-1;

}

.intro .eyebrow {

    color:#e1d9ff;

    letter-spacing:1.4px;

}

.intro h1 {

    color:white;

    font-size:29px

}

.intro p {

    color:#eeeaff;

    font-size:12px;

    max-width:580px

}

.refresh {

    color:#fff;

    border:1px solid rgba(255,255,255,.42);

    background:rgba(255,255,255,.14);

    backdrop-filter:blur(8px);

    transition:transform .2s,background .2s

}

.refresh:hover {

    color:#fff;

    background:rgba(255,255,255,.27);

    transform:translateY(-2px)

}

.stats {

    gap:15px;

    margin-bottom:19px

}

.stat {

    overflow:hidden;

    padding:20px 19px;

    border-width:1px;

    box-shadow:0 9px 20px rgba(67,56,150,.08);

    transition:transform .22s,box-shadow .22s,border-color .22s,filter .22s

}

.stat:before {

    z-index:0;

    background:radial-gradient(circle at 100% 0%,rgba(255,255,255,.7),transparent 65%)

}

.stat>* {

    position:relative;

    z-index:1

}

.stat:nth-child(1) {

    background:linear-gradient(130deg,#d7f8e9,#f0fff8 90%);

    border-color:#9ce6c5

}

.stat:nth-child(2) {

    background:linear-gradient(130deg,#e5dcff,#f5f0ff 90%);

    border-color:#cbbaff

}

.stat:nth-child(3) {

    background:linear-gradient(130deg,#dceaff,#f0f7ff 90%);

    border-color:#b9d3ff

}

.stat:nth-child(4) {

    background:linear-gradient(130deg,#ffe0e7,#fff3f5 90%);

    border-color:#ffbccb

}

.stat:nth-child(1) .stat-value {

    color:#087e5b

}

.stat:nth-child(2) .stat-value {

    color:#6a43df

}

.stat:nth-child(3) .stat-value {

    color:#2869cc

}

.stat:nth-child(4) .stat-value {

    color:#ce3c65

}

.stat-label {

    font-size:11px;

    color:#475275

}

.stat-value {

    font-size:29px;

    margin:13px 0 5px

}

.stat-hint {

    color:#64708f

}

.stat:hover {

    transform:translateY(-7px);

    box-shadow:0 17px 35px rgba(87,69,190,.20);

    filter:saturate(1.15)

}

.panel {

    background:#fff;

    border-color:#dedff6;

    box-shadow:0 8px 22px rgba(67,56,150,.065);

    transition:transform .22s,box-shadow .22s,border-color .22s

}

.panel:hover {

    border-color:#bcb0ff;

    box-shadow:0 16px 32px rgba(96,76,203,.13)

}

.panels>.panel:first-child {

    border-top:4px solid #6e54ec;

    background:linear-gradient(180deg,#f7f4ff,#fff 31%)

}

.panels>.panel:nth-child(2) {

    border-top:4px solid #20b78e;

    background:linear-gradient(180deg,#f2fffa,#fff 31%)

}

.chart-panel:first-child {

    border-top:4px solid #7961f1;

    background:linear-gradient(180deg,#f8f6ff,#fff 29%)

}

.chart-panel:nth-child(2) {

    border-top:4px solid #4387e9;

    background:linear-gradient(180deg,#f4f9ff,#fff 29%)

}

.audit {

    border-top:4px solid #f28a65;

    background:linear-gradient(180deg,#fff8f4,#fff 23%)

}

.panel h2 {

    font-size:14px

}

.setting {

    transition:background .2s,padding .2s

}

.setting:hover {

    background:#f2efff;

    padding-left:9px;

    padding-right:9px;

    border-radius:9px

}

.matrix tbody tr {

    transition:background .2s

}

.matrix tbody tr:hover {

    background:#effaf6

}

.matrix .check {

    color:#139a76;

    font-size:14px

}

.flag.on {

    background:#dcf7e9;

    color:#087b5b

}

.flag.off {

    background:#fff0e1;

    color:#b56816

}

.counts span {

    background:#eeeaff;

    color:#5a42bd;

    border-color:#dcd2ff

}

.counts span:hover {

    background:#ded6ff

}

.log-state {

    background:#eeeaff;

    color:#5745b2

}

.logs tbody tr:hover {

    background:#f2efff

}

.nav a.active {

    background:linear-gradient(100deg,#e3dcff,#eeeaff);

    box-shadow:inset 3px 0 #6950f1

}

.nav a:hover {

    background:#e5e0ff;

    color:#5740dc

}

.profile-trigger:hover {

    border-color:#b8a9ff;

    box-shadow:0 7px 17px rgba(94,75,205,.14)

}

.donut {

    box-shadow:0 13px 28px rgba(91,70,194,.16)

}

@media(max-width:700px) {

    .intro {

        padding:22px 19px;

        border-radius:17px

    }

    .intro h1 {

        font-size:24px

    }

    .stat-value {

        font-size:25px

    }

    .stats {

        gap:10px

    }

}

@media(prefers-reduced-motion:reduce) {

    .refresh,.setting,.matrix tbody tr,.stat,.panel {

        transition:none!important

    }

}


/* ===== Security Status: bổ sung, không ghi đè các khối dashboard cũ ===== */
.status-section{margin-top:18px}
.status-section h2{margin:0 0 14px;font-size:14px;font-weight:800}
.status-sub{font-size:11px;line-height:1.65;color:#8490aa;margin:4px 0 15px}
.status-summary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:17px 0}
.status-summary .status-tile{border:1px solid #e5e1fa;background:linear-gradient(145deg,#f8f6ff,#fff);border-radius:14px;padding:17px}
.status-tile .status-kicker{font-size:10px;color:#66738f;font-weight:800;letter-spacing:.6px}
.status-tile .status-result{font-size:19px;font-weight:800;margin-top:10px;overflow-wrap:anywhere;color:#5742c4}
.status-tile .status-result.good{color:#098765}.status-tile .status-result.bad{color:#d34b62}.status-tile .status-result.warn{color:#bd781b}
.guard-counters{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:11px}
.guard-counter{border:1px solid #e6e9f4;border-radius:12px;padding:15px;background:#fff}
.guard-counter small{display:block;font-size:10px;font-weight:800;color:#73809b}.guard-counter strong{display:block;font-size:24px;margin-top:8px;color:#453e92}
.status-grid{display:grid;grid-template-columns:1fr 1fr;gap:17px;margin-top:18px}
.status-row{display:flex;align-items:center;justify-content:space-between;gap:10px;border-bottom:1px solid #edf0f7;padding:12px 0;font-size:11px}
.status-row:last-child{border-bottom:0}
.status-pill{display:inline-block;border-radius:7px;padding:6px 9px;font-size:10px;font-weight:800;background:#f0efff;color:#5742c4;white-space:nowrap}
.status-pill.high,.status-pill.block{background:#fff0f2;color:#c93351}.status-pill.medium,.status-pill.redact{background:#fff4df;color:#a86d11}.status-pill.pass{background:#e8faf3;color:#07855d}
.status-alert{width:100%;text-align:left;display:flex;justify-content:space-between;align-items:center;gap:8px;border:1px solid #ebe8f6;border-radius:10px;background:#fbfaff;padding:12px;margin-bottom:9px;color:#37435d;font-size:11px;cursor:pointer}
.status-alert:hover{background:#f1efff}
.status-empty{padding:20px;text-align:center;color:#95a0b6;font-size:11px}
.status-modal[hidden]{display:none}.status-modal{position:fixed;inset:0;z-index:9999;background:rgba(20,18,48,.6);display:flex;align-items:center;justify-content:center;padding:18px}
.status-modal-dialog{background:#fff;border-radius:17px;width:min(520px,100%);padding:25px;box-shadow:0 22px 55px #14123055}
.status-modal-dialog h2{font-size:18px;margin:0 0 12px}.status-modal-dialog p{font-size:12px;line-height:1.7;color:#53617c;overflow-wrap:anywhere}
.status-modal-close{border:0;background:#6550ee;color:white;padding:10px 18px;border-radius:9px;cursor:pointer;font-size:12px;font-weight:700}
@media(max-width:850px){.status-grid{grid-template-columns:1fr}.status-summary{grid-template-columns:1fr 1fr}.guard-counters{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:450px){.status-summary{grid-template-columns:1fr}}


/* Final responsive and visual refinements – preserve Plus Jakarta Sans. */
.stats{grid-template-columns:repeat(5,minmax(0,1fr));gap:12px}
.stat:nth-child(1){background:linear-gradient(145deg,#e9fbf4,#fff 78%);border-color:#c9efdf}
.stat:nth-child(2){background:linear-gradient(145deg,#f0ecff,#fff 78%);border-color:#ddd4ff}
.stat:nth-child(3){background:linear-gradient(145deg,#edf4ff,#fff 78%);border-color:#d4e3ff}
.stat:nth-child(4){background:linear-gradient(145deg,#fff2df,#fff 78%);border-color:#ffdfb6}
.stat:nth-child(5){background:linear-gradient(145deg,#ffeaf0,#fff 78%);border-color:#ffcbd8}
.stat-blocked .stat-value{color:#d97706}.stat-denied .stat-value,.red{color:#e04468}
.stat{box-shadow:0 8px 22px rgba(71,76,140,.07)}
.panel{box-shadow:0 8px 24px rgba(71,76,140,.055)}
.panels>.panel:first-child{border-top:4px solid #7058ed}
.panels>.panel:nth-child(2){border-top:4px solid #2eaf91}
.chart-panel:first-child{border-top:4px solid #745cf1}
.chart-panel:nth-child(2){border-top:4px solid #4597df}
.audit{border-top:4px solid #f2a04f}
.legend-item:nth-child(1) .legend-dot{background:#17b68d!important}
.legend-item:nth-child(2) .legend-dot{background:#7d68f6!important}
.legend-item:nth-child(3) .legend-dot{background:#f59c53!important}
.legend-item:nth-child(4) .legend-dot{background:#ee647d!important}
.legend-item:nth-child(5) .legend-dot{background:#aab4c8!important}
.status-summary .status-tile:nth-child(1){background:linear-gradient(135deg,#edf4ff,#fff);border-color:#d6e3ff}
.status-summary .status-tile:nth-child(2){background:linear-gradient(135deg,#f1edff,#fff);border-color:#ded5ff}
.status-summary .status-tile:nth-child(3){background:linear-gradient(135deg,#eafaf4,#fff);border-color:#ccefe0}
.guard-counter:nth-child(1){background:#eafaf3;border-color:#c8efdd}
.guard-counter:nth-child(2){background:#f1edff;border-color:#ddd4ff}
.guard-counter:nth-child(3){background:#fff3e3;border-color:#ffdfb9}
.guard-counter:nth-child(4){background:#ffeaf0;border-color:#ffcbd8}
.guard-counter:nth-child(5){background:#f3f5fa;border-color:#e1e6f0}
.status-pill.blocked{background:#fff0dc;color:#b96a0c}
.status-pill.denied{background:#ffe7ed;color:#c42e55}
.status-pill.redacted,.status-pill.redact{background:#eee9ff;color:#6548cb}
.status-pill.pass,.status-pill.good{background:#e4f8ef;color:#087e5b}
.logs .flag{background:#f0efff;color:#5c4bd1}
.logs tr:has(.flag){transition:background .18s}
.logs tr:has(.flag):hover{background:#f7f5ff}
.table-wrap{max-width:100%}
.donut{background-color:#eef0fa}
.trend-stack{background:#f1f3fb}
button:focus-visible,a:focus-visible{outline:3px solid rgba(98,82,236,.35);outline-offset:3px}
@media(min-width:1500px){.app{width:min(1480px,100%)}.content{padding:38px clamp(28px,3vw,48px) 44px}}
@media(max-width:1200px){.sidebar{width:245px}.stats{grid-template-columns:repeat(3,minmax(0,1fr))}.charts{grid-template-columns:1fr 1fr}}
@media(max-width:900px){body{padding:12px}.app{min-height:calc(100vh - 24px)}.sidebar{width:215px;padding:17px 12px}.topbar{padding:0 18px}.content{padding:25px 20px}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.panels,.charts,.status-grid{grid-template-columns:1fr}}
@media(max-width:640px){body{padding:0}.app{display:block;min-height:100vh;border-radius:0}.sidebar{width:100%;min-height:auto;padding:12px 14px;border-right:0;border-bottom:1px solid var(--line)}.mac{display:none}.brand{margin:0 3px 12px}.nav-caption{margin:5px 4px 8px}.nav{flex-direction:row;flex-wrap:wrap}.nav a{flex:1 1 auto;justify-content:center;padding:10px 9px;font-size:11px}.sidebar-spacer{display:none}.profile-wrap{margin-top:10px}.profile-menu{bottom:auto;top:calc(100% + 8px)}.topbar{height:auto;min-height:58px;padding:11px 14px;align-items:flex-start;flex-direction:column}.topbar-actions{width:100%;gap:6px}.content{padding:20px 13px 28px}.intro{margin-bottom:18px}.intro h1{font-size:23px}.intro p{font-size:11px}.stats{grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.stat{padding:14px 12px}.stat-value{font-size:21px}.stat-label{font-size:10px}.stat-hint{font-size:9px}.panel{padding:16px}.charts{gap:12px}.donut-layout{gap:15px}.donut{width:140px;height:140px}.donut::after{inset:23px}.donut-center strong{font-size:21px}.legend{min-width:130px}.trend-chart{gap:5px;padding-inline:2px}.trend-label{font-size:9px}.status-summary{grid-template-columns:1fr}.guard-counters{grid-template-columns:repeat(2,minmax(0,1fr))}.status-grid{grid-template-columns:1fr}.audit-head{align-items:flex-start}.logs{min-width:590px}}
@media(max-width:380px){.stats{grid-template-columns:1fr}.topbar-actions>*{font-size:9px}.donut-layout{justify-content:center}.legend{width:100%}.trend-total{font-size:8px}}
@media(prefers-reduced-motion:reduce){*,*::before,*::after{scroll-behavior:auto!important;animation:none!important;transition:none!important}}

</style>

</head>



<body>

<div class="app">

<aside class="sidebar">

  <div class="mac" aria-hidden="true"><i></i><i></i><i></i></div>

  <div class="brand"><div class="logo">AI</div><div><strong>ASSISTANT</strong><small>AI Assistant Data Protection Framework<br>for Schools</small></div></div>

  <div class="nav-caption">WORKSPACE</div>

  <nav class="nav" aria-label="Main navigation">

    <a href="index.php"><span class="nav-ico">💬</span>Chat AI</a>

    <a href="security.php" class="active" aria-current="page"><span class="nav-ico">🛡️</span>Security Dashboard</a>

    <a href="setup.php"><span class="nav-ico">⚙️</span>Settings</a>

  </nav>

  <div class="sidebar-spacer"></div>

  <div class="profile-wrap" id="profileWrap">

    <button type="button" class="profile-trigger" id="profileTrigger" aria-expanded="false" aria-controls="profileMenu">

      <span class="avatar"><?=esc(mb_substr((string)($user['full_name'] ?? 'Q'),0,1,'UTF-8'))?></span>

      <span class="profile-info"><strong><?=esc($user['full_name'] ?? 'Administrator')?></strong><small><?=esc($user['email'] ?? '')?></small></span>

      <span class="chevron" aria-hidden="true">⌃</span>

    </button>

    <div class="profile-menu" id="profileMenu" hidden>

      <div class="profile-head"><strong><?=esc($user['full_name'] ?? 'Administrator')?></strong><span><?=esc($user['email'] ?? '')?> · <?=esc($user['role'] ?? '')?></span></div>

      <a href="index.php">💬 &nbsp;Back to Chat AI</a>

      <a href="setup.php">⚙️ &nbsp;System Settings</a>

      <a class="logout" href="logout.php">↪ &nbsp;Sign Out</a>

    </div>

  </div>

</aside>

<div class="workspace">

<header class="topbar">

  <div class="topbar-left"><span class="top-dot"></span><span class="topbar-label">Security &amp; Monitoring</span></div>

  <div class="topbar-actions"><a class="outline-btn" href="index.php">💬 Chat AI</a><span class="role-badge"><?=esc($user['role'] ?? '')?></span><span class="mode-badge">✨ <?=esc($mode)?> mode</span></div>

</header>

<main class="content">

  <div class="intro"><div><div class="eyebrow">SECURITY MONITORING</div><h1>Security Dashboard</h1><p>Monitor AI protection settings, access permissions, security events, and audit activity.</p></div><a class="refresh" href="security.php">↻ Refresh Data</a></div>

  <section class="stats" aria-label="Security Overview">

    <div class="stat"><div class="stat-label">🛡️ RBAC Pre-Retrieval</div><div class="stat-value <?=$rbac?'green':'orange'?>"><?=$rbac?'ON':'OFF'?></div><div class="stat-hint">Server configuration</div></div>

    <div class="stat"><div class="stat-label">✨ Output Filter</div><div class="stat-value <?=$filter?'green':'orange'?>"><?=$filter?'ON':'OFF'?></div><div class="stat-hint">Server configuration</div></div>

    <div class="stat"><div class="stat-label">📋 Audit Events</div><div class="stat-value violet"><?=number_format($total)?></div><div class="stat-hint">Valid JSON records</div></div>

    <div class="stat stat-blocked"><div class="stat-label">⛔ Blocked Events</div><div class="stat-value orange"><?=number_format($counts['BLOCKED'])?></div><div class="stat-hint">Requests stopped by security controls</div></div>
    <div class="stat stat-denied"><div class="stat-label">🚫 Denied Requests</div><div class="stat-value red"><?=number_format($counts['DENIED'])?></div><div class="stat-hint">Requests rejected by access policy</div></div>

  </section>

  <section class="panels">

    <div class="panel"><h2>Protection Layer Status</h2><div class="setting"><span>Pre-retrieval access control</span><span class="flag <?=$rbac?'on':'off'?>"><?=$rbac?'ON':'OFF'?></span></div><div class="setting"><span>Output response filtering</span><span class="flag <?=$filter?'on':'off'?>"><?=$filter?'ON':'OFF'?></span></div><div class="setting"><span>System mode</span><strong><?=esc($mode)?></strong></div><p class="panel-sub">These indicators reflect configuration, not verified enforcement. Baseline mode is intended for testing only.</p></div>

    <div class="panel"><h2>RBAC Access Matrix</h2><table class="matrix"><thead><tr><th>Role</th><th>Public</th><th>Internal</th><th>Restricted</th></tr></thead><tbody><tr><td>SinhVien</td><td class="check">✓</td><td class="dash">—</td><td class="dash">—</td></tr><tr><td>GiangVien</td><td class="check">✓</td><td class="check">✓</td><td class="dash">—</td></tr><tr><td>QuanTri</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr></tbody></table><p class="panel-sub">Policy matrix. Document APIs must independently enforce authorization.</p></div>

  </section>

  <section class="charts" aria-label="Security audit charts">

    <div class="panel chart-panel">

      <div class="chart-title"><h2>Security Event Distribution</h2><span class="log-state">Actual audit data</span></div>

      <div class="chart-sub">Distribution of passed, redacted, blocked, and denied events across all readable audit records.</div>

      <div class="donut-layout">

        <div class="donut" style="background:<?=esc($donutGradient)?>" role="img" aria-label="Distribution chart for <?=number_format($total)?> events">

          <div class="donut-center"><strong><?=number_format($total)?></strong><small>Events</small></div>

        </div>

        <div class="legend">

          <?php foreach ($counts as $name=>$num): ?>

            <div class="legend-item"><span class="legend-name"><i class="legend-dot" style="background:<?=esc($palette[$name])?>"></i><?=esc($name)?></span><strong><?=number_format($num)?></strong></div>

          <?php endforeach; ?>

        </div>

      </div>

      <div class="chart-note"><?= $total === 0 ? 'No audit data is available. The chart is currently empty.' : 'Metrics are aggregated from the audit status field and do not represent model accuracy.' ?></div>

    </div>

    <div class="panel chart-panel">

      <div class="chart-title"><h2>7-Day Security Trend</h2><span class="log-state">Last 7 days</span></div>

      <div class="chart-sub">Daily event counts by status, based on timestamps recorded in the audit log.</div>

      <?php if ($dailyMax === 0): ?>

        <div class="trend-empty">No valid timestamped events were recorded in the last 7 days.</div>

      <?php else: ?>

        <div class="trend-chart" role="img" aria-label="Stacked security event counts over the last seven days">

          <?php foreach ($daily as $day=>$values): $dayTotal=array_sum($values); $height=($dayTotal/$dailyMax)*140; ?>

            <div class="trend-col" title="<?=esc($day)?>: <?=number_format($dayTotal)?> events">

              <div class="trend-total"><?= $dayTotal ? number_format($dayTotal) : '' ?></div>

              <div class="trend-stack" style="height:<?=round($height,2)?>px">

                <?php foreach ($values as $status=>$n): if ($n <= 0 || $dayTotal <= 0) continue; ?>

                  <div class="trend-segment" style="height:<?=round(100*$n/$dayTotal,3)?>%;background:<?=esc($palette[$status])?>" title="<?=esc($status)?>: <?=number_format($n)?>"></div>

                <?php endforeach; ?>

              </div>

              <div class="trend-label"><?=esc(date('d/m',strtotime($day)))?></div>

            </div>

          <?php endforeach; ?>

        </div>

      <?php endif; ?>

      <div class="chart-note">Days without records are shown as zero. No sample data is generated.</div>

    </div>

  </section>

  <section class="panel audit"><div class="audit-head"><h2>Security Audit Log · Recent Events</h2><span class="log-state"><?=esc($logState)?></span></div><div class="counts"><?php foreach($counts as $name=>$num): ?><span><?=esc($name)?>: <?=number_format($num)?></span><?php endforeach; ?></div><p class="panel-sub">Showing up to the 50 most recent events. Query content, document identifiers, and sensitive data are not exposed.</p><div class="table-wrap"><table class="logs"><thead><tr><th>Timestamp</th><th>Role</th><th>Status</th><th>Action</th><th>Latency (ms)</th></tr></thead><tbody><?php if (!$events): ?><tr><td colspan="5" class="empty">No valid audit records are available.</td></tr><?php else: foreach($events as $e): ?><tr><td><?=esc($e['time'] ?: '—')?></td><td><?=esc($e['role'])?></td><td><span class="flag status-pill <?=strtolower(esc($e['status']))?>"><?=esc($e['status'])?></span></td><td><?=esc($e['action'])?></td><td><?=is_numeric($e['latency'])?esc(round((float)$e['latency'],2)):'—'?></td></tr><?php endforeach; endif; ?></tbody></table></div><div class="footer-note">Data is aggregated from server logs. No synthetic metrics are generated.</div></section>


<!-- ===== SECURITY STATUS INTEGRATION: EXISTING DASHBOARD SECTIONS ARE PRESERVED ===== -->
<section class="status-section" aria-label="Security status monitoring">
  <div class="panel">
    <h2>🛡️ Security Status · Latest Control Results</h2>
    <p class="status-sub">Metrics are derived from configuration and actual audit records. N/A means there is insufficient evidence; it does not mean the system is secure.</p>
    <div class="status-summary">
      <div class="status-tile"><div class="status-kicker">ACCESS CONTROL</div><div class="status-result <?= $accessStatus==='DENIED'?'bad':'' ?>"><?=esc($accessStatus)?></div><p class="status-sub">The latest access result is shown only when the audit log provides explicit evidence.</p></div>
      <div class="status-tile"><div class="status-kicker">OUTPUT FILTER</div><div class="status-result <?= $filterStatus==='PASS'?'good':(in_array($filterStatus,['BLOCKED','DENIED'],true)?'bad':'warn') ?>"><?=esc($filterStatus)?></div><p class="status-sub">The recorded post-processing action is shown without inferring behavior from the response.</p></div>
      <div class="status-tile"><div class="status-kicker">PIPELINE STATUS</div><div class="status-result"><?=esc($pipelineStatus)?></div><p class="status-sub">The presence of logs does not prove that the pipeline is online or fully operational.</p></div>
    </div>
    <div class="status-row"><span>Current system mode</span><span class="status-pill"><?=esc($mode)?></span></div>
    <div class="status-row"><span>RBAC Pre-Retrieval</span><span class="status-pill <?= $rbac?'pass':'medium' ?>"><?= $rbac?'ON':'OFF' ?></span></div>
    <div class="status-row"><span>Output Filter</span><span class="status-pill <?= $filter?'pass':'medium' ?>"><?= $filter?'ON':'OFF' ?></span></div>
  </div>
</section>
<section class="panel status-section" aria-label="Output Guardrails counters">
  <h2>✨ Output Guardrails · Last 50 Records</h2>
  <p class="status-sub">Counters are classified from the status/action_taken fields of the 50 most recent events, not the system-wide total.</p>
  <div class="guard-counters">
    <?php foreach ($guardCounts as $label=>$number): ?>
    <div class="guard-counter"><small><?=esc($label)?></small><strong><?=number_format($number)?></strong></div>
    <?php endforeach; ?>
  </div>
</section>
<div class="status-grid">
  <section class="panel" aria-label="Security alerts">
    <h2>🚨 Security Alerts</h2>
    <p class="status-sub">Alerts are derived from BLOCKED, DENIED, and REDACTED audit events. Root causes are not inferred when logs lack details.</p>
    <?php if (!$securityAlerts): ?>
      <div class="status-empty">No BLOCKED, DENIED, or REDACTED alerts were found in the 50 most recent events.</div>
    <?php else: foreach(array_slice($securityAlerts,0,8) as $alert): ?>
      <button type="button" class="status-alert" data-alert='<?=esc(json_encode($alert,JSON_UNESCAPED_UNICODE|JSON_INVALID_UTF8_SUBSTITUTE))?>'>
        <span><?=esc($alert['label'])?><br><small><?=esc($alert['time'] ?: 'No timestamp')?> · <?=esc($alert['role'])?></small></span>
        <span class="status-pill <?=strtolower($alert['level'])?>"><?=esc($alert['level'])?></span>
      </button>
    <?php endforeach; endif; ?>
  </section>
  <section class="panel" aria-label="Control history">
    <h2>📜 Recent Control History</h2>
    <p class="status-sub">Query content, document contents, and identifying information are not displayed.</p>
    <?php if (!$statusHistory): ?>
      <div class="status-empty">No valid records are available.</div>
    <?php else: foreach(array_slice($statusHistory,0,8) as $item): ?>
      <div class="status-row"><span><?=esc($item['time'] ?: 'No timestamp')?><br><small><?=esc($item['role'])?> · <?=esc($item['action'] ?: $item['status'])?></small></span><span class="status-pill <?=strtolower($item['guard'])?>"><?=esc($item['guard'])?></span></div>
    <?php endforeach; endif; ?>
  </section>
</div>
<div class="status-modal" id="securityStatusModal" hidden role="dialog" aria-modal="true" aria-labelledby="securityStatusModalTitle">
  <div class="status-modal-dialog">
    <h2 id="securityStatusModalTitle">Alert Details</h2>
    <p id="securityStatusModalMeta"></p>
    <p id="securityStatusModalDetail"></p>
    <button type="button" class="status-modal-close" id="securityStatusModalClose">Close</button>
  </div>
</div>
<!-- ===== END OF SECURITY STATUS ===== -->

</main>

</div></div>

<script>

(function(){

 const trigger=document.getElementById('profileTrigger');

 const menu=document.getElementById('profileMenu');

 const wrap=document.getElementById('profileWrap');

 function setOpen(open){menu.hidden=!open;trigger.setAttribute('aria-expanded',String(open));}

 trigger.addEventListener('click',function(){setOpen(menu.hidden);});

 document.addEventListener('click',function(event){if(!wrap.contains(event.target))setOpen(false);});

 document.addEventListener('keydown',function(event){if(event.key==='Escape'){setOpen(false);trigger.focus();}});

})();

</script>


<script>
// Read-only modal; no API polling, no Chat/RAG invocation, no role mutation.
(function(){
  const modal=document.getElementById('securityStatusModal');
  const close=document.getElementById('securityStatusModalClose');
  if(!modal||!close)return;
  function hide(){modal.hidden=true;}
  document.querySelectorAll('[data-alert]').forEach(function(btn){
    btn.addEventListener('click',function(){
      try {
        const alert=JSON.parse(btn.getAttribute('data-alert'));
        document.getElementById('securityStatusModalMeta').textContent=
          'Role: '+(alert.role||'—')+' · Severity: '+(alert.level||'—')+' · Timestamp: '+(alert.time||'—');
        document.getElementById('securityStatusModalDetail').textContent=alert.detail||'No additional details available.';
        modal.hidden=false;
        close.focus();
      } catch(e) { /* Invalid log-derived payload; do not render */ }
    });
  });
  close.addEventListener('click',hide);
  modal.addEventListener('click',function(e){if(e.target===modal)hide();});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!modal.hidden)hide();});
})();
</script>

</body></html>
