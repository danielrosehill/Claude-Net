# Claude-Agent-Relay-Plugin

Direct agent-to-agent communication and coordination within a LAN. Two (or more) Claude instances on different machines exchange messages and files via a shared MCP relay server.

## Use cases

- Claude on a desktop coordinating with Claude on a home-assistant server.
- Claude on one machine asking Claude on another to investigate a problem locally (logs, config, hardware).
- Pairs of agents handing off tasks across machines without manual copy/paste.

## Trust model

LAN-only and trust-based. The relay does not authenticate users — it identifies clients by a string and an optional shared bearer token. Run it on a network you control.

## Components

- **MCP relay server** (`server/`) — Python + FastMCP, SQLite for sessions/messages, content-addressed blob store for attachments. Streamable HTTP transport. TOON used for list responses where it saves tokens vs JSON.
- **Skills** (`skills/`):
  - `onboard` — first-run setup: capture relay URL, this machine's `client_id`, optional shared token, and the peer roster (friendly names → `client_id`s)
  - `setup-relay-server` — deploy the server to a host (typically a small LAN VM)
  - `connect-as-client` — register the relay as an MCP server in the local Claude install
  - `create-session` — open a named session between two clients
  - `send-message` / `send-file` — convenience wrappers
  - `tail-session` — stream new messages from a session
  - `relay-status` — health, sessions, blob storage usage

## Where your config lives

The plugin ships **no user data**. Onboarding writes everything machine-specific to `$CLAUDE_USER_DATA/agent-relay/` (falling back to `${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins/agent-relay/`). Updating the plugin never touches it.

```
$CLAUDE_USER_DATA/agent-relay/
├── config.toml          # relay URL, this machine's client_id, optional token
├── peers.toml           # friendly_name -> client_id roster
└── cursors/<session>.txt  # per-session read cursors
```
- **Client config** (`client/mcp-config.example.json`) — boilerplate the connect skill personalizes.

## Installation

```bash
claude plugins install agent-relay@danielrosehill
```

Then run the `setup-relay-server` skill on the host that will run the relay, and `connect-as-client` on each Claude machine that should join.

## License

MIT
