# Research: agent-to-agent messaging between two people's Claude Code sessions

Date: 2026-11-09. Web and docs research only; nothing was installed or tested. Stars and push dates come from
the GitHub API on that date. "Inferred" marks a conclusion the source does not state.

## Requirement

- **Agents:** two Claude Code users, each on their own Anthropic account. Side A is a Linux desktop; side B is a Windows desktop.
- **Network:** both machines are on one Tailscale tailnet. The relay runs on a home Linux server (Docker) that is reachable only over the tailnet, so it is the same from the LAN or remote.
- **Traffic:**
  - Each agent can send tasks and updates to the other.
  - Each can flag items "for A's attention" or "for B's attention".
  - Each has an inbox that persists.
  - Nice to have: threads, acknowledgements, and humans able to read the same traffic.

## 1. What Claude Code offers natively

Sources: [cross-session messaging](https://code.claude.com/docs/en/cross-session-messaging),
[channels](https://code.claude.com/docs/en/channels),
[channels reference](https://code.claude.com/docs/en/channels-reference).

- **Cross-session `SendMessage` / `ListAgents` does not cross accounts.**
  - It is available from v2.1.224, and from v2.1.234 on native Windows.
  - On one machine it travels over a per-user socket or named pipe. Between machines it goes through Anthropic's servers over that account's Remote Control connection.
  - It reaches only "your other sessions". No Team or Enterprise mode for peer messaging between accounts is documented (inferred from silence).
- **Channels: an MCP server can push events into a running session.** This is the piece that removes polling.
  - The server declares `capabilities.experimental['claude/channel'] = {}` and calls `notifications/claude/channel` with `{content, meta}`.
  - Events that arrive while Claude is busy queue up. An idle session starts a new turn.
  - Adding `tools: {}` plus a `reply` tool makes the channel two-way.
  - Limits:
    - It is a research preview.
    - The channel server runs locally over stdio, so a remote relay needs a local shim that connects out to it.
    - A custom channel needs `--dangerously-load-development-channels server:<name>`. That flag shows a confirmation on every interactive start and is ignored with `-p` or the Agent SDK.
    - Team and Enterprise orgs need `channelsEnabled` turned on.
    - A server that negotiates MCP revision 2026-07-28 isn't registered as a channel. Set `MCP_PROTOCOL_NEGOTIATION=legacy`.
    - Sender identity must be allowlisted, because an ungated channel is a prompt-injection route.
  - **Windows risk:** issues
    [#37026](https://github.com/anthropics/claude-code/issues/37026),
    [#43585](https://github.com/anthropics/claude-code/issues/43585),
    [#50465](https://github.com/anthropics/claude-code/issues/50465) and
    [#106174](https://github.com/anthropics/claude-code/issues/106174) report channels being ignored or inbound
    events being dropped on Windows. Whether current releases are fixed is unconfirmed. **Test on side B's machine before committing.**
- **A second route into a session, untested:** a local shim posts into the session's own messaging
  socket (`CLAUDE_CODE_MESSAGING_SOCKET`, with `CLAUDE_CODE_MESSAGING_TOKEN` on Windows). This avoids the development
  flag, but it is subject to `crossSessionInbound` hold/refuse rules (inferred viability).
- **Remote Control, cloud sessions, Claude in Slack:** each is tied to one account, and none pushes into another person's session.

**Conclusion:** a self-hosted relay is required. The open choice is how messages reach the agent: it polls, it blocks
in a `wait` tool, or a channel shim pushes them.

## 2. Existing self-hostable relays

| Rank | Project | Fit | Maturity (2026-11-09) | Main risk |
|---|---|---|---|---|
| 1 | [mcp_agent_mail_rust](https://github.com/Dicklesworthstone/mcp_agent_mail_rust) | Mail model: subject, `thread_id`, importance, `ack_required` and receipts. Git + markdown archive that humans can read; web UI and TUI. Streamable HTTP `/mcp/`, bearer auth, GHCR Docker image, Windows installer. | 240 stars, pushed today. Successor to the Python [mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail) (2.2k stars). | Licence is "MIT + rider": read it. One shared bearer token per server. Built for coding fleets, so it has extra surface (file leases). No push (inferred). |
| 2 | [claude-mesh](https://github.com/pouriamrt/claude-mesh) | Hono + SQLite relay plus a **local stdio channel shim** per machine, so it pushes. Per-user pair codes give bearer tokens, `from` is stamped by the relay, and threads use `in_reply_to`. README recommends Tailscale. Inbound tested on Windows 11. | 23 stars, MIT, last push 2026-09-19 | Depends on the channels preview and its development flag. Outbound path only unit-tested. No human viewer. |
| 3 | Chat server + MCP: [Mattermost official MCP](https://docs.mattermost.com/agents/mcpserver/README.html), Zulip, Matrix | Humans and agents share threads, with mobile apps and per-user accounts. | Mattermost MCP is vendor-supported. Zulip and Matrix MCPs are small or stale. | No agent inbox or ack semantics, so mentions-as-inbox is a convention you build. Heavier server. |
| 4 | [Patchcord](https://github.com/ppravdin/patchcord) | Threads with resolve/defer, `wait_for_message`, offline queue. | 4 stars, last push 2026-07-16 | Self-hosting needs Supabase. |
| 5 | [bot-relay-mcp](https://github.com/Maxlumiere/bot-relay-mcp) | Task objects (accept/complete/reject), channels, read receipts, per-agent tokens. | 4 stars, 327 commits, pushed today | Single maintainer, frequent breaking majors, no Dockerfile. |

Also checked:
- [a2abridge](https://github.com/vbcherepanov/a2abridge): A2A peer-to-peer mesh with mTLS, heavy to set up.
- [outbox](https://github.com/bfxavier/outbox): .NET, no licence, 0 stars.
- TempMee/mcp-relay: 404.
- tailbus, Synapse, cc2cc, mcp-dispatch: these are local-only or too early.

Not searched directly: Smithery, mcp.so, the official MCP registry.

## 3. The scratchpad demo

`demo/agent-interconnect/` is a working relay: FastMCP + SQLite, per-participant bearer tokens, MCP tools
`send_message` / `read_messages` / `wait_for_reply`, and a PySide6 tray client for humans. Compared with the candidates above:

- **Already has:**
  - per-person tokens;
  - a human-readable thread plus a desktop client;
  - tailnet-only deployment;
  - Windows reach via `mcp-remote`.
- **Lacks:**
  - push into the session;
  - task objects or status;
  - acknowledgements;
  - threads (it is one flat thread).
- **Note:** the demo wires side B as **Claude Desktop**, not Claude Code. Claude Code on Windows can add the relay
  directly as an HTTP MCP server (`claude mcp add --transport http ...`), so `mcp-remote` isn't needed there.

## Recommendation (to decide)

1. **First, validate the push path on Windows.** Run a ten-line custom channel on side B with the development flag. If it
   works, use push. If not, use `wait`/poll, or try the messaging-socket route.
2. **Pilot mcp_agent_mail_rust in Docker on the home server, tailnet-only.** It covers inbox, threads, acks and
   persistence with the most maturity, which is the "more solid" option. Pair it with a small channel shim of our own
   per side if push works.
3. **Keep claude-mesh as the alternative** if per-person identity and built-in push matter more than maturity. Its
   design (relay-stamped `from`, local channel shim) is also the model for the shim in option 2.
4. **Keep the demo** as the fallback. It is extensible, at about 600 lines, if both candidates disappoint.
