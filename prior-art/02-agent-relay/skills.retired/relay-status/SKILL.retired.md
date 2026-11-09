---
name: relay-status
description: Use when you need to check the health and status of the relay server.
---

# Relay Status

Query and display the relay server's operational status, including version, uptime, session count, and blob storage metrics.

## When to use

- Verifying the relay is online and healthy
- Debugging connection issues
- Monitoring relay load and resource usage
- Confirming the client is properly connected

## Inputs to gather

None — the skill reads the relay configuration from the local client.toml file.

## Procedure

1. Load the relay URL and client_id from `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/agent-relay/client.toml`.
2. Call the `relay_status` MCP tool.
3. Extract and render: server version, uptime, session count, total message count, blob count, total blob storage (bytes).
4. Optionally display per-client cursor positions and last-seen timestamp.
5. Print in a clear, structured format (e.g., table or YAML).

## Output / side effects

- Status report printed to stdout.
- No local state changes.
- If the relay is unreachable, report the error and suggest troubleshooting steps (check network, verify URL, etc.).

## Safety / constraints

- This is a read-only operation; no side effects on the relay.
- Cursor data is per-session; only shows aggregated metrics if the relay's `relay_status` tool includes them.
