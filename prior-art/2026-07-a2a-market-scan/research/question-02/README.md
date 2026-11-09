# Q2 — Same-machine A2A (local ↔ local)

## Question

Two instances of Claude Code are running as two independent sessions in **two different terminals on the same machine**.

**What mechanisms currently on the market let these two instances communicate with each other?** As with [Q1](../question-01/), the bridge may be **ephemeral** (spun up on demand) or a **permanent bolt-on** (persistent local infrastructure).

## Two approaches under evaluation

Each candidate is classified into one of two archetypes:

- **Approach A — Ephemeral secure bridge / comms layer.** Spun up on demand and torn down after. On a single machine this can be **fully localhost** — a loopback socket, shared file/named pipe, or a local MCP server bound to `127.0.0.1` — with no network exposure at all. (Tailscale is available as a trunk too, but is unnecessary when both peers are local.) Emphasis: zero standing infrastructure.
- **Approach B — Permanent bolt-on / third-party rendezvous ("meet in the middle").** A persistent layer installed once. On startup each Claude Code session **auto-registers a unique ID**; connectivity is authenticated via a **join code** per session. The service mints two access links/tokens so the two agents can discover and exchange information directly. Emphasis: reusable, addressable, auth built in.

## Scope & evaluation criteria

Solutions are evaluated on:

- **Persistence model** — ephemeral bridge vs. permanent install.
- **Transport** — how the two local processes exchange messages (shared files, local socket/MCP server, tmux, named pipes, local message bus).
- **Setup effort** — what the user must install/configure.
- **Directionality** — one-way handoff vs. bidirectional conversation.
- **Coordination model** — peer-to-peer vs. orchestrator/worker.
- **Human-in-the-loop** — can a human **monitor** the traffic between the two agents, **take control** of a session / interrupt it, manage **session state**, handle **disconnection/reconnection**, and inspect **logs/transcripts** of the exchange? (On a single machine, tmux-style attach/detach and shared log files make this especially tractable.)
- **Maturity** — off-the-shelf product vs. DIY pattern.

## Out of scope

- Cross-machine / remote communication (that is [Q1](../question-01/)).
- Claude Code's built-in subagents (`Task` tool) where the parent spawns children within one session — the question is about **two separately-launched top-level instances**. (Noted for contrast, not as the answer.)

## Findings

See **[findings.md](findings.md)**. Working notes and candidate list in **[working-notes.md](working-notes.md)**.
