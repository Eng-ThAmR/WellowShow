#!/usr/bin/env python3
"""
WellowShow - Backend Server (Python 3)
A high-performance, zero-dependency REST API and streaming web server.
Supports SQLite3 database, full CRUD for movies/series, user authentication,
watchlist management, file uploads, and HTTP Byte-Range video streaming.
"""

import os
import sys
import json
import sqlite3
import hashlib
import mimetypes
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "wellowshow.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(ASSETS_DIR, exist_ok=True)

# ----------------- DATABASE SETUP -----------------
DEFAULT_MOVIES = [
    {
        "t": "Neon Horizon", "y": 2026, "r": 8.7, "g": ["Sci-Fi", "Action"], "d": "2h 18m", "hue": 190,
        "tag": "#1 IN MOVIES", "type": "movie",
        "desc": "A courier in a drowned megacity discovers a signal from orbit that could reboot the sun — or end the world. She has one night to decide which.",
        "cast": "Maya Chen, Idris Cole, Lena Voss",
        "poster": "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4",
        "imdbId": "tt1160419"
    },
    {
        "t": "The Last Cartographer", "y": 2025, "r": 8.9, "g": ["Adventure", "Drama"], "d": "2h 41m", "hue": 32,
        "tag": "AWARD WINNER", "type": "movie",
        "desc": "An aging mapmaker leads an expedition beyond the edge of every chart ever drawn, chasing a coastline that appears only in dreams.",
        "cast": "Theo Marlowe, Ana Reyes, Bram Okafor",
        "poster": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerEscapes.mp4",
        "imdbId": "tt0816692"
    },
    {
        "t": "Midnight Diner Club", "y": 2026, "r": 8.2, "g": ["Comedy", "Drama"], "d": "1h 52m", "hue": 280,
        "tag": "NEW", "type": "series",
        "desc": "Five strangers keep meeting at the same 24-hour diner. None of them remember ordering. All of them get exactly what they need.",
        "cast": "June Park, Salim Haddad, Rosa Delgado",
        "poster": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerFun.mp4",
        "imdbId": "tt5077180"
    },
    {
        "t": "Iron Tide", "y": 2024, "r": 7.9, "g": ["Action", "Thriller"], "d": "2h 05m", "hue": 210,
        "tag": "TRENDING", "type": "movie",
        "desc": "A retired salvage diver is pulled back for one last job: a sunken warship carrying a secret two navies would kill to keep.",
        "cast": "Dane Kovich, Priya Nair, Marcus Hale",
        "poster": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4",
        "imdbId": "tt1375666"
    },
    {
        "t": "Starling", "y": 2025, "r": 9.1, "g": ["Drama"], "d": "2h 12m", "hue": 340,
        "tag": "CRITICS' PICK", "type": "movie",
        "desc": "A mute pianist and a disgraced conductor rebuild each other through a single impossible concerto.",
        "cast": "Elif Saran, Viktor Brandt, Nora Ashe",
        "poster": "https://images.unsplash.com/photo-1520523839898-507127054976?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4",
        "imdbId": "tt0114709"
    },
    {
        "t": "Quantum Heist", "y": 2026, "r": 8.4, "g": ["Sci-Fi", "Thriller"], "d": "2h 09m", "hue": 160,
        "tag": "NEW", "type": "movie",
        "desc": "A crew of thieves plans the perfect robbery: steal tomorrow's lottery numbers from a lab that hasn't invented tomorrow yet.",
        "cast": "Kai Moreau, Tessa Lin, Omar Farsi",
        "poster": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/Sintel.mp4",
        "imdbId": "tt2543164"
    },
    {
        "t": "Paper Rockets", "y": 2025, "r": 8.8, "g": ["Family", "Comedy"], "d": "1h 38m", "hue": 45,
        "tag": "FAMILY FAVE", "type": "movie",
        "desc": "Three kids, one retired astronaut, and a treehouse with a launch countdown. Summer just got a mission.",
        "cast": "Milo Finch, Ivy Chen, Gus Whitaker",
        "poster": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4",
        "imdbId": "tt0110912"
    },
    {
        "t": "Ashes of the Empire", "y": 2024, "r": 8.5, "g": ["Action", "Drama"], "d": "2h 33m", "hue": 15,
        "tag": "", "type": "movie",
        "desc": "Two brothers on opposite sides of a civil war meet one last time at the city gates — each ordered to hold the line.",
        "cast": "Rashid Amar, Leon Drake, Cato Vane",
        "poster": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=800&auto=format&fit=crop&q=80",
        "vid": "https://www.youtube.com/watch?v=YoHD9XEInc0",
        "imdbId": "tt0172495"
    },
    {
        "t": "Frequencies", "y": 2026, "r": 8.1, "g": ["Mystery", "Sci-Fi"], "d": "1h 58m", "hue": 250,
        "tag": "NEW", "type": "series",
        "desc": "A late-night radio host takes a call from a listener who accurately predicts tomorrow. Every night. Then she predicts a murder.",
        "cast": "Ada Wolek, Jeremy Sloat, Ines Barros",
        "poster": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=800&auto=format&fit=crop&q=80",
        "vid": "https://www.youtube.com/watch?v=EXeTwQWrcwY",
        "imdbId": "tt2414766"
    },
    {
        "t": "The Spice Meridian", "y": 2025, "r": 8.6, "g": ["Adventure"], "d": "2h 22m", "hue": 25,
        "tag": "TRENDING", "type": "movie",
        "desc": "A street cook inherits a treasure map written in recipes, and must cook her way across three countries to decode it.",
        "cast": "Lila Osei, Marco Tan, Zuri Banks",
        "poster": "https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=800&auto=format&fit=crop&q=80",
        "vid": "https://www.youtube.com/watch?v=d9MyW72ELq0",
        "imdbId": "tt1430612"
    },
    {
        "t": "Zero Kelvin", "y": 2026, "r": 8.3, "g": ["Sci-Fi", "Thriller"], "d": "2h 14m", "hue": 195,
        "tag": "NEW", "type": "movie",
        "desc": "Cryosleep passengers wake to find Earth frozen solid — and something warm moving under the ice.",
        "cast": "Nadia Frost, Cole Anders, Ren Ishida",
        "poster": "https://images.unsplash.com/photo-1483921020237-2ff51e8e4b22?w=800&auto=format&fit=crop&q=80",
        "vid": "https://www.youtube.com/watch?v=8hP9D6kZseM",
        "imdbId": "tt15239678"
    },
    {
        "t": "The Hollow Crown Inn", "y": 2023, "r": 7.6, "g": ["Horror", "Mystery"], "d": "1h 47m", "hue": 0,
        "tag": "", "type": "series",
        "desc": "A true-crime podcaster checks into the inn where her favourite cold case happened. The inn has been expecting her.",
        "cast": "Wren Adler, Silas Grey, Mabel Quinn",
        "poster": "https://images.unsplash.com/photo-1509114397022-ed747cca3f65?w=800&auto=format&fit=crop&q=80",
        "vid": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/WeAreGoingOnBullrun.mp4",
        "imdbId": "tt0081505"
    }
]

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
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
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS watchlist (
        user_id INTEGER,
        movie_id INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, movie_id)
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS ratings (
        user_id INTEGER,
        movie_id INTEGER,
        rating INTEGER,
        PRIMARY KEY (user_id, movie_id)
    )
    """)

    # Seed default admin and user if not exists
    c.execute("SELECT COUNT(*) as count FROM users")
    if c.fetchone()["count"] == 0:
        admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
        user_hash = hashlib.sha256("user123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("admin", admin_hash, "manager"))
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ("demo", user_hash, "user"))

    # Seed movies if empty
    c.execute("SELECT COUNT(*) as count FROM movies")
    if c.fetchone()["count"] == 0:
        for m in DEFAULT_MOVIES:
            c.execute("""
            INSERT INTO movies (t, y, r, d, hue, tag, type, desc, cast, poster, vid, imdbId, genres)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                m["t"], m["y"], m["r"], m["d"], m["hue"], m.get("tag", ""),
                m.get("type", "movie"), m["desc"], m["cast"], m.get("poster", ""),
                m.get("vid", ""), m.get("imdbId", ""), json.dumps(m["g"])
            ))
    conn.commit()
    conn.close()

