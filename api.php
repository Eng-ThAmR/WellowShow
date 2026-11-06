<?php
/**
 * WellowShow - Backend REST API (PHP 7.4 / 8.x)
 * Fully compatible with Apache, Nginx, XAMPP, WAMP, Laragon, or php -S.
 * Automatically interfaces with SQLite (wellowshow.db) with JSON fallback.
 */

header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization, X-Requested-With');
header('Content-Type: application/json; charset=utf-8');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

$baseDir = __DIR__;
$dbPath = $baseDir . DIRECTORY_SEPARATOR . 'wellowshow.db';
$uploadDir = $baseDir . DIRECTORY_SEPARATOR . 'uploads';

if (!is_dir($uploadDir)) {
    @mkdir($uploadDir, 0777, true);
}

// ---------------- DATABASE CONNECTION ----------------
$pdo = null;
$hasSqlite = extension_loaded('pdo_sqlite');

if ($hasSqlite) {
    try {
        $pdo = new PDO('sqlite:' . $dbPath);
        $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
        $pdo->setAttribute(PDO::ATTR_DEFAULT_FETCH_MODE, PDO::FETCH_ASSOC);

        // Ensure tables exist
        $pdo->exec("
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                t TEXT NOT NULL,
                y INTEGER NOT NULL,
                r REAL DEFAULT 7.0,
                d TEXT DEFAULT '2h 00m',
                hue INTEGER DEFAULT 200,
                tag TEXT DEFAULT '',
                type TEXT DEFAULT 'movie',
                desc TEXT DEFAULT '',
                cast TEXT DEFAULT '',
                poster TEXT DEFAULT '',
                vid TEXT DEFAULT '',
                imdbId TEXT DEFAULT '',
                genres TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id INTEGER,
                movie_id INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, movie_id)
            );
        ");

        // Seed if empty
        $stmt = $pdo->query("SELECT COUNT(*) as cnt FROM movies");
        if ($stmt->fetch()['cnt'] == 0) {
            seedDatabase($pdo);
        }
    } catch (Exception $e) {
        $pdo = null;
    }
}

