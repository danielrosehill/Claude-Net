# Claude-Net

An agent-to-agent communication layer between two people's Claude Code sessions on different machines (Linux and
Windows) and different Anthropic accounts. It runs through a relay on a home server reachable only over Tailscale.
Agents send each other tasks and updates, and flag items for either human's attention.

- `docs/research.md`: what exists (native Claude Code features, self-hostable relays) and the recommendation.
- `demo/agent-interconnect/`: a sanitised scratchpad relay that already works, kept as a reference.

Status (2026-11-09): research done, no build chosen yet.
