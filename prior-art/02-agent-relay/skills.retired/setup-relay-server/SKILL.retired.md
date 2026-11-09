---
name: setup-relay-server
description: Use when you need to deploy the MCP relay server to a remote SSH host.
---

# Setup Relay Server

Deploy the Claude Agent Relay server to a user-specified SSH host, configure it with systemd, and verify connectivity.

## When to use

- First-time relay server installation on a new host
- Re-deploying the relay after code updates
- Moving the relay to a different machine

## Inputs to gather

- SSH target host (e.g., `user@relay-host` or `192.0.2.75`)
- Bind address for the relay (default: `127.0.0.1`; use `0.0.0.0` for LAN access)
- Port (default: `8844`)
- Optional shared bearer token for all clients (or empty to skip)

## Procedure

1. Validate SSH connectivity to the target host.
2. Copy or clone the `server/` directory to the host (e.g., `/opt/claude-relay/`).
3. On the host, create a Python venv and install: `pip install -e .`
4. Write `/etc/claude-relay/config.toml` with bind address, port, `/var/lib/claude-relay/` data dir, and optional shared token.
5. Copy `server/systemd/claude-relay.service` to `/etc/systemd/system/`, adjust paths if needed.
6. Enable and start the service: `systemctl enable --now claude-relay`.
7. Test reachability: `curl http://<bind>:<port>/mcp` (should return status).
8. Print the relay URL and connection parameters the user needs for `connect-as-client`.

## Output / side effects

- Relay server running on the target host under systemd.
- `/var/lib/claude-relay/` created on the host for sessions, blobs, and state.
- User receives: relay URL, port, recommended client_ids, and connection test result.

## Safety / constraints

- Do not hardcode the deployment target; accept any SSH host.
- Server data lives on the relay host (`/var/lib/claude-relay/`), not in user data directories.
- Shared token (if provided) is passed to the config but not logged; treat as sensitive.
- Systemd unit runs as root; document port < 1024 restrictions if applicable.