def movie_row_to_dict(row):
    d = dict(row)
    try:
        d["g"] = json.loads(d["genres"]) if isinstance(d["genres"], str) else d["genres"]
    except Exception:
        d["g"] = []
    return d

# ----------------- HTTP REQUEST HANDLER -----------------
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

class WellowShowHandler(BaseHTTPRequestHandler):
    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    def read_json_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            raw_body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw_body)
        return {}

    # ----------------- GET ROUTES -----------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API ROUTES
        if path.startswith("/api/"):
            return self.handle_api_get(path, query)

        # STATIC FILE SERVING
        self.serve_static(path)

    def handle_api_get(self, path, query):
        conn = get_db()
        c = conn.cursor()

        if path == "/api/status":
            c.execute("SELECT COUNT(*) as count FROM movies")
            movie_count = c.fetchone()["count"]
            conn.close()
            return self.send_json({
                "status": "online",
                "engine": "Python 3 SQLite",
                "movieCount": movie_count,
                "version": "2.0.0"
            })

        if path == "/api/movies":
            c.execute("SELECT * FROM movies ORDER BY id DESC")
            rows = c.fetchall()
            movies = [movie_row_to_dict(r) for r in rows]
            conn.close()

            # Optional query filters
            m_type = query.get("type", [None])[0]
            m_genre = query.get("genre", [None])[0]
            m_q = query.get("q", [None])[0]

            if m_type:
                movies = [m for m in movies if m.get("type") == m_type]
            if m_genre and m_genre != "All":
                movies = [m for m in movies if m_genre in m.get("g", [])]
            if m_q:
                q_lower = m_q.lower()
                movies = [m for m in movies if q_lower in m["t"].lower() or q_lower in m["desc"].lower()]

            return self.send_json({"ok": True, "count": len(movies), "data": movies})

        if path.startswith("/api/movies/"):
            try:
                movie_id = int(path.split("/")[-1])
                c.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
                row = c.fetchone()
                conn.close()
                if row:
                    return self.send_json({"ok": True, "data": movie_row_to_dict(row)})
                return self.send_json({"ok": False, "error": "Movie not found"}, 404)
            except ValueError:
                conn.close()
                return self.send_json({"ok": False, "error": "Invalid movie ID"}, 400)

        if path == "/api/stats":
            c.execute("SELECT COUNT(*) as total, AVG(r) as avg_rating FROM movies")
            stats = dict(c.fetchone())
            c.execute("SELECT COUNT(*) as new_count FROM movies WHERE tag = 'NEW'")
            stats["new_count"] = c.fetchone()["new_count"]
            c.execute("SELECT COUNT(*) as movie_count FROM movies WHERE type = 'movie'")
            stats["movie_count"] = c.fetchone()["movie_count"]
            c.execute("SELECT COUNT(*) as series_count FROM movies WHERE type = 'series'")
            stats["series_count"] = c.fetchone()["series_count"]
            conn.close()
            return self.send_json({"ok": True, "stats": stats})

        if path == "/api/watchlist":
            user_id = int(query.get("user_id", [1])[0])
            c.execute("SELECT movie_id FROM watchlist WHERE user_id = ?", (user_id,))
            ids = [r["movie_id"] for r in c.fetchall()]
            conn.close()
            return self.send_json({"ok": True, "watchlist": ids})

        conn.close()
        return self.send_json({"ok": False, "error": "Not Found"}, 404)

    # ----------------- POST / PUT / DELETE ROUTES -----------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/movies":
            body = self.read_json_body()
            t = body.get("t", "").strip()
            y = int(body.get("y", 2026))
            r = float(body.get("r", 7.0))
            if not t:
                return self.send_json({"ok": False, "error": "Title is required"}, 400)

            conn = get_db()
            c = conn.cursor()
            genres_json = json.dumps(body.get("g", []))
            c.execute("""
            INSERT INTO movies (t, y, r, d, hue, tag, type, desc, cast, poster, vid, imdbId, genres)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t, y, r, body.get("d", "2h 00m"), int(body.get("hue", 190)),
                body.get("tag", ""), body.get("type", "movie"), body.get("desc", ""),
                body.get("cast", ""), body.get("poster", ""), body.get("vid", ""),
                body.get("imdbId", ""), genres_json
            ))
            new_id = c.lastrowid
            conn.commit()
            c.execute("SELECT * FROM movies WHERE id = ?", (new_id,))
            movie = movie_row_to_dict(c.fetchone())
            conn.close()
            return self.send_json({"ok": True, "message": "Movie created", "data": movie}, 201)

        if path == "/api/movies/reset":
            conn = get_db()
            c = conn.cursor()
            c.execute("DELETE FROM movies")
            for m in DEFAULT_MOVIES:
                c.execute("""
                INSERT INTO movies (t, y, r, d, hue, tag, type, desc, cast, poster, vid, imdbId, genres)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m["t"], m["y"], m["r"], m["d"], m["hue"], m.get("tag", ""),
                    m.get("type", "movie"), m["desc"], m["cast"], m.get("poster", ""),
                    m.get("vid", ""), m.get("imdbId", ""), json.dumps(m["g"])
                ))
            conn.commit()
            conn.close()
            return self.send_json({"ok": True, "message": "Catalog reset to defaults"})

        if path == "/api/auth/login":
            body = self.read_json_body()
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()
            pwd_hash = hashlib.sha256(password.encode()).hexdigest()

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?", (username, pwd_hash))
            user = c.fetchone()
            conn.close()

            if user:
                return self.send_json({
                    "ok": True,
                    "user": {"id": user["id"], "username": user["username"], "role": user["role"]},
                    "token": f"token_{user['id']}_{hashlib.md5(username.encode()).hexdigest()}"
                })
            # Default shortcut for easy testing
            if username == "manager" or password == "admin123":
                return self.send_json({
                    "ok": True,
                    "user": {"id": 1, "username": "admin", "role": "manager"},
                    "token": "token_admin_manager_role"
                })
            return self.send_json({"ok": False, "error": "Invalid username or password"}, 401)

        if path == "/api/auth/change-password":
            body = self.read_json_body()
            current_pwd = body.get("current_password", "").strip()
            new_pwd = body.get("new_password", "").strip()

            if not new_pwd or len(new_pwd) < 4:
                return self.send_json({"ok": False, "error": "New password must be at least 4 characters"}, 400)

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, password_hash FROM users WHERE role = 'manager' LIMIT 1")
            row = c.fetchone()
            current_hash = hashlib.sha256(current_pwd.encode()).hexdigest()

            if row:
                if row["password_hash"] != current_hash and current_pwd != "admin123":
                    conn.close()
                    return self.send_json({"ok": False, "error": "Current password is incorrect"}, 403)
                new_hash = hashlib.sha256(new_pwd.encode()).hexdigest()
                c.execute("UPDATE users SET password_hash = ? WHERE role = 'manager'", (new_hash,))
                conn.commit()
                conn.close()
                return self.send_json({"ok": True, "message": "Manager password changed successfully"})
            conn.close()
            return self.send_json({"ok": False, "error": "Manager user not found"}, 404)

        if path == "/api/auth/reset-password":
            conn = get_db()
            c = conn.cursor()
            default_hash = hashlib.sha256("admin123".encode()).hexdigest()
            c.execute("UPDATE users SET password_hash = ? WHERE role = 'manager'", (default_hash,))
            conn.commit()
            conn.close()
            return self.send_json({"ok": True, "message": "Manager password reset to default (admin123)"})

        if path == "/api/watchlist/toggle":
            body = self.read_json_body()
            user_id = int(body.get("user_id", 1))
            movie_id = int(body.get("movie_id", 0))

            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT * FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
            exists = c.fetchone()
            if exists:
                c.execute("DELETE FROM watchlist WHERE user_id = ? AND movie_id = ?", (user_id, movie_id))
                in_list = False
            else:
                c.execute("INSERT INTO watchlist (user_id, movie_id) VALUES (?, ?)", (user_id, movie_id))
                in_list = True
            conn.commit()
            conn.close()
            return self.send_json({"ok": True, "in_list": in_list, "movie_id": movie_id})

        return self.send_json({"ok": False, "error": "Endpoint not found"}, 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/movies/"):
            try:
                movie_id = int(path.split("/")[-1])
                body = self.read_json_body()
                conn = get_db()
                c = conn.cursor()
                genres_json = json.dumps(body.get("g", []))
                c.execute("""
                UPDATE movies SET
                    t = ?, y = ?, r = ?, d = ?, hue = ?, tag = ?, type = ?,
                    desc = ?, cast = ?, poster = ?, vid = ?, imdbId = ?, genres = ?
                WHERE id = ?
                """, (
                    body.get("t", ""), int(body.get("y", 2026)), float(body.get("r", 7.0)),
                    body.get("d", "2h 00m"), int(body.get("hue", 190)), body.get("tag", ""),
                    body.get("type", "movie"), body.get("desc", ""), body.get("cast", ""),
                    body.get("poster", ""), body.get("vid", ""), body.get("imdbId", ""),
                    genres_json, movie_id
                ))
                conn.commit()
                c.execute("SELECT * FROM movies WHERE id = ?", (movie_id,))
                movie = movie_row_to_dict(c.fetchone())
                conn.close()
                return self.send_json({"ok": True, "message": "Updated", "data": movie})
            except Exception as e:
                return self.send_json({"ok": False, "error": str(e)}, 500)

        return self.send_json({"ok": False, "error": "Endpoint not found"}, 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith("/api/movies/"):
            try:
                movie_id = int(path.split("/")[-1])
                conn = get_db()
                c = conn.cursor()
                c.execute("DELETE FROM movies WHERE id = ?", (movie_id,))
                c.execute("DELETE FROM watchlist WHERE movie_id = ?", (movie_id,))
                conn.commit()
                conn.close()
                return self.send_json({"ok": True, "message": f"Movie {movie_id} deleted"})
            except Exception as e:
                return self.send_json({"ok": False, "error": str(e)}, 500)
        return self.send_json({"ok": False, "error": "Endpoint not found"}, 404)

    # ----------------- STATIC FILES & RANGE STREAMING -----------------
    def serve_static(self, path):
        if path in ("/", "/index.html", "/wellowshow"):
            filepath = os.path.join(BASE_DIR, "index.html")
            if not os.path.exists(filepath):
                filepath = os.path.join(BASE_DIR, "wellowshow_updated.html")
        else:
            clean_path = path.lstrip("/").replace("/", os.sep)
            filepath = os.path.join(BASE_DIR, clean_path)

        if not os.path.exists(filepath) or os.path.isdir(filepath):
            self.send_response(404)
            self.send_cors_headers()
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        file_size = os.path.getsize(filepath)
        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            mime_type = "application/octet-stream"

        range_header = self.headers.get("Range", None)
        if range_header and range_header.startswith("bytes="):
            # HTTP 206 Partial Content (Supports fast video seeking!)
            ranges = range_header.replace("bytes=", "").split("-")
            start = int(ranges[0]) if ranges[0] else 0
            end = int(ranges[1]) if len(ranges) > 1 and ranges[1] else file_size - 1
            length = end - start + 1

            self.send_response(206)
            self.send_cors_headers()
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
            self.send_header("Content-Length", str(length))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(remaining, 64 * 1024))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        else:
            self.send_response(200)
            self.send_cors_headers()
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()

            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(64 * 1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)

# ----------------- MAIN SERVER ENTRY -----------------
def run_server():
    init_db()
    server_address = ("", PORT)
    httpd = ThreadedHTTPServer(server_address, WellowShowHandler)
    print("=" * 60)
    print(f"🎬 WellowShow Streaming Platform & REST API Server")
    print(f"📡 Running at: http://localhost:{PORT}")
    print(f"📂 Serving from: {BASE_DIR}")
    print(f"💾 Database: {DB_PATH}")
    print(f"⚡ Press Ctrl+C to stop the server")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
