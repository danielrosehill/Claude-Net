# Demo: Agent Interconnect (scratchpad relay)

A sanitised copy of a first working relay, kept as a reference for what *could* work. It is not the
chosen design. Copied 2026-11-09 from a private homelab repo at commit `5d90c3e`. Names, hosts, tailnet
and LAN addresses, and secret-store IDs were replaced: people are `alice` / `bob`, the relay is
`relay.example.ts.net`, the LAN address is `192.0.2.10`.

## Shape

- **One relay** (`server/app.py`, FastMCP < 2 + SQLite, Docker, port 8790), reachable only over the tailnet.
  - MCP endpoint `/mcp`: tools `whoami`, `send_message`, `read_messages`, `wait_for_reply`.
  - REST endpoints for the human client: `/api/health`, `/api/me`, `/api/messages`, `/api/read`.
  - Four participants, each with its own bearer token, passed as env
    `TOKENS=alice:…,bob:…,alice-claude:…,bob-claude:…` from a gitignored `.env`.
- **There is no MCP server on either side.** Each agent connects to the relay's `/mcp` directly:
  - Linux, Claude Code: as an HTTP MCP server, or through an MCP gateway.
  - Windows, Claude Desktop: `npx mcp-remote http://relay.example.ts.net:8790/mcp --header "Authorization:Bearer <token>"`.
- **Human client** (`client/interconnect.py`): a PySide6 tray chat app that polls REST every 3 s and shows
  desktop notifications. Its config is `{"server": "...", "token": "..."}`, and a setup dialog asks for both on first run.
  - The Windows `.exe` is built by PyInstaller in GitHub Actions. The workflow is in
    `.github-workflow-build-windows-client.yml.example`, renamed so it doesn't run in this repo.

## State at copy time

- **Relay:** deployed. REST and the MCP tools, including `wait_for_reply`, were tested, plus one real agent send.
- **Windows client:** built and installed. Reported working end to end on 2026-11-09 (by the user, not verified by this repo).
- **Linux client:** not installed.

## Known limits (input to the research)

- **No push.** Agents only see messages when they call `read_messages`, or block in `wait_for_reply`. A
  Claude Code *channel* shim would let the relay wake an idle session instead (see `../../docs/research.md`).
- **One flat thread.** There is no task object, status, assignment, or acknowledgement beyond read markers.
