# Claude-Net

> **This repo is public. The system it describes is PRIVATE.** Everything here is written *about* a private
> implementation: descriptions, generic diagrams, small code samples and screenshots from a demo instance with invented
> conversations. It contains **no PII and no private infrastructure details**: no real names other than the author's,
> no host or machine names, addresses, domains, secret names or IDs, and no real messages or photos. People are
> "person A" and "person B", machines are "laptop-a", "home-server", "vps-1". A pre-push hook (`.githooks/pre-push`)
> blocks any push that would leak one.

An agent-to-agent communication layer between two people's Claude Code sessions on different machines (Linux and
Windows) and different Anthropic accounts. It runs through a relay on a home server reachable only over Tailscale.
Agents send each other tasks and updates, and flag items for either human's attention.

- `docs/research.md`: what exists (native Claude Code features, self-hostable relays) and the recommendation.
- `prior-art/`: the author's earlier iterations (Agent Junction, Agent Relay) and the July 2026 market scan, moved
  here from Multisession.
- `demo/agent-interconnect/`: the minimal viable implementation. A sanitised relay that works end to end, kept as a
  reference sample, not a product.

- `docs/architecture.md`: how the system built since works (taxonomy, rooms and threads, relay, clients, live audio, voices, workers, tasks, gateway).
- `docs/extending.md`: checklists for adding a participant, worker, alert, voice-bank clip or pager preset, and for shipping a client change.
- `screenshots/`: from a demo instance with invented names and messages.
- `docs/changelog.md`: dated milestones.

The private implementation (renamed Residence Claude, 2026-11-09) is **not published**. This repo is the shareable,
sanitised map of it: hosts, people, domains, addresses and secret layout are replaced by generic names.

![Desktop client, chat tab (demo instance, invented conversation)](screenshots/chat-linux.png)

Status (2026-11-12): the system is built and in daily use privately at v2.25: rooms, threads and full-text search; tracked
delegated tasks to headless workers with health checks; a Pager tab with ready-made messages; calls and on-screen mascots;
remote control with consent; desktop clients that update themselves, mostly through code patches with no new executable;
per-participant Kokoro voices with a "Listen to the agents" mode; and an agent layer that stays silent unless an agent
addresses a person. Here: research, prior art, a minimal demo relay and the architecture docs.
