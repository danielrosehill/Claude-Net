from dataclasses import dataclass
from pathlib import Path
import os
import tomllib


@dataclass
class Config:
    bind_host: str = "0.0.0.0"
    bind_port: int = 7878
    data_dir: Path = Path("/var/lib/claude-relay")
    shared_token: str | None = None
    max_blob_bytes: int = 500 * 1024 * 1024
    total_blob_quota_bytes: int = 10 * 1024 * 1024 * 1024

    @property
    def db_path(self) -> Path:
        return self.data_dir / "relay.sqlite"

    @property
    def blob_dir(self) -> Path:
        return self.data_dir / "blobs"


def load(path: str | os.PathLike = "/etc/claude-relay/config.toml") -> Config:
    cfg = Config()
    p = Path(path)
    if p.exists():
        data = tomllib.loads(p.read_text())
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, Path(v) if k == "data_dir" else v)
    env_token = os.environ.get("RELAY_TOKEN")
    if env_token:
        cfg.shared_token = env_token
    cfg.data_dir.mkdir(parents=True, exist_ok=True)
    cfg.blob_dir.mkdir(parents=True, exist_ok=True)
    return cfg