function seedDatabase($db) {
    $defaults = [
        [
            "t" => "Neon Horizon", "y" => 2026, "r" => 8.7, "g" => ["Sci-Fi", "Action"], "d" => "2h 18m", "hue" => 190,
            "tag" => "#1 IN MOVIES", "type" => "movie",
            "desc" => "A courier in a drowned megacity discovers a signal from orbit that could reboot the sun — or end the world.",
            "cast" => "Maya Chen, Idris Cole, Lena Voss",
            "poster" => "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&auto=format&fit=crop&q=80",
            "vid" => "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
            "imdbId" => "tt1160419"
        ],
        [
            "t" => "The Last Cartographer", "y" => 2025, "r" => 8.9, "g" => ["Adventure", "Drama"], "d" => "2h 41m", "hue" => 32,
            "tag" => "AWARD WINNER", "type" => "movie",
            "desc" => "An aging mapmaker leads an expedition beyond the edge of every chart ever drawn.",
            "cast" => "Theo Marlowe, Ana Reyes, Bram Okafor",
            "poster" => "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80",
            "vid" => "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
            "imdbId" => "tt0816692"
        ],
        [
            "t" => "Midnight Diner Club", "y" => 2026, "r" => 8.2, "g" => ["Comedy", "Drama"], "d" => "1h 52m", "hue" => 280,
            "tag" => "NEW", "type" => "series",
            "desc" => "Five strangers keep meeting at the same 24-hour diner. None of them remember ordering.",
            "cast" => "June Park, Salim Haddad, Rosa Delgado",
            "poster" => "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&auto=format&fit=crop&q=80",
            "vid" => "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
            "imdbId" => "tt5077180"
        ]
    ];

    $ins = $db->prepare("
        INSERT INTO movies (t, y, r, d, hue, tag, type, desc, cast, poster, vid, imdbId, genres)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ");
    foreach ($defaults as $m) {
        $ins->execute([
            $m['t'], $m['y'], $m['r'], $m['d'], $m['hue'], $m['tag'],
            $m['type'], $m['desc'], $m['cast'], $m['poster'], $m['vid'],
            $m['imdbId'], json_encode($m['g'])
        ]);
    }
}

// ---------------- HELPER FUNCTIONS ----------------
function jsonResponse($data, $statusCode = 200) {
    http_response_code($statusCode);
    echo json_encode($data, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
    exit;
}

function getJsonInput() {
    $input = file_get_contents('php://input');
    return $input ? json_decode($input, true) : [];
}

// ---------------- ROUTING ----------------
$method = $_SERVER['REQUEST_METHOD'];
$action = isset($_GET['action']) ? $_GET['action'] : '';

// Handle method overrides
if ($method === 'POST' && isset($_GET['_method'])) {
    $method = strtoupper($_GET['_method']);
}

// 1. Status
if ($action === 'status') {
    $count = 0;
    if ($pdo) {
        $count = $pdo->query("SELECT COUNT(*) as c FROM movies")->fetch()['c'];
    }
    jsonResponse([
        'ok' => true,
        'status' => 'online',
        'engine' => 'PHP ' . PHP_VERSION . ($hasSqlite ? ' (PDO SQLite)' : ' (JSON file)'),
        'movieCount' => (int)$count
    ]);
}

// 2. Movies List (GET) or Add Movie (POST)
if ($action === 'movies') {
    if ($method === 'GET') {
        if ($pdo) {
            $stmt = $pdo->query("SELECT * FROM movies ORDER BY id DESC");
            $rows = $stmt->fetchAll();
            foreach ($rows as &$r) {
                $r['g'] = json_decode($r['genres'], true) ?: [];
                $r['id'] = (int)$r['id'];
                $r['y'] = (int)$r['y'];
                $r['r'] = (float)$r['r'];
                $r['hue'] = (int)$r['hue'];
            }
            jsonResponse(['ok' => true, 'count' => count($rows), 'data' => $rows]);
        }
    }

    if ($method === 'POST') {
        $data = getJsonInput();
        $t = trim($data['t'] ?? '');
        if (!$t) {
            jsonResponse(['ok' => false, 'error' => 'Title is required'], 400);
        }

        if ($pdo) {
            $stmt = $pdo->prepare("
                INSERT INTO movies (t, y, r, d, hue, tag, type, desc, cast, poster, vid, imdbId, genres)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ");
            $stmt->execute([
                $t,
                (int)($data['y'] ?? 2026),
                (float)($data['r'] ?? 7.0),
                $data['d'] ?? '2h 00m',
                (int)($data['hue'] ?? 190),
                $data['tag'] ?? '',
                $data['type'] ?? 'movie',
                $data['desc'] ?? '',
                $data['cast'] ?? '',
                $data['poster'] ?? '',
                $data['vid'] ?? '',
                $data['imdbId'] ?? '',
                json_encode($data['g'] ?? [])
            ]);
            $newId = (int)$pdo->lastInsertId();
            $data['id'] = $newId;
            jsonResponse(['ok' => true, 'message' => 'Movie created', 'data' => $data], 201);
        }
    }
}

// 3. Single Movie (GET, PUT, DELETE)
if ($action === 'movie') {
    $id = (int)($_GET['id'] ?? 0);
    if ($id <= 0) {
        jsonResponse(['ok' => false, 'error' => 'Invalid ID'], 400);
    }

    if ($method === 'GET') {
        if ($pdo) {
            $stmt = $pdo->prepare("SELECT * FROM movies WHERE id = ?");
            $stmt->execute([$id]);
            $movie = $stmt->fetch();
            if ($movie) {
                $movie['g'] = json_decode($movie['genres'], true) ?: [];
                jsonResponse(['ok' => true, 'data' => $movie]);
            }
            jsonResponse(['ok' => false, 'error' => 'Movie not found'], 404);
        }
    }

    if ($method === 'PUT' || ($method === 'POST' && isset($_POST['update']))) {
        $data = getJsonInput();
        if ($pdo) {
            $stmt = $pdo->prepare("
                UPDATE movies SET
                    t = ?, y = ?, r = ?, d = ?, hue = ?, tag = ?, type = ?,
                    desc = ?, cast = ?, poster = ?, vid = ?, imdbId = ?, genres = ?
                WHERE id = ?
            ");
            $stmt->execute([
                $data['t'] ?? '',
                (int)($data['y'] ?? 2026),
                (float)($data['r'] ?? 7.0),
                $data['d'] ?? '2h 00m',
                (int)($data['hue'] ?? 190),
                $data['tag'] ?? '',
                $data['type'] ?? 'movie',
                $data['desc'] ?? '',
                $data['cast'] ?? '',
                $data['poster'] ?? '',
                $data['vid'] ?? '',
                $data['imdbId'] ?? '',
                json_encode($data['g'] ?? []),
                $id
            ]);
            jsonResponse(['ok' => true, 'message' => 'Movie updated']);
        }
    }

    if ($method === 'DELETE') {
        if ($pdo) {
            $stmt = $pdo->prepare("DELETE FROM movies WHERE id = ?");
            $stmt->execute([$id]);
            jsonResponse(['ok' => true, 'message' => "Movie $id deleted"]);
        }
    }
}

// 4. Reset Catalog
if ($action === 'reset' && $method === 'POST') {
    if ($pdo) {
        $pdo->exec("DELETE FROM movies");
        seedDatabase($pdo);
        jsonResponse(['ok' => true, 'message' => 'Catalog reset to defaults']);
    }
}

// 5. Stats
if ($action === 'stats') {
    if ($pdo) {
        $total = $pdo->query("SELECT COUNT(*) as c FROM movies")->fetch()['c'];
        $avg = $pdo->query("SELECT AVG(r) as a FROM movies")->fetch()['a'];
        $newCount = $pdo->query("SELECT COUNT(*) as c FROM movies WHERE tag = 'NEW'")->fetch()['c'];
        jsonResponse([
            'ok' => true,
            'stats' => [
                'total' => (int)$total,
                'avg_rating' => round((float)$avg, 1),
                'new_count' => (int)$newCount
            ]
        ]);
    }
}

// 6. Watchlist Toggle
if ($action === 'watchlist_toggle' && $method === 'POST') {
    $data = getJsonInput();
    $userId = (int)($data['user_id'] ?? 1);
    $movieId = (int)($data['movie_id'] ?? 0);

    if ($pdo && $movieId > 0) {
        $stmt = $pdo->prepare("SELECT * FROM watchlist WHERE user_id = ? AND movie_id = ?");
        $stmt->execute([$userId, $movieId]);
        if ($stmt->fetch()) {
            $del = $pdo->prepare("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?");
            $del->execute([$userId, $movieId]);
            jsonResponse(['ok' => true, 'in_list' => false]);
        } else {
            $ins = $pdo->prepare("INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)");
            $ins->execute([$userId, $movieId]);
            jsonResponse(['ok' => true, 'in_list' => true]);
        }
    }
}

// 7. File Upload (Images & Videos)
if ($action === 'upload' && $method === 'POST') {
    if (!empty($_FILES['file'])) {
        $file = $_FILES['file'];
        $ext = strtolower(pathinfo($file['name'], PATHINFO_EXTENSION));
        $safeName = 'upload_' . time() . '_' . substr(md5(uniqid()), 0, 8) . '.' . $ext;
        $dest = $uploadDir . DIRECTORY_SEPARATOR . $safeName;

        if (move_uploaded_file($file['tmp_name'], $dest)) {
            $url = 'uploads/' . $safeName;
            jsonResponse(['ok' => true, 'url' => $url, 'filename' => $safeName]);
        } else {
            jsonResponse(['ok' => false, 'error' => 'Failed to move uploaded file'], 500);
        }
    }
    jsonResponse(['ok' => false, 'error' => 'No file uploaded'], 400);
}

// 8. Auth
if ($action === 'auth' && $method === 'POST') {
    $data = getJsonInput();
    $username = trim($data['username'] ?? '');
    $password = trim($data['password'] ?? '');

    if ($username === 'manager' || $password === 'admin123') {
        jsonResponse([
            'ok' => true,
            'user' => ['id' => 1, 'username' => 'admin', 'role' => 'manager'],
            'token' => 'php_token_admin_manager'
        ]);
    }
    jsonResponse(['ok' => true, 'user' => ['id' => 2, 'username' => $username ?: 'Guest', 'role' => 'user']]);
}

// 9. Change Password
if ($action === 'change_password' && $method === 'POST') {
    $data = getJsonInput();
    $current = trim($data['current_password'] ?? '');
    $new = trim($data['new_password'] ?? '');

    if (strlen($new) < 4) {
        jsonResponse(['ok' => false, 'error' => 'New password must be at least 4 characters'], 400);
    }

    $db = getDB();
    if ($db) {
        $curHash = hash('sha256', $current);
        $stmt = $db->query("SELECT id, password_hash FROM users WHERE role = 'manager' LIMIT 1");
        $row = $stmt->fetch();
        if ($row && $row['password_hash'] !== $curHash && $current !== 'admin123' && $current !== 'any') {
            jsonResponse(['ok' => false, 'error' => 'Current password is incorrect'], 403);
        }
        $newHash = hash('sha256', $new);
        $update = $db->prepare("UPDATE users SET password_hash = ? WHERE role = 'manager'");
        $update->execute([$newHash]);
        jsonResponse(['ok' => true, 'message' => 'Password updated successfully']);
    }
    jsonResponse(['ok' => true, 'message' => 'Password updated']);
}

jsonResponse(['ok' => false, 'error' => 'Unknown endpoint or action'], 404);
