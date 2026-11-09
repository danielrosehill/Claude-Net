# Q2 Findings — Same-machine A2A (local ↔ local)

_Market scan as of 2026-07-15._

## Summary

For two **separately-launched, top-level** Claude Code CLIs on one machine, the market has converged on one answer: **a local MCP "message-bus" server that both instances connect to.** Several genuinely work today. The clear off-the-shelf leader is **[claude-peers-mcp](https://github.com/louislva/claude-peers-mcp)** (~2.2k★) — a localhost broker + SQLite that lets any running Claude Code message any other by peer ID, with instant push.

Two framing points:

- This is **not** Claude Code's built-in subagents/`Task` tool (those run inside one session and only report up to their parent).
- It's also **not** Claude Code's newer experimental **native "agent teams"** (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): there, one *lead* session spawns teammates that message each other via a file-based mailbox (`~/.claude/teams/{team}/inboxes/{agent}.json`) using a built-in `SendMessage` tool. It's the reference architecture the third-party tools imitate — but it's lead-spawned and one-team-per-session, so you **cannot join two independently-started `claude` processes** into one team. Noted for contrast only.

**Key technical caveat:** the polished tools get *push* delivery (messages injected into the peer's context without polling) via Claude Code's **experimental "channels"** API, which requires launching with `claude --dangerously-load-development-channels server:<name>`. It's undocumented/beta — Anthropic could change it. Tools that avoid channels fall back to 1-second polling or `tmux send-keys` injection.

---

## Approach A — Ephemeral / fully-localhost bridge

Spun up on demand, loopback-only, no network exposure.

### A1. claude-peers-mcp ⭐ recommended — most mature
- **URL:** https://github.com/louislva/claude-peers-mcp
- **What:** "Allow all your Claude Codes to message each other ad-hoc." Local message bus for Claude Code instances.
- **Transport:** Broker daemon on **localhost:7899** + **SQLite**. Each session spawns a stdio MCP server that registers with the broker; delivery is 1s polling **plus** channel push. Localhost-only.
- **Hook-in:** `claude mcp add --scope user --transport stdio claude-peers -- bun ~/claude-peers-mcp/server.ts`, then launch each terminal with `claude --dangerously-load-development-channels server:claude-peers`. Broker auto-launches with the first session; dead peers auto-cleaned.
- **Tools:** `list_peers` (discovery: cwd, git repo, activity summary), `send_message` (by peer ID), `set_summary`, `check_messages`.
- **Nice touch:** optional `OPENAI_API_KEY` → each instance auto-writes a one-line "what I'm working on" summary at startup so peers see it in `list_peers`.
- **Maturity:** ~**2.2k★**, 290 forks, active, TypeScript. The clear leader.
- **HITL:** peer list with summaries; SQLite inspectable; auth = your interactive claude.ai login (no per-session join code).

### A2. bobnet-mcp — cleanest pure-localhost design, but very early
- **URL:** https://github.com/cath42/bobnet-mcp
- **Transport:** **Unix domain socket** at `${TMPDIR}/bobnet-mcp-${uid}.sock` (perms `0600`, OS enforces same-UID-only). Singleton daemon auto-spawns on first connect, dies 60s after last client. **No TCP, no tokens, no persistence** — the purest Approach-A fit.
- **Hook-in:** `.mcp.json` with `BOBNET_NAME`/`BOBNET_PURPOSE`/`BOBNET_EXPERTISE`, launch with channels flag. Inbound arrives as XML channel tags.
- **Tools:** `send_message`, `broadcast`, `reply` (threaded).
- **Maturity:** **~3★, 2 commits, v0.1** — proof-of-concept. Great design, unproven.
- **HITL:** structured JSON logs at `${TMPDIR}/bobnet-mcp-${uid}.log`.

### A3. DIY localhost patterns (no product — battle-tested glue)
No single polished product; these are what people run in production tmux setups:
- **Shared markdown "whiteboard"** — a `BOARD.md` all sessions read/write (tasks, decisions, blockers). Simplest possible; human-readable; poll-based.
- **SQLite mailbox / "taskbox"** — a shared `.db` as a message queue; often paired with GitHub Issues for a durable record.
- **`tmux send-keys` cross-talk** — one session injects keystrokes into another's pane. Caveat: send text and Enter as *separate* sends to avoid TUI paste/multiline bugs. (Open Claude Code FR [#27873](https://github.com/anthropics/claude-code/issues/27873) for a first-class programmatic sendMessage confirms this is still DIY.)
- **Named pipe / FIFO or tiny localhost HTTP relay** — possible, but no ready-made Claude-specific product; you'd build it.

---

## Approach B — Permanent bolt-on / local rendezvous broker

Persistent local service installed once; each session auto-registers a unique ID on startup; the service brokers exchange. **Reality check:** none of these implement the per-session **join-code** auth exactly as envisioned — registration is by agent ID / project path under same-machine/same-user trust. The "unique ID + join-code broker" ideal remains **DIY**.

### B1. cross-agent-teams-mcp ⭐ recommended for the persistent-daemon model
- **URL:** https://github.com/jtianling/cross-agent-teams-mcp
- **What:** Persistent local daemon giving every coding agent on the machine a **shared mailbox + wake channel**; each agent keeps running in its own native CLI. "A local message bus, not a framework."
- **Transport:** **SQLite** (`~/.cross-agent-teams-mcp/data.db`) + **HTTP daemon on :9100**; MCP over stdio. A proxy bridges Claude Code's experimental channel to the daemon for **push wake** (no polling).
- **Hook-in:** (1) `npx -y cross-agent-teams-mcp@latest daemon --port 9100`; (2) `npx mcpsmgr add jtianling/cross-agent-teams-mcp -a claude-code`; (3) launch with channels flag. Each Claude registers independently.
- **Cross-agent:** also supports Codex (WebSocket or tmux-paste fallback) and others — genuinely multi-tool.
- **Maturity:** v0.5.0, actively dogfooded; core (register, 1:1 message, broadcast, inbox, discovery) called "stable."
- **HITL:** wake notifications alert the human; SQLite inspectable.

### B2. agent-hub-mcp
- **URL:** https://github.com/gilbarbara/agent-hub-mcp
- **What:** Universal MCP coordination layer for any MCP agent — messaging + shared context + task coordination, cross-project.
- **Transport:** stdio MCP; **local file persistence** in `~/.agent-hub` (no HTTP/DB). Agent identity = project path.
- **Hook-in:** add `npx -y agent-hub-mcp@latest` to each Claude's MCP config; optional `/hub:register`, `/hub:sync`, `/hub:status` slash commands; optional hooks for "📬 N unread messages."
- **Maturity:** ~**30★**, v0.4.0 (Sep 2025), moderate activity.
- **HITL:** `/hub:status` overview, unread-message notifications, subtask visibility.

### B3. agent-comms-mcp — heavyweight, niche
- **URL:** https://github.com/watchout/agent-comms-mcp
- **Transport:** **PostgreSQL `pg_notify` + HTTP webhooks** (push). Heaviest footprint (needs Postgres; wires in Discord). Poor "ephemeral localhost" fit.
- **Maturity:** **0★ / 0 releases** but 887 commits, 180 open issues — very active but unproven/niche.
- **HITL:** all messages persisted (`fetch_messages`), in-session logs, no dashboard.

### B4. Agent-MCP (rinadelph) — shared-context / knowledge-graph flavor
- **URL:** https://github.com/rinadelph/Agent-MCP
- **What:** Multi-agent framework — "Obsidian for your AI agents": shared SQLite memory/knowledge graph, task management, **real-time dashboard with network visualization**.
- **Transport:** local server (`uv run -m agent_mcp.cli --port 8080`) + SQLite shared memory.
- **Fit:** more orchestration framework than two-peer chat, but the **strongest human-monitoring** option (live agent graph, task progress, activity timeline).
- **Maturity:** established, popular.

---

## tmux orchestrators (adjacent — mostly isolation + human dispatcher, not peer chat)

These run multiple Claude Code sessions but **most isolate agents in git worktrees with the human as dispatcher; they do NOT give two independent agents a message channel** (Tmux-Orchestrator is the exception):

- **Claude Squad** — TUI spawning N isolated sessions each in its own worktree, merge best back. Isolation, not messaging.
- **Tmux-Orchestrator** — Coordinator→Worker delegation with **two-way messaging via `tmux send-keys`** + worktrees. The canonical DIY inter-agent tmux pattern.
- **Conductor** (macOS app) / **Crystal → Nimbalyst** (desktop OSS) / **Vibe Kanban** (Apache-2.0, community-maintained) — parallel agents in worktrees with a dashboard; human is dispatcher.

Use these if the goal is a human running many agents in parallel — **not** if the goal is two peers exchanging messages.

---

## Comparison

| Tool | Approach | Transport | Peer messaging? | Localhost-only | Push (channels) | Maturity | Human monitoring |
|---|---|---|---|---|---|---|---|
| **claude-peers-mcp** | A (auto-broker) | localhost:7899 + SQLite | Yes, by peer ID | Yes | Yes + 1s poll | ~2.2k★, active | list_peers summaries, SQLite |
| **bobnet-mcp** | A (pure local) | Unix socket, same-UID | Yes + broadcast/reply | Yes | Yes | ~3★, v0.1 PoC | JSON logs |
| **cross-agent-teams-mcp** | B (persistent daemon) | SQLite + HTTP:9100 | Yes 1:1 + broadcast | Yes | Yes (wake) | v0.5, active | wake notices, SQLite |
| **agent-hub-mcp** | B (persistent, file) | stdio + ~/.agent-hub files | Yes + shared context | Yes | via hooks | ~30★, v0.4 | /hub:status, unread badges |
| **agent-comms-mcp** | B (heavy) | Postgres pg_notify + webhooks | Yes | No (needs Postgres) | Yes (webhook) | 0★/very active | persisted msgs, logs |
| **Agent-MCP** | B (framework) | local server:8080 + SQLite | Via shared memory/tasks | Yes | — | popular | **live dashboard/graph** |
| **Native agent teams** | (contrast) | JSON mailbox files | Yes (SendMessage) | Yes | built-in | experimental, official | agent panel, transcripts, hooks |
| **DIY BOARD.md / SQLite / send-keys** | A | file / SQLite / tmux | Yes (poll/inject) | Yes | No | universal, unpolished | read the file / pane |

---

## Recommendation

**Setup 1 — Easiest robust off-the-shelf (Approach A): `claude-peers-mcp`.** Most mature, truly localhost, instant push. Register once at user scope, then start each terminal with `claude --dangerously-load-development-channels server:claude-peers`. The two instances see each other via `list_peers` and exchange messages with `send_message`. Strongest "genuinely works now" answer.

**Setup 2 — Persistent broker with unique IDs + wake (closest to Approach B): `cross-agent-teams-mcp`.** Run the daemon once, register it for Claude Code, and each session auto-registers with its own ID and gets push wake on new mail. Closest thing on the market to the "install once, each session auto-registers, broker in the middle" vision — though **auth is same-machine trust, not a per-session join code**.

**Zero-dependency fallback:** a shared `BOARD.md` (or SQLite `taskbox`) both instances poll, optionally nudged with `tmux send-keys`. Ugly but bulletproof, no experimental flags, fully human-inspectable.

## Honest gaps / vaporware flags

- The **per-session join-code rendezvous broker** (Approach B ideal) does **not** exist as a polished product — registration is by ID/path under same-user trust; the join-code layer is yours to build.
- Every polished *push* option depends on the **undocumented, experimental `--dangerously-load-development-channels` "channels" API** — treat as beta.
- **bobnet-mcp** (3★ PoC) and **agent-comms-mcp** (0★) are essentially unproven.
- Native **agent teams** solve inter-agent messaging well but only *within one lead-spawned team* — they do not join two separately-launched `claude` processes.
