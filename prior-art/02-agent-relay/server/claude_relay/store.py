import sqlite3
import time
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    name TEXT PRIMARY KEY,
    description TEXT,
    participants TEXT NOT NULL,
    created_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session TEXT NOT NULL,
    sender TEXT NOT NULL,
    ts INTEGER NOT NULL,
    text TEXT,
    attachments TEXT,
    FOREIGN KEY (session) REFERENCES sessions(name)
);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session, id);
CREATE TABLE IF NOT EXISTS blobs (
    sha256 TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mime TEXT,
    created_at INTEGER NOT NULL,
    refcount INTEGER NOT NULL DEFAULT 0
);
"""


class Store:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def create_session(self, name: str, participants: list[str], description: str = "") -> dict:
        self.conn.execute(
            "INSERT OR IGNORE INTO sessions (name, description, participants, created_at) VALUES (?, ?, ?, ?)",
            (name, description, ",".join(participants), int(time.time())),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM sessions WHERE name = ?", (name,)).fetchone()
        return dict(row)

    def list_sessions(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM sessions ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def add_message(self, session: str, sender: str, text: str, attachments: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO messages (session, sender, ts, text, attachments) VALUES (?, ?, ?, ?, ?)",
            (session, sender, int(time.time()), text, attachments),
        )
        self.conn.commit()
        return cur.lastrowid

    def read_inbox(self, session: str, since_cursor: int = 0, limit: int = 100) -> list[dict]:
        rows = self.conn.execute(
            "SELECT id, sender, ts, text, attachments FROM messages WHERE session = ? AND id > ? ORDER BY id ASC LIMIT ?",
            (session, since_cursor, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def register_blob(self, sha: str, size: int, mime: str = "") -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO blobs (sha256, size, mime, created_at) VALUES (?, ?, ?, ?)",
            (sha, size, mime, int(time.time())),
        )
        self.conn.commit()

    def stats(self) -> dict:
        s = self.conn.execute("SELECT COUNT(*) AS n FROM sessions").fetchone()["n"]
        m = self.conn.execute("SELECT COUNT(*) AS n FROM messages").fetchone()["n"]
        b = self.conn.execute("SELECT COUNT(*) AS n, COALESCE(SUM(size), 0) AS bytes FROM blobs").fetchone()
        return {"sessions": s, "messages": m, "blobs": b["n"], "blob_bytes": b["bytes"]}
