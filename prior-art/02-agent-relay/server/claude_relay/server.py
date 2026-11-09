from pathlib import Path
from fastmcp import FastMCP

from . import __version__
from .config import Config
from .store import Store
from .blobs import store_file, fetch_blob, blob_path
from .toon import encode_table


def build(cfg: Config) -> FastMCP:
    store = Store(cfg.db_path)
    mcp = FastMCP("claude-relay")

    @mcp.tool
    def relay_status() -> dict:
        s = store.stats()
        return {"version": __version__, **s, "data_dir": str(cfg.data_dir)}

    @mcp.tool
    def create_session(name: str, participants: list[str], description: str = "") -> dict:
        return store.create_session(name, participants, description)

    @mcp.tool
    def list_sessions() -> str:
        rows = store.list_sessions()
        return encode_table(
            ["name", "participants", "description", "created_at"],
            [(r["name"], r["participants"], r["description"] or "", r["created_at"]) for r in rows],
        )

    @mcp.tool
    def send_message(session: str, sender: str, text: str, attachments: str = "") -> dict:
        msg_id = store.add_message(session, sender, text, attachments)
        return {"id": msg_id, "session": session}

    @mcp.tool
    def read_inbox(session: str, since_cursor: int = 0, limit: int = 100) -> str:
        rows = store.read_inbox(session, since_cursor, limit)
        return encode_table(
            ["id", "sender", "ts", "text", "attachments"],
            [(r["id"], r["sender"], r["ts"], r["text"] or "", r["attachments"] or "") for r in rows],
        )

    @mcp.tool
    def upload_blob(local_path: str) -> dict:
        src = Path(local_path)
        if not src.exists():
            raise FileNotFoundError(local_path)
        if src.stat().st_size > cfg.max_blob_bytes:
            raise ValueError(f"file exceeds max_blob_bytes ({cfg.max_blob_bytes})")
        sha, size = store_file(cfg.blob_dir, src)
        store.register_blob(sha, size)
        return {"sha256": sha, "size": size}

    @mcp.tool
    def download_blob(sha256: str, dest_path: str) -> dict:
        size = fetch_blob(cfg.blob_dir, sha256, Path(dest_path))
        return {"sha256": sha256, "size": size, "dest": dest_path}

    @mcp.tool
    def attach_blob(session: str, sha256: str, filename: str, mime: str = "") -> dict:
        if not blob_path(cfg.blob_dir, sha256).exists():
            raise FileNotFoundError(f"blob {sha256} not on relay")
        marker = f"{filename}:{sha256}:{mime}"
        return {"session": session, "attachment": marker}

    return mcp
