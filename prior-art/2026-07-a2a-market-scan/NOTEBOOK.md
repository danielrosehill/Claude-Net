# Research Notebook

## Study

Point-in-time market scan: **what tools currently exist to let two separate Claude Code instances (two terminals) communicate?** Two scenarios — cross-machine ([Q1](research/question-01/)) and same-machine ([Q2](research/question-02/)).

## Method

1. Define the two question scenarios precisely (done).
2. Market scan — inventory candidate tools/patterns per scenario via web research (GitHub projects, MCP registries, Anthropic docs, community write-ups).
3. Evaluate each candidate against the criteria in each question's README.
4. Write up `findings.md` per question with a recommendation; log all sources in `sources/SOURCES.md`.

## Timeline

| Date | Entry |
|------|-------|
| 2026-07-15 | Repo created; two-question scope defined; research kicked off. |
| 2026-07-15 | Market scan complete for both scenarios; findings + sources written up. |

## Status

| Question | Scenario | Status | Top pick |
|----------|----------|--------|----------|
| [Q1](research/question-01/findings.md) | Cross-machine (local ↔ remote) | ✅ Complete | MCP Agent Mail over Tailscale Serve |
| [Q2](research/question-02/findings.md) | Same-machine (local ↔ local) | ✅ Complete | claude-peers-mcp (localhost) |

## Headline conclusions

- **The market has converged on one primitive: a shared MCP "mailbox"/message-bus server that both Claude Code instances connect to as clients.** Claude Code cannot natively *be* a server, so direct A→B calls require an Agent-SDK wrapper (a2claude/claude-a2a); the practical pattern is both instances as clients of a middle-man.
- **Approach A (ephemeral bridge) is well-served and is the recommendation in both scenarios.** Same-machine: `claude-peers-mcp` (localhost broker, ~2.2k★). Cross-machine: `MCP Agent Mail` on an HTTP MCP exposed via **Tailscale Serve** (not Funnel — Serve keeps it tailnet-private).
- **Approach B (permanent bolt-on / join-code rendezvous) is a genuine product gap.** The only off-the-shelf match is **AgentTrust** (~1★, nascent, routes through a third party). The per-session join-code broker as envisioned would have to be built.
- **Human-in-the-loop varies sharply.** `MCP Agent Mail`'s web UI + "human overseer" is best-in-class for monitoring/taking control; most others expose only SQLite/logs or a status command.
- **Caveat:** the polished *push* (no-poll) delivery in the localhost tools rides Claude Code's undocumented, experimental **channels** API (`--dangerously-load-development-channels`). Treat as beta.
