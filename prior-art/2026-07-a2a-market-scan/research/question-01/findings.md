# Q1 Findings — Cross-machine A2A (local ↔ remote)

_Market scan as of 2026-07-15._

## Summary

The dominant viable pattern for two cross-machine Claude Code instances is: **put a shared HTTP MCP "mailbox" server somewhere both machines can reach, and reach it privately over Tailscale.** The strongest off-the-shelf answer is **[MCP Agent Mail](https://github.com/Dicklesworthstone/mcp_agent_mail)** (~2k★, HTTP-native) exposed via `tailscale serve` — it bundles the message bus *and* a human-monitoring web UI in one package.

Four facts shape every option:

1. **Claude Code natively connects to remote MCP servers over Streamable HTTP** (`claude mcp add --transport http <name> <url>`), with auto-reconnect (exponential backoff, ~5 attempts). This is *the* official primitive: both cross-machine instances point at the **same** HTTP MCP endpoint. ([docs](https://code.claude.com/docs/en/mcp))
2. **Claude Code cannot natively *be* an MCP/A2A server.** One instance can't directly answer another. To expose a session as a callable endpoint you need an Agent-SDK wrapper (a2claude / claude-a2a). So the realistic shape is "both instances are *clients* of a shared middle-man," not "A calls B directly."
3. **Claude Code's own multi-agent features are single-machine** (native agent teams, Claude Squad, Tmux-Orchestrator all run on one host). None spans machines.
4. **Official cross-machine A2A is an open, unstaffed feature request** — [anthropics/claude-code#28300](https://github.com/anthropics/claude-code/issues/28300). Anthropic's own suggested workaround is "a shared MCP server both machines reach." No first-party product exists; everything below is third-party or DIY.

**Consequence:** most "agent mailbox" MCP servers were built for *same-machine* use (localhost broker / shared filesystem). Going cross-machine means either (a) pick one of the few HTTP-native ones, or (b) expose a localhost broker over Tailscale.

---

## Approach A — Ephemeral secure bridge (Tailscale-trunked HTTP/MCP)

Ranked best-fit first.

### A1. MCP Agent Mail over Tailscale Serve ⭐ top pick
- **URL:** https://github.com/Dicklesworthstone/mcp_agent_mail
- **What:** "Gmail for coding agents" — identities, inboxes, searchable threads (SQLite+FTS5), git-backed human-readable message artifacts, and advisory **file leases** so agents don't clobber each other.
- **Transport:** **HTTP-only FastMCP**, server on port 8765. HTTP-native = works cross-machine out of the box (no shared filesystem needed) — the key differentiator.
- **Hook-in:** run the server on the remote box; `tailscale serve https / 8765` → `https://<host>.<tailnet>.ts.net`; each instance does `claude mcp add --transport http agentmail https://… --header "Authorization: Bearer <token>"`. Both share inboxes/threads.
- **Security:** Bearer token, optional JWT+JWKS; localhost-bypass on by default (**turn it off for tailnet use**); DOMPurify+CSP on the web UI.
- **Maturity:** Strong — **~2,000★, 850+ commits, active.** Best-maintained option.
- **HITL:** Best in class — Web UI at `/mail` to browse/search all traffic, a **"Human Overseer"** who can inject high-priority messages, fully human-auditable git history. Directly answers "monitor the traffic / take control."

### A2. Plain remote MCP mailbox over Tailscale Serve — minimal / most ephemeral
- **URLs:** [tailscale serve](https://tailscale.com/docs/reference/tailscale-cli/serve) · [Serve/Funnel](https://tailscale.com/blog/reintroducing-serve-funnel) · [Aperture MCP proxying](https://tailscale.com/docs/aperture/mcp-server)
- **What:** the generic pattern, not a product. Run *any* HTTP MCP server with send/read tools (a ~50-line FastMCP mailbox, or the claude-peers broker) on one host; `tailscale serve` publishes it inside the tailnet only; both instances add it as an HTTP MCP. Tear down = kill process + `tailscale serve --https=443 off`. Genuinely spin-up/spin-down.
- **Security:** HTTPS inside the tailnet (WireGuard) + Tailscale ACLs + TS-provisioned TLS; add a bearer token on the MCP. **Use Serve, not Funnel** — Funnel exposes to the public internet; Tailscale's own docs say don't use Funnel for normal MCP.
- **Aperture** is the productized version: aggregates remote MCP servers behind one `/v1/mcp` endpoint at a `*.ts.net` hostname with identity-based access.
- **Maturity:** Tailscale is production-grade; the mailbox stays tiny/yours.
- **HITL:** whatever you build in.

### A3. agent-comms-mcp — push-based, cross-machine by design
- **URL:** https://github.com/watchout/agent-comms-mcp
- **What:** Real-time **push** messaging (no polling; auto-injected into the session).
- **Transport:** PostgreSQL `pg_notify` + webhook/HTTP bridges (file fallback without Postgres). Explicitly cross-machine.
- **Security:** HMAC-SHA256 with replay protection, per-agent rate limiting, loop/depth detection, dedup.
- **Maturity:** **Very early — 0★, no releases** (887 commits). Promising, unproven.
- **HITL:** human-to-bot messaging on the same channel; no dedicated UI.

### A4. Redis MCP (official) / agent-switchboard — durable pub/sub over the tailnet
- **URLs:** [redis/mcp-redis](https://github.com/redis/mcp-redis) (official) · agent-switchboard (thin MCP over Redis Streams — repo currently 404s, may be renamed/removed)
- **What:** run Redis on the remote box (reachable over Tailscale); official Redis MCP exposes pub/sub + Streams (durable log, replay, consumer groups) to both instances.
- **Security:** Redis AUTH/TLS + Tailscale ACLs.
- **Maturity:** Redis MCP official/solid; the agent-mailbox glue is DIY (not mailbox-shaped OOTB).
- **HITL:** none built in (`redis-cli MONITOR` / read streams manually).

### A5. Same-machine mailboxes, forced cross-machine (fallback tier)
Polished but **built for one host** — cross-machine only by exposing their localhost broker over Tailscale or shared NFS. Prefer A1.
- **claude-peers-mcp** (https://github.com/louislva/claude-peers-mcp) — localhost broker (SQLite + HTTP `:7899`), instant channel push. Cleanest same-host peer messaging; localhost-bound.
- **cross-agent-teams / "xats"** (https://jtianling.com/en/cross-agent-teams-release.html) — local shared mailbox + wake channel.
- **cc2cc** (https://github.com/non4me/cc2cc) — JSON-file mailbox + MCP push; docs explicitly say "same machine, NFS, or shared volume." HMAC signing. 13★.
- **agent-hub-mcp** (https://github.com/gilbarbara/agent-hub-mcp) — stdio MCP, `~/.agent-hub` store, cross-project but local; no auth; 30★; `/hub:status` oversight.

---

## Approach B — Permanent bolt-on / third-party rendezvous ("meet in the middle")

**Honest headline: there is no mature, polished Approach-B product purpose-built for two Claude Codes to rendezvous via a hosted registry with per-session join codes.** The archetype exists only as (a) one immature hosted service, (b) A2A wrappers, and (c) repurposed tunnels. Ranked by closeness:

### B1. AgentTrust — closest to the described archetype (but immature)
- **URL:** https://github.com/agenttrust/mcp-server · agenttrust.ai
- **What:** Hosted, persistent platform. Each agent **registers, gets a verified identity** (`agent@agenttrust.ai`) and an **API key (`atk_…`)**; 19 MCP tools for agent-to-agent email/messaging + cloud file sharing. Matches "persistent service, auto-register a unique ID, service mediates discovery/exchange" most directly.
- **Transport:** MCP server runs locally via stdio; talks HTTPS (Bearer) to the hosted backend — both machines just add the MCP + their key. No tunnel needed (the cloud *is* the rendezvous).
- **Security:** Ed25519 message signing (keys local, never transmitted), server-side anti-spoofing, 0600 configs.
- **Maturity:** **Nascent — ~1★**, v1.2.1 (Apr 2026). Works, but unproven and routes your channel through a third party.
- **HITL:** `agenttrust_escalate` tool for human review.

### B2. a2claude / claude-a2a — expose a CC session as an A2A endpoint
- **URLs:** [a2claude writeup](https://dev.to/kanywst/a2claude-turn-claude-code-into-a-server-other-ai-agents-can-call-1mf6) · [claude-a2a](https://github.com/ericabouaf/claude-a2a)
- **What:** wrap Claude Code (via Agent SDK) as an **A2A protocol server** with an Agent Card at `/.well-known/agent-card.json`. A `contextId` is the rendezvous handle (resend to resume the session). Returns structured results (tool calls, diffs, cost, permission requests); A2A's `input-required` state parks on permission checkpoints (nice HITL).
- **Transport:** HTTP + JSON-RPC/gRPC/REST (A2A v1.0, now Linux Foundation-governed). Cross-machine via any tunnel/tailnet.
- **Fit:** the "make B answerable, A calls it" direction — true directional A2A rather than a shared mailbox; more machinery than two personal sessions need.
- **Maturity:** small OSS projects, maintained, low stars.

### B3. Generic rendezvous/relay tunnels (agent-aware-ish, transport not mailbox)
- **ngrok** (https://ngrok.com/docs/agent) — public endpoints via long-lived TLS; AI/API-gateway positioning.
- **Cloudflare Tunnel** (https://developers.cloudflare.com/tunnel/) — persistent named tunnels; official agent-facing skills for CC + Cloudflare MCP.
- **Pinggy** (https://pinggy.io/blog/best_ngrok_alternatives/) — ships a dedicated Agent Skill + MCP server for tunnel workflows (most "agent-aware" tunnel).
- **Verdict:** these mint links/tokens (your "access links") but are *dumb transport* — no agent identities or mailboxes; you still need a message server behind them. For a private two-machine case, **Tailscale Serve beats all of these** (no public exposure). `croc` / `magic-wormhole` are code-phrase *file-transfer* rendezvous, not persistent channels — not a fit despite the "join code" resemblance.

---

## Comparison

| Solution | Approach | Transport | Cross-machine? | Hookup | Auth | Maturity | HITL / monitoring |
|---|---|---|---|---|---|---|---|
| **MCP Agent Mail** | A | HTTP (FastMCP) | Yes (native) | remote HTTP MCP over Tailscale Serve | Bearer / JWT | ~2k★, very active | **Web UI, human overseer, git audit** |
| **Plain MCP + Tailscale Serve/Aperture** | A | HTTPS in tailnet | Yes | `claude mcp add --transport http` | TS ACL + TLS + token | TS production-grade | DIY |
| **agent-comms-mcp** | A | pg_notify + HTTP push | Yes (by design) | `.mcp.json` | HMAC-SHA256 | 0★, early | human-to-bot msgs |
| **Redis MCP + Redis over tailnet** | A | Redis + MCP | Yes | add Redis MCP both sides | Redis AUTH/TLS | official Redis, solid | manual (MONITOR) |
| **claude-peers-mcp** | A | localhost HTTP broker | Only via TS/NFS hack | spawns MCP per session | none (localhost) | ~2.2k★, single-host | none |
| **cc2cc** | A | JSON files + MCP push | Shared FS only | hooks + MCP | HMAC (shared key) | 13★ | none |
| **agent-hub-mcp** | A | stdio + filesystem | Local | `mcpServers` stdio | none | 30★ | `/hub:status` |
| **AgentTrust** | B | stdio→HTTPS hosted | Yes (cloud rendezvous) | add MCP + `atk_` key | Ed25519 + Bearer | ~1★, nascent | `escalate` HITL tool |
| **a2claude / claude-a2a** | B | HTTP/JSON-RPC (A2A) | Yes (+ tunnel) | wrap CC as A2A server | A2A `input-required` | small OSS | permission parking |
| **ngrok / Cloudflare / Pinggy** | B | public tunnel | Yes | need a server behind them | tunnel tokens | mature (transport only) | tunnel dashboards |

---

## Recommendation

**Setup 1 (RECOMMENDED — Approach A, batteries included).** Run **MCP Agent Mail** on the remote server. Expose it inside your tailnet only: `tailscale serve https / 8765` → `https://<remoteserver>.<tailnet>.ts.net`. On both machines: `claude mcp add --transport http agentmail https://<remoteserver>.<tailnet>.ts.net --header "Authorization: Bearer <token>"`. Both instances now share inboxes/threads/file-leases; you watch and inject via the `/mail` web UI (also over Tailscale). One package delivers the message bus **and** the human-monitoring / take-control surface; the only standing infra is one small server you start when needed. Funnel is not used, so nothing is public — fits the Tailscale-trunk preference exactly.

**Setup 2 (RECOMMENDED — Approach A, truly minimal/ephemeral).** Smallest footprint: run a lightweight HTTP MCP mailbox (claude-peers broker or a tiny FastMCP send/read server) on either machine, `tailscale serve` it, `claude mcp add --transport http` on both, add one bearer token. Tear the whole bridge down with a process kill + `tailscale serve --https=443 off`. Purest expression of "spun up on demand, torn down after."

**On Approach B:** if you specifically want the hosted-rendezvous / per-session-ID / minted-links model, **AgentTrust** is the only off-the-shelf thing shaped like it today — but it's ~1★ and routes your channel through a third party, so treat it as experimental. For a self-managed remote server you control, **Tailscale + a shared MCP (Setup 1/2) is strictly better** on security, maturity, and privacy than any Approach-B rendezvous currently on the market.

## Honest gaps / vaporware flags

- **No first-party Anthropic cross-machine solution** exists ([#28300](https://github.com/anthropics/claude-code/issues/28300) open, unstaffed).
- Most "agent mailbox" MCPs are **single-machine**; only MCP Agent Mail, agent-comms-mcp, and Redis-MCP are genuinely HTTP/network-native.
- **Approach B has no mature product** — AgentTrust is the only real match and is nascent (~1★); the "join-code rendezvous" services on the market (ngrok/Cloudflare/Pinggy) are transport, not agent-aware channels. **Genuine product gap.**
- Claude Code **cannot natively act as a server**, so true directional A2A requires the a2claude/claude-a2a SDK wrappers.
