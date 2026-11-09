---
name: connect-as-client
description: Use when you need to register a relay server as an MCP client in your local Claude install.
---

# Connect as Client

Register a running relay server as an MCP server in the local Claude install and authenticate as a client.

## When to use

- After deploying a relay server with `setup-relay-server`
- Adding a second Claude instance to an existing relay
- Switching to a different relay endpoint

## Inputs to gather

- Relay URL (e.g., `http://relay-host:8844`)
- Client ID for this instance (e.g., `claude-alice-desktop`)
- Optional shared bearer token (if the relay requires it)

## Procedure

1. Prompt the user for relay URL, client_id, and optional token.
2. Call `claude mcp add` with HTTP streamable transport, passing the relay URL.
3. Invoke the `relay_status` MCP tool to verify connectivity.
4. If successful, write the chosen client_id and relay URL to `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/agent-relay/client.toml`.
5. Display the relay status and confirm the client is registered.

## Output / side effects

- Relay registered in Claude's MCP config.
- `client.toml` persisted under `$CLAUDE_USER_DATA/agent-relay/` with client_id and relay URL.
- User sees relay version, uptime, and a list of active sessions.

## Safety / constraints

- Bearer token (if provided) is stored in plaintext in config; assume the user controls file permissions.
- Relay URL is validated with a live `relay_status` call before confirming registration.
