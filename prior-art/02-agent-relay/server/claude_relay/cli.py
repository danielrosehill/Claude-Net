import argparse
import os
from . import config as cfg_mod
from .server import build


def main() -> None:
    ap = argparse.ArgumentParser(prog="claude-relay")
    ap.add_argument("--config", default=os.environ.get("RELAY_CONFIG", "/etc/claude-relay/config.toml"))
    ap.add_argument("--host", default=None)
    ap.add_argument("--port", type=int, default=None)
    args = ap.parse_args()

    cfg = cfg_mod.load(args.config)
    if args.host:
        cfg.bind_host = args.host
    if args.port:
        cfg.bind_port = args.port

    mcp = build(cfg)
    mcp.run(transport="http", host=cfg.bind_host, port=cfg.bind_port)


if __name__ == "__main__":
    main()
