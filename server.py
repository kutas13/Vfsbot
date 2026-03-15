import base64
import hashlib
import hmac
import json
import os
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "spyke.db")
PORT = 4173


def hash_password(password: str, salt: bytes | None = None) -> str:
  if salt is None:
    salt = os.urandom(16)
  digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
  return f"{base64.b64encode(salt).decode()}${base64.b64encode(digest).decode()}"


def verify_password(password: str, password_hash: str) -> bool:
  salt_b64, expected_b64 = password_hash.split("$", 1)
  salt = base64.b64decode(salt_b64.encode())
  expected = base64.b64decode(expected_b64.encode())
  candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120000)
  return hmac.compare_digest(candidate, expected)


def setup_database() -> None:
  with sqlite3.connect(DB_PATH) as conn:
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
      )
      """
    )
    conn.execute(
      """
      CREATE TABLE IF NOT EXISTS passport_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        uploaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
      )
      """
    )
    user = conn.execute("SELECT id FROM users WHERE username = ?", ("Furkan Kutas",)).fetchone()
    if user is None:
      conn.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        ("Furkan Kutas", hash_password("Furkan13!")),
      )


class AppHandler(SimpleHTTPRequestHandler):
  def __init__(self, *args, **kwargs):
    super().__init__(*args, directory=ROOT, **kwargs)

  def _json_response(self, status: int, payload: dict) -> None:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)

  def do_POST(self):  # noqa: N802
    if self.path != "/api/login":
      return self._json_response(404, {"ok": False, "message": "Bulunamadı"})

    try:
      content_length = int(self.headers.get("Content-Length", "0"))
      raw_body = self.rfile.read(content_length)
      data = json.loads(raw_body.decode("utf-8"))
    except (ValueError, json.JSONDecodeError):
      return self._json_response(400, {"ok": False, "message": "Geçersiz istek."})

    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
      return self._json_response(400, {"ok": False, "message": "Kullanıcı adı ve şifre zorunludur."})

    with sqlite3.connect(DB_PATH) as conn:
      row = conn.execute(
        "SELECT username, password_hash FROM users WHERE username = ?", (username,)
      ).fetchone()

    if row is None:
      return self._json_response(401, {"ok": False, "message": "Kullanıcı adı veya şifre hatalı."})

    db_username, password_hash = row
    if not verify_password(password, password_hash):
      return self._json_response(401, {"ok": False, "message": "Kullanıcı adı veya şifre hatalı."})

    return self._json_response(200, {"ok": True, "message": f"Hoş geldin {db_username}"})

  def do_GET(self):  # noqa: N802
    if self.path == "/api/health":
      return self._json_response(200, {"ok": True, "db": DB_PATH})
    return super().do_GET()


if __name__ == "__main__":
  setup_database()
  server = ThreadingHTTPServer(("0.0.0.0", PORT), AppHandler)
  print(f"Spyke Turizm app running at http://localhost:{PORT}")
  server.serve_forever()
