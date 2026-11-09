# claude-relay (MCP server)

The MCP relay server that backs the `agent-relay` plugin. Runs on a single LAN host (typically a small VM); Claude instances on other machines connect to it as MCP clients.

## Install (manual; the plugin's `setup-relay-server` skill automates this)

```bash
sudo useradd -r -s /usr/sbin/nologin claude-relay
sudo mkdir -p /opt/claude-relay /etc/claude-relay /var/lib/claude-relay
sudo chown claude-relay:claude-relay /var/lib/claude-relay
sudo cp -r server/ /opt/claude-relay/src
sudo python3 -m venv /opt/claude-relay/.venv
sudo /opt/claude-relay/.venv/bin/pip install -e /opt/claude-relay/src
sudo cp server/config.example.toml /etc/claude-relay/config.toml
sudo cp server/systemd/claude-relay.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now claude-relay
```

Health check:

```bash
curl -s http://<host>:7878/mcp/  # FastMCP exposes a JSON-RPC endpoint
```

## Tools exposed

- `relay_status()`
- `create_session(name, participants[], description?)`
- `list_sessions()` -> TOON
- `send_message(session, sender, text, attachments?)`
- `read_inbox(session, since_cursor?, limit?)` -> TOON
- `upload_blob(local_path)` -> sha256, size
- `download_blob(sha256, dest_path)`
- `attach_blob(session, sha256, filename, mime?)`

## Storage

- Messages and session metadata: SQLite at `/var/lib/claude-relay/relay.sqlite`
- Blobs: content-addressed at `/var/lib/claude-relay/blobs/<sha[:2]>/<sha>`
