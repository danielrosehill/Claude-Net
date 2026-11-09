"""Agent Interconnect server.

One shared household thread for four participants: two people (alice, bob) and
their Claude agents (alice-claude, bob-claude). People use the desktop client
over the REST API; agents use the MCP endpoint. Every caller is identified by a
bearer token (env TOKENS="name:token,name:token,...").
"""

from __future__ import annotations

import asyncio
import os
import sqlite3
import time
from contextlib import closing

from mcp.server.fastmcp import Context, FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

DB_PATH = os.environ.get("DB_PATH", "/data/interconnect.db")
PORT = int(os.environ.get("PORT", "8790"))

PARTICIPANTS = {
    "alice": "Alice",
    "bob": "Bob",
    "alice-claude": "Alice's Claude",
    "bob-claude": "Bob's Claude",
}


def _load_tokens() -> dict[str, str]:
    tokens: dict[str, str] = {}
    for pair in os.environ.get("TOKENS", "").split(","):
        if ":" in pair:
            name, tok = pair.strip().split(":", 1)
            if name in PARTICIPANTS and tok:
                tokens[tok] = name
    if not tokens:
        raise SystemExit("TOKENS is empty: set TOKENS=name:token,...")
    return tokens


TOKENS = _load_tokens()


def db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


with closing(db()) as _c:
    _c.executescript(
        """
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            sender TEXT NOT NULL,
            recipient TEXT NOT NULL DEFAULT 'all',
            body TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cursors(
            participant TEXT PRIMARY KEY,
            last_read INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    _c.commit()

_new_message = asyncio.Event()


def _identify(headers) -> str | None:
    auth = headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return TOKENS.get(auth[7:].strip())
    return None


def _row(r: sqlite3.Row) -> dict:
    return {
        "id": r["id"],
        "ts": r["ts"],
        "time": time.strftime("%Y-%m-%d %H:%M", time.localtime(r["ts"])),
        "sender": r["sender"],
        "sender_name": PARTICIPANTS.get(r["sender"], r["sender"]),
        "recipient": r["recipient"],
        "body": r["body"],
    }


def store(sender: str, body: str, recipient: str = "all") -> dict:
    if recipient != "all" and recipient not in PARTICIPANTS:
        raise ValueError(f"unknown recipient {recipient!r}; use one of {list(PARTICIPANTS)} or 'all'")
    body = body.strip()
    if not body:
        raise ValueError("empty message")
    with closing(db()) as c:
        cur = c.execute(
            "INSERT INTO messages(ts, sender, recipient, body) VALUES(?,?,?,?)",
            (time.time(), sender, recipient, body),
        )
        c.commit()
        row = c.execute("SELECT * FROM messages WHERE id=?", (cur.lastrowid,)).fetchone()
    _new_message.set()
    _new_message.clear()
    return _row(row)


def fetch(after: int = 0, limit: int = 200) -> list[dict]:
    with closing(db()) as c:
        rows = c.execute(
            "SELECT * FROM (SELECT * FROM messages WHERE id>? ORDER BY id DESC LIMIT ?) ORDER BY id",
            (after, limit),
        ).fetchall()
    return [_row(r) for r in rows]


def get_cursor(who: str) -> int:
    with closing(db()) as c:
        r = c.execute("SELECT last_read FROM cursors WHERE participant=?", (who,)).fetchone()
    return r["last_read"] if r else 0


def set_cursor(who: str, last_id: int) -> None:
    with closing(db()) as c:
        c.execute(
            "INSERT INTO cursors(participant,last_read) VALUES(?,?) "
            "ON CONFLICT(participant) DO UPDATE SET last_read=max(last_read, excluded.last_read)",
            (who, last_id),
        )
        c.commit()


def unread_for(who: str) -> list[dict]:
    return [m for m in fetch(get_cursor(who)) if m["sender"] != who]


mcp = FastMCP(
    "agent-interconnect",
    host="0.0.0.0",
    port=PORT,
    stateless_http=True,
    instructions=(
        "Household message thread shared by Alice, Bob and their two Claude agents "
        "(alice-claude, bob-claude). Use read_messages to see what is new, "
        "send_message to post, wait_for_reply to block until someone answers. "
        "The humans read this thread in a desktop app, so write plainly and briefly."
    ),
)


def _caller(ctx: Context) -> str:
    req = ctx.request_context.request
    who = _identify(req.headers) if req is not None else None
    if not who:
        raise PermissionError("missing or unknown bearer token")
    return who


@mcp.tool()
def whoami(ctx: Context) -> dict:
    """Return which participant this connection is, and the list of participants."""
    return {"you": _caller(ctx), "participants": PARTICIPANTS}


@mcp.tool()
def send_message(body: str, ctx: Context, to: str = "all") -> dict:
    """Post a message to the shared household thread.

    to: 'all' (default), or one of alice, bob, alice-claude, bob-claude.
    Everyone can read the thread; `to` decides who gets notified.
    """
    return store(_caller(ctx), body, to)


@mcp.tool()
def read_messages(ctx: Context, only_unread: bool = True, limit: int = 30) -> dict:
    """Read the thread. By default returns messages you haven't read yet (excluding
    your own) and marks them read. only_unread=False returns the last `limit` messages."""
    who = _caller(ctx)
    msgs = unread_for(who) if only_unread else fetch(0, limit)
    msgs = msgs[-limit:]
    if msgs:
        set_cursor(who, max(m["id"] for m in msgs))
    return {"you": who, "count": len(msgs), "messages": msgs}


@mcp.tool()
async def wait_for_reply(ctx: Context, timeout_seconds: int = 120) -> dict:
    """Block until someone else posts a NEW message (after this call starts; max 600 s),
    then return those messages and mark them read. Use after send_message when you need
    an answer. Older unread messages are not returned here: use read_messages for those."""
    who = _caller(ctx)
    deadline = time.time() + max(5, min(timeout_seconds, 600))
    latest = fetch(0, 1)
    start_id = latest[-1]["id"] if latest else 0
    while time.time() < deadline:
        msgs = [m for m in fetch(start_id) if m["sender"] != who]
        if msgs:
            set_cursor(who, max(m["id"] for m in msgs))
            return {"you": who, "count": len(msgs), "messages": msgs}
        try:
            await asyncio.wait_for(_new_message.wait(), timeout=min(5, deadline - time.time()))
        except asyncio.TimeoutError:
            pass
    return {"you": who, "count": 0, "messages": [], "timed_out": True}


# ---- REST API for the desktop client -------------------------------------------------


def _auth(request: Request) -> str | None:
    return _identify(request.headers)


@mcp.custom_route("/api/health", methods=["GET"])
async def health(request: Request):
    return JSONResponse({"ok": True})


@mcp.custom_route("/api/me", methods=["GET"])
async def api_me(request: Request):
    who = _auth(request)
    if not who:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    return JSONResponse({"you": who, "name": PARTICIPANTS[who], "participants": PARTICIPANTS,
                         "last_read": get_cursor(who)})


@mcp.custom_route("/api/messages", methods=["GET", "POST"])
async def api_messages(request: Request):
    who = _auth(request)
    if not who:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    if request.method == "POST":
        data = await request.json()
        try:
            msg = store(who, data.get("body", ""), data.get("to", "all"))
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        set_cursor(who, msg["id"])
        return JSONResponse(msg)
    after = int(request.query_params.get("after", "0"))
    return JSONResponse({"messages": fetch(after)})


@mcp.custom_route("/api/read", methods=["POST"])
async def api_read(request: Request):
    who = _auth(request)
    if not who:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    data = await request.json()
    set_cursor(who, int(data.get("last_id", 0)))
    return JSONResponse({"ok": True})


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
