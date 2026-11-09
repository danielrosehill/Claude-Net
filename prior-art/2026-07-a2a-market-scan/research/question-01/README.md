# Q1 — Cross-machine A2A (local ↔ remote)

## Question

Two instances of Claude Code are running in two separate terminals:

- **Instance A** runs on the **local** machine.
- **Instance B** runs on a **remote server the user manages** — e.g. the user is SSHed into the server and Claude Code is installed there, running server-side.

**What mechanisms currently on the market let these two instances communicate with each other?** The bridge may be **ephemeral** (spun up on demand for a session) or a **permanent bolt-on** (persistent infrastructure the user installs once).

## Two approaches under evaluation

Each candidate is classified into one of two archetypes:

- **Approach A — Ephemeral secure bridge / comms layer.** Spun up on demand for a session and torn down after. For the cross-machine case the natural transport trunk is **Tailscale** (tailnet-private connectivity between the two machines), carrying whatever channel the agents speak over (HTTP/MCP, socket, message queue). Emphasis: minimal standing infrastructure, secure-by-default network path.
- **Approach B — Permanent bolt-on / third-party rendezvous ("meet in the middle").** A persistent layer the user installs once. On startup each Claude Code session **auto-registers a unique ID**; connectivity is authenticated via a **join code** per session. The rendezvous service mints two access links/tokens so the two agents can discover and exchange information directly. Emphasis: reusable, addressable, auth built in.

## Scope & evaluation criteria

Solutions are evaluated on:

- **Persistence model** — ephemeral bridge vs. permanent install.
- **Transport** — how messages cross the machine boundary (SSH, HTTP/MCP, message bus, shared queue, tunnel).
- **Setup effort** — what the user must install/configure on each side.
- **Directionality** — one-way handoff vs. bidirectional conversation.
- **Security** — exposure across the network boundary, auth, encryption.
- **Human-in-the-loop** — can a human **monitor** the cross-agent traffic, **take control** of a session / interrupt it, manage **session state**, handle **disconnection/reconnection** gracefully, and inspect **logs/transcripts** of the exchange? Who owns the audit trail on each side of the boundary?
- **Maturity** — off-the-shelf product vs. DIY pattern.

## Out of scope

- Same-machine communication (that is [Q2](../question-02/)).
- Building a bespoke protocol from scratch (we catalogue what exists).

## Findings

See **[findings.md](findings.md)**. Working notes and candidate list in **[working-notes.md](working-notes.md)**.
