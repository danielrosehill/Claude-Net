---
name: onboard
description: First-run setup for agent-relay. Captures the relay URL, this machine's client_id, optional shared token, and the roster of peer clients (friendly name -> client_id). All written to $CLAUDE_USER_DATA/agent-relay/config.toml -- never into the plugin directory. Run once per machine before using send-message, tail-session, etc.
---

# Onboard

First-run configuration for the agent-relay plugin. The plugin itself ships no user data; everything you configure here is stored outside the plugin directory so updates never overwrite it.

## Where config lives

Resolve the user data root in this order:

1. `$CLAUDE_USER_DATA` if set
2. `${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins`

Then this plugin's namespace is `<root>/agent-relay/`. The onboarding writes:

- `<root>/agent-relay/config.toml` -- relay URL, this machine's client_id, optional shared token
- `<root>/agent-relay/peers.toml` -- roster of known peers (friendly name -> client_id + optional notes)
- `<root>/agent-relay/cursors/<session>.txt` -- per-session read cursors (created lazily by `tail-session`)

Never write any of this under the plugin directory.

## Steps

### 1. Resolve and create the data dir

```bash
ROOT="${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}"
DATA="$ROOT/agent-relay"
mkdir -p "$DATA/cursors"
echo "Using $DATA"
```

### 2. Gather inputs from the user

Ask, in order:

- **Relay URL** -- e.g. `http://relay-host:7878/mcp/`. If the relay isn't deployed yet, suggest running `setup-relay-server` first.
- **This machine's client_id** -- short, stable, kebab-case. Suggest a default based on `hostname` and the active user (e.g. `claude-${USER}-${HOSTNAME%%.*}`).
- **Shared bearer token** -- optional. If the relay was set up without one, leave blank.
- **Peer roster** -- repeatedly prompt for `friendly_name`, `client_id`, optional `notes`. The friendly_name is what other skills will accept on the command line (so `send-message ha "..."` resolves to client_id `claude-homeassistant-server`). Stop when the user says they're done.

### 3. Write `config.toml`

```toml
relay_url = "http://relay-host:7878/mcp/"
client_id = "claude-alice-desktop"
shared_token = ""   # leave empty on a trusted LAN
```

### 4. Write `peers.toml`

```toml
[[peers]]
name = "ha"
client_id = "claude-homeassistant-server"
notes = "Claude on the Home Assistant server"

[[peers]]
name = "bob-laptop"
client_id = "claude-bob-laptop"
notes = ""
```

### 5. Register the relay as an MCP server locally

Hand off to `connect-as-client` (or run inline):

```bash
claude mcp add --transport http agent-relay "$(grep '^relay_url' "$DATA/config.toml" | cut -d'"' -f2)"
```

If a `shared_token` is set, add the `Authorization: Bearer ...` header. If a `client_id` is set, add `X-Client-Id: <id>`.

### 6. Verify

Call the `relay_status` MCP tool and show the result. If it returns version + uptime, onboarding is complete.

## Updating later

Re-running `onboard` is non-destructive: read existing values as defaults, only overwrite fields the user changes. To add a single peer without re-walking everything, the user can edit `peers.toml` directly or call this skill in `--add-peer` mode.
