<?php
declare(strict_types=1);

/** Locate the backend beside assistant/ or one level above its web folder. */
function attt_project_root(): ?string {
    $webRoot = dirname(__DIR__);
    foreach ([$webRoot, dirname($webRoot)] as $candidate) {
        if (is_file($candidate . '/src/main.py')) {
            return $candidate;
        }
    }
    return null;
}
