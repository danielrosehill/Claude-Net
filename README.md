# Claude-Net

An agent-to-agent communication layer between two people's Claude Code sessions on different machines (Linux and
Windows) and different Anthropic accounts. It runs through a relay on a home server reachable only over Tailscale.
Agents send each other tasks and updates, and flag items for either human's attention.

- `docs/research.md`: what exists (native Claude Code features, self-hostable relays) and the recommendation.
- `prior-art/`: the author's earlier iterations (Agent Junction, Agent Relay) and the July 2026 market scan, moved
  here from Multisession.
- `demo/agent-interconnect/`: the minimal viable implementation. A sanitised relay that works end to end, kept as a
  reference sample, not a product.

Status (2026-11-09): prior-art survey done; the demo is the only code. No build chosen yet.
