# Source Index

Sources consulted during the market scan (July 2026), grouped by scenario. Some sources appear in both.

## Q1 — Cross-machine

- Claude Code MCP (remote HTTP/SSE, reconnection): https://code.claude.com/docs/en/mcp
- Cross-machine A2A feature request (open, unstaffed): https://github.com/anthropics/claude-code/issues/28300
- **MCP Agent Mail** (top pick): https://github.com/Dicklesworthstone/mcp_agent_mail
- agent-comms-mcp: https://github.com/watchout/agent-comms-mcp
- cc2cc: https://github.com/non4me/cc2cc
- Redis MCP (official): https://github.com/redis/mcp-redis
- agent-switchboard (Redis Streams MCP; repo currently 404): https://github.com/vitaminR/agent-switchboard
- **AgentTrust** (Approach-B rendezvous): https://github.com/agenttrust/mcp-server
- a2claude (turn CC into an A2A server): https://dev.to/kanywst/a2claude-turn-claude-code-into-a-server-other-ai-agents-can-call-1mf6
- claude-a2a: https://github.com/ericabouaf/claude-a2a
- Tailscale Serve: https://tailscale.com/docs/reference/tailscale-cli/serve
- Tailscale Serve/Funnel: https://tailscale.com/blog/reintroducing-serve-funnel
- Tailscale Aperture MCP proxying: https://tailscale.com/docs/aperture/mcp-server
- Tunnels: https://ngrok.com/docs/agent · https://developers.cloudflare.com/tunnel/ · https://pinggy.io/blog/best_ngrok_alternatives/
- A2A protocol background (AWS): https://aws.amazon.com/blogs/opensource/open-protocols-for-agent-interoperability-part-1-inter-agent-communication-on-mcp/

## Q2 — Same-machine

- **claude-peers-mcp** (top pick): https://github.com/louislva/claude-peers-mcp · fork: https://github.com/jamditis/claude-peers-mcp
- bobnet-mcp (pure-localhost Unix socket, PoC): https://github.com/cath42/bobnet-mcp
- **cross-agent-teams-mcp** (persistent daemon): https://github.com/jtianling/cross-agent-teams-mcp · https://jtianling.com/en/cross-agent-teams-release.html
- agent-hub-mcp: https://github.com/gilbarbara/agent-hub-mcp
- agent-comms-mcp: https://github.com/watchout/agent-comms-mcp
- Agent-MCP (rinadelph, shared-context + dashboard): https://github.com/rinadelph/Agent-MCP
- Native agent teams (single-machine mailbox reference): https://code.claude.com/docs/en/agent-teams
- Programmatic sendMessage FR: https://github.com/anthropics/claude-code/issues/27873
- Claude Squad: https://www.claudemod.com/mods/claude-squad · https://github.com/smtg-ai/claude-squad
- Tmux-Orchestrator: https://github.com/absmartly/Tmux-Orchestrator · https://github.com/hesreallyhim/awesome-claude-code/issues/1279
- Conductor: https://www.conductor.build/
- Crystal → Nimbalyst / Vibe Kanban: https://nimbalyst.com/blog/best-agent-management-tools-2026/
- DIY BOARD.md / SQLite taskbox: https://dev.to/alanwest/how-to-coordinate-multiple-claude-code-agents-without-losing-your-mind-1i9f
- tmux + shared queue guide: https://www.epam.com/insights/ai/blogs/step-by-step-guide-to-building-a-multi-agent-claude-code-ai-development-team
- swarm / TeammateTool patterns: https://gist.github.com/kieranklaassen/4f2aba89594a4aea4ad64d753984b2ea

## Shared / background

- Claude Code MCP docs: https://code.claude.com/docs/en/mcp
- Claude Code agent teams docs: https://code.claude.com/docs/en/agent-teams
- The **experimental "channels" API** (`claude --dangerously-load-development-channels server:<name>`) underpins push delivery in claude-peers-mcp, bobnet-mcp, and cross-agent-teams-mcp — undocumented/beta.
