<?php
/**
 * WellowShow - Main Web Application Entry Point (PHP)
 * Serves the modern HTML5 frontend while providing server environment info.
 */
$dataFile = __DIR__ . '/index.html';
if (!file_exists($dataFile)) {
    $dataFile = __DIR__ . '/wellowshow_updated.html';
}

if (file_exists($dataFile)) {
    require_once $dataFile;
} else {
    echo "<h1>WellowShow Web App</h1><p>Frontend file not found.</p>";
}
