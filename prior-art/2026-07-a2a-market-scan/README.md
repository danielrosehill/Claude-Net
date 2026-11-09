# Claude A2A Research

> Folded in from `danielrosehill/Claude-A2A-Research` on 2026-10-22, when that repo was retired in favour of
> Claude-Dead-Drop. Point-in-time scan from July 2026; it predates Claude Code's native cross-session
> `SendMessage` (2.1.224, 2026-08-07), which changed the same-machine answer. See `../2026-10-prior-art.md`.

A time-limited research study evaluating **what tools are currently on the market** for letting two separate instances of Claude Code — running in two different terminals — communicate with each other.

> ⚠️ **Snapshot in time.** This is a point-in-time market scan (July 2026), not a continuously maintained notebook. The agent-orchestration space moves fast; treat findings as accurate as of the dates noted in each write-up.

## The challenge

Two instances of Claude Code are running as two independent sessions in two separate terminals. The goal is to create a mechanism for them to talk to one another — whether an **ephemeral bridge** (spin-up-when-needed) or a **permanent bolt-on** (persistent infrastructure). Two variants are studied:

| # | Scenario | Setup |
|---|----------|-------|
| **[Q1](research/question-01/)** | **Cross-machine** (local ↔ remote) | One instance runs locally; the other runs on a remote server the user manages (e.g. SSH session with Claude Code installed server-side). |
| **[Q2](research/question-02/)** | **Same-machine** (local ↔ local) | Both instances run on the same machine, in two different terminals. |

For each scenario the study inventories available solutions and evaluates them on setup effort, persistence model (ephemeral vs. permanent), transport, security, and fit.

## Structure

```
.
├── README.md                 # This file
├── NOTEBOOK.md               # Research log: status, method, timeline
├── research/
│   ├── question-01/          # Cross-machine (local ↔ remote)
│   │   ├── README.md         #   Question statement & scope
│   │   ├── findings.md       #   Evaluated solutions + recommendation
│   │   └── working-notes.md  #   Scratch notes, candidates, dead ends
│   └── question-02/          # Same-machine (local ↔ local)
│       ├── README.md
│       ├── findings.md
│       └── working-notes.md
├── sources/                  # Source index (SOURCES.md) + saved material
└── assets/                   # Diagrams, screenshots
```

## Headline findings (2026-07-15)

| Scenario | Recommended solution | Approach |
|----------|---------------------|----------|
| **Q1 — Cross-machine** | **[MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail)** (HTTP-native message bus) exposed via **Tailscale Serve**; both instances `claude mcp add --transport http`. Bundles a human-monitoring web UI. | A (ephemeral bridge) |
| **Q2 — Same-machine** | **[claude-peers-mcp](https://github.com/louislva/claude-peers-mcp)** (~2.2k★ localhost broker) — `list_peers` / `send_message` between any running Claude Codes. | A (localhost bridge) |

- **The market has converged on one primitive:** a shared MCP mailbox/message-bus that both instances connect to *as clients*. Claude Code can't natively act as a server, so direct A→B calls need an Agent-SDK wrapper.
- **Approach B (permanent join-code rendezvous) is a genuine product gap** — the only off-the-shelf match, [AgentTrust](https://github.com/agenttrust/mcp-server), is nascent (~1★) and third-party-hosted.
- **Caveat:** polished push delivery rides Claude Code's undocumented experimental *channels* API — treat as beta.

Full analysis in **[NOTEBOOK.md](NOTEBOOK.md)** and the per-question findings below.

## Start here

- **[NOTEBOOK.md](NOTEBOOK.md)** — status, method, and headline conclusions.
- **[Q1 findings](research/question-01/findings.md)** — cross-machine · **[Q2 findings](research/question-02/findings.md)** — same-machine
- **[sources/SOURCES.md](sources/SOURCES.md)** — all sources consulted.
