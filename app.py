from flask import Flask, request, jsonify, redirect, render_template_string
import sqlite3
import string
import random
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = "urls.db"
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS urls (
                code        TEXT PRIMARY KEY,
                original    TEXT NOT NULL,
                clicks      INTEGER DEFAULT 0,
                created_at  TEXT NOT NULL
            )
        """)
        conn.commit()

def gen_code(length: int = 6) -> str:
    """Generate a unique random short code."""
    chars = string.ascii_letters + string.digits
    with get_db() as conn:
        while True:
            code = "".join(random.choices(chars, k=length))
            row = conn.execute("SELECT 1 FROM urls WHERE code = ?", (code,)).fetchone()
            if not row:
                return code

@app.route("/shorten", methods=["POST"])
def shorten():
    """
    POST /shorten
    Body (JSON): { "url": "https://example.com/very/long/path" }
    Returns:     { "short_url": "http://localhost:5000/abc123", "code": "abc123" }
    """
    data = request.get_json(silent=True) or {}
    original = data.get("url", "").strip()

    if not original:
        return jsonify({"error": "Missing 'url' field"}), 400

    if not (original.startswith("http://") or original.startswith("https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    code = gen_code()
    created_at = datetime.utcnow().isoformat()

    with get_db() as conn:
        conn.execute(
            "INSERT INTO urls (code, original, clicks, created_at) VALUES (?, ?, 0, ?)",
            (code, original, created_at),
        )
        conn.commit()

    return jsonify({
        "code": code,
        "short_url": f"{BASE_URL}/{code}",
        "original": original,
        "created_at": created_at,
    }), 201


@app.route("/<code>")
def redirect_to_original(code):
    """
    GET /<code>
    Increments the click counter and redirects to the original URL.
    Returns 404 JSON if the code is not found.
    """
    with get_db() as conn:
        row = conn.execute("SELECT original FROM urls WHERE code = ?", (code,)).fetchone()
        if not row:
            return jsonify({"error": f"Short code '{code}' not found"}), 404

        conn.execute("UPDATE urls SET clicks = clicks + 1 WHERE code = ?", (code,))
        conn.commit()

    return redirect(row["original"], code=302)


@app.route("/api/links", methods=["GET"])
def list_links():
    """
    GET /api/links
    Returns all stored short links (newest first).
    """
    with get_db() as conn:
        rows = conn.execute(
            "SELECT code, original, clicks, created_at FROM urls ORDER BY created_at DESC"
        ).fetchall()

    return jsonify([
        {
            "code": r["code"],
            "short_url": f"{BASE_URL}/{r['code']}",
            "original": r["original"],
            "clicks": r["clicks"],
            "created_at": r["created_at"],
        }
        for r in rows
    ])


@app.route("/api/links/<code>", methods=["GET"])
def get_link(code):
    """GET /api/links/<code> — fetch stats for a single link."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT code, original, clicks, created_at FROM urls WHERE code = ?", (code,)
        ).fetchone()

    if not row:
        return jsonify({"error": "Not found"}), 404

    return jsonify({
        "code": row["code"],
        "short_url": f"{BASE_URL}/{row['code']}",
        "original": row["original"],
        "clicks": row["clicks"],
        "created_at": row["created_at"],
    })


@app.route("/api/links/<code>", methods=["DELETE"])
def delete_link(code):
    """DELETE /api/links/<code> — remove a short link."""
    with get_db() as conn:
        result = conn.execute("DELETE FROM urls WHERE code = ?", (code,))
        conn.commit()

    if result.rowcount == 0:
        return jsonify({"error": "Not found"}), 404

    return jsonify({"message": f"Deleted '{code}'"}), 200

FRONTEND = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>URL Shortener</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: system-ui, sans-serif; background: #f5f5f5; display: flex;
         justify-content: center; padding: 3rem 1rem; color: #111; }
  .container { width: 100%; max-width: 600px; }
  h1 { font-size: 1.6rem; font-weight: 600; margin-bottom: 1.5rem; }
  input { width: 100%; padding: .65rem .85rem; border: 1px solid #d1d5db;
          border-radius: 8px; font-size: 1rem; outline: none; }
  input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,.15); }
  button { margin-top: .75rem; width: 100%; padding: .65rem; background: #2563eb;
           color: #fff; border: none; border-radius: 8px; font-size: 1rem;
           cursor: pointer; font-weight: 500; }
  button:hover { background: #1d4ed8; }
  .result { margin-top: 1rem; padding: .75rem 1rem; background: #ecfdf5;
            border: 1px solid #6ee7b7; border-radius: 8px; font-size: .9rem;
            word-break: break-all; }
  .error { margin-top: .75rem; color: #dc2626; font-size: .9rem; }
  .links { margin-top: 2rem; }
  .link-row { background: #fff; border: 1px solid #e5e7eb; border-radius: 8px;
              padding: .75rem 1rem; margin-bottom: .5rem; font-size: .85rem; }
  .link-row a { color: #2563eb; text-decoration: none; font-weight: 500; }
  .link-row .orig { color: #6b7280; overflow: hidden; text-overflow: ellipsis;
                    white-space: nowrap; max-width: 100%; display: block; }
  .link-row .meta { color: #9ca3af; font-size: .8rem; margin-top: 2px; }
</style>
</head>
<body>
<div class="container">
  <h1>&#9889; URL Shortener</h1>
  <input id="urlInput" type="text" placeholder="https://example.com/long/url" />
  <button onclick="shorten()">Shorten</button>
  <div id="result"></div>
  <div class="links" id="links"></div>
</div>
<script>
async function shorten() {
  const url = document.getElementById('urlInput').value.trim();
  const res = await fetch('/shorten', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({url})
  });
  const data = await res.json();
  const el = document.getElementById('result');
  if (!res.ok) { el.innerHTML = `<div class="error">${data.error}</div>`; return; }
  el.innerHTML = `<div class="result">&#10003; <a href="${data.short_url}" target="_blank">${data.short_url}</a></div>`;
  loadLinks();
}

async function loadLinks() {
  const res = await fetch('/api/links');
  const links = await res.json();
  document.getElementById('links').innerHTML = links.map(l => `
    <div class="link-row">
      <a href="${l.short_url}" target="_blank">${l.short_url}</a>
      <span class="orig">${l.original}</span>
      <span class="meta">${l.clicks} click${l.clicks !== 1 ? 's' : ''} &middot; ${l.created_at.slice(0,10)}</span>
    </div>`).join('');
}

document.getElementById('urlInput').addEventListener('keydown', e => { if (e.key==='Enter') shorten(); });
loadLinks();
</script>
</body>
</html>"""


@app.route("/")
def index():
    return render_template_string(FRONTEND)

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
