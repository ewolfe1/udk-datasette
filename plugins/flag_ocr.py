"""
Datasette plugin: lets visitors flag an OCR line for staff to reprocess.

The viewer sends  POST /-/flag-ocr  with a JSON body like {"ocr_id": 11392382}.
This plugin looks that line up in the read-only archive (kansan.db) and saves
a copy to a separate SQLite file, flags.db. Datasette never serves flags.db,
and the archive is never written to.

Put this file in plugins/ and add  --plugins-dir plugins/  to datasette serve.
Set the FLAGS_DB environment variable to keep flags.db somewhere else
(for example on a Docker volume). Default: flags.db in the working directory.
"""
import json
import os
import sqlite3
import time
from collections import defaultdict, deque

from datasette import hookimpl
from datasette.utils.asgi import Response

FLAGS_DB = os.environ.get("FLAGS_DB", "flags.db")
ARCHIVE = "kansan"  # Datasette names each database after its file: kansan.db
PATH = "/-/flag-ocr"

# Rate limit per IP address, kept in memory only: IPs are never saved to disk.
MAX_FLAGS = 30        # flags allowed per IP...
WINDOW = 60 * 60      # ...per hour (in seconds)
recent = defaultdict(deque)  # ip -> times of that IP's recent flag attempts

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS ocr_flags (
    id         INTEGER PRIMARY KEY,
    ocr_id     INTEGER,  -- ocr_elements.id when flagged; may change after a rebuild
    pid        TEXT,
    x1         INTEGER,
    y1         INTEGER,
    x2         INTEGER,
    y2         INTEGER,
    text       TEXT,     -- the OCR text as it was when flagged
    iiif_url   TEXT,
    flagged_at TEXT DEFAULT (datetime('now')),  -- UTC; first flag of this text
    UNIQUE (pid, x1, y1, x2, y2, text)          -- one row per line + text
)
"""


@hookimpl
def startup():
    conn = sqlite3.connect(FLAGS_DB)
    conn.execute(CREATE_TABLE)
    conn.close()


@hookimpl
def register_routes():
    return [(f"^{PATH}$", flag_ocr)]


@hookimpl
def skip_csrf(scope):
    # Datasette's CSRF check rejects this POST as soon as the browser has any
    # cookie for the site. Flagging needs no login, so there's nothing for it
    # to protect; the JSON-only rule in flag_ocr() blocks other sites' forms.
    return scope["path"] == PATH


def error(message, status):
    return Response.json({"ok": False, "error": message}, status=status)


def parse_ocr_id(body):
    """Return the id from a JSON body like {"ocr_id": 123}, or None if invalid."""
    try:
        value = json.loads(body)["ocr_id"]
    except (ValueError, KeyError, TypeError):
        return None
    if isinstance(value, int) and 0 < value < 2**63:
        return value
    return None


def over_limit(ip):
    """Count one attempt for this IP; return True if it's over the limit."""
    now = time.time()
    times = recent[ip]
    while times and now - times[0] > WINDOW:
        times.popleft()
    if len(times) >= MAX_FLAGS:
        return True
    times.append(now)
    return False


async def flag_ocr(request, datasette):
    if request.method != "POST":
        return error("Use POST", 405)

    # A form on another website can't send this content type
    if not request.headers.get("content-type", "").startswith("application/json"):
        return error("Send JSON", 415)

    ocr_id = parse_ocr_id(await request.post_body())
    if ocr_id is None:
        return error('Expected {"ocr_id": <number>}', 400)

    client = request.scope.get("client")
    if over_limit(client[0] if client else "unknown"):
        return error("Too many flags. Try again later.", 429)

    # Look up the line here; never trust text or coordinates sent by a browser
    result = await datasette.get_database(ARCHIVE).execute(
        "SELECT id, pid, x1, y1, x2, y2, text, iiif_url FROM ocr_elements WHERE id = ?",
        [ocr_id],
    )
    row = result.first()
    if row is None:
        return error("No OCR line with that id", 404)

    conn = sqlite3.connect(FLAGS_DB)
    cursor = conn.execute(
        """INSERT OR IGNORE INTO ocr_flags (ocr_id, pid, x1, y1, x2, y2, text, iiif_url)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        tuple(row),  # same column order as the SELECT above
    )
    conn.commit()
    conn.close()

    # rowcount is 0 when this line + text was already flagged
    status = "flagged" if cursor.rowcount else "already_flagged"
    return Response.json({"ok": True, "status": status})
