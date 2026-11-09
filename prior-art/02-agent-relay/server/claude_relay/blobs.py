import hashlib
import shutil
from pathlib import Path


def blob_path(root: Path, sha: str) -> Path:
    return root / sha[:2] / sha


def store_file(root: Path, src: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    size = 0
    with src.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            size += len(chunk)
    sha = h.hexdigest()
    dst = blob_path(root, sha)
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)
    return sha, size


def fetch_blob(root: Path, sha: str, dest: Path) -> int:
    src = blob_path(root, sha)
    if not src.exists():
        raise FileNotFoundError(f"blob {sha} not found")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return src.stat().st_size
