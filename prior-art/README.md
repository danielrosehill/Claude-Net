# Prior art: the author's own earlier iterations

Moved here from the [Multisession](https://github.com/danielrosehill/Multisession) repo on 2026-11-09, because
cross-machine agent messaging is this repo's subject. Multisession keeps the same-machine and file-mailbox line.
Home and LAN addresses and people's names were replaced with placeholders (`192.0.2.x`, `relay-host`, `alice`/`bob`)
on the way in.

- `01-agent-junction/` (2026-02 to 2026-04): an encrypted, synchronous, in-memory MCP bus.
- `02-agent-relay/` (2026-05 to 2026-07): a FastMCP + SQLite LAN relay with file transfer. This is the closest
  ancestor of `../demo/agent-interconnect/`.
- `2026-07-a2a-market-scan/` (2026-07-15): the first market scan. Its cross-machine pick was **MCP Agent Mail
  behind Tailscale Serve**, the same answer `../docs/research.md` reaches four months later with the Rust successor.

The text below is the original iterations index, unchanged except for the placeholders. "This repo" and "dead-drop"
in it mean Multisession.

---

## Earlier iterations (original index)

Dead-drop is the fourth attempt at the same problem: letting Claude Code agents working in
different places pass each other what they know, without the user relaying it by hand. The first
two attempts were separate repositories. They were folded in here on 2026-10-22 and the original
repositories deleted, so the whole line lives in one place. Git mirrors taken before deletion are
outside the repo, in the author's own backups.

| # | Name | Dates | Approach | Why it was superseded |
|---|---|---|---|---|
| 1 | [`01-agent-junction/`](01-agent-junction/) | 2026-02-17 → 2026-04-10 | **The first iteration.** TypeScript MCP server: an encrypted (AES-256-GCM), in-memory, read-once message bus on localhost or the LAN. Agents `register`, get an alias, `list_peers`, `send_message`, `read_messages`. An Electron monitor app came later. Published to npm as `agent-junction` 0.1.0. | A synchronous meeting place: both agents must be connected at the same time, a server must be running, and messages vanish on read or disconnect. Most real hand-offs are asynchronous. |
| 2 | [`02-agent-relay/`](02-agent-relay/) | 2026-05-03 → 2026-07-23 | Python FastMCP relay with SQLite sessions and a content-addressed blob store, so agents on different LAN machines could exchange messages **and files**. Shipped as the `agent-relay` plugin (8 skills). | Still a server to deploy and keep running, and a roster of client IDs to maintain, for what turned out to be mostly "leave a note for later". |
| 3 | Claude-Breakout (this repo's former name) | 2026-08-12 | Built on Claude Code's native cross-session `SendMessage` (2.1.224). An idea that does not belong in the current repo gets a new repo, a seed brief on disk, and a pinged second agent. | Native messaging made the bus unnecessary, but covered one case (founding a repo) and needed the receiver to be running. |
| 4 | dead-drop (current) | 2026-10-22 | A markdown file in the **target repo's** `a2a/` folder, with a SessionStart hook, reminders, and living messages. `SendMessage` is only the doorbell. Breakout is now one message kind. | — |

The direction across all four: from a live channel both sides must join, towards a durable note
in the place the reader already works.

## What is in these folders

Each folder is the original repository's tracked files at its last commit, with these changes:

- `package-lock.json` files, the banner image and the `.claude/` folder were left out.
- Skill folders are renamed `skills.retired/` and each `SKILL.md` is renamed `SKILL.retired.md`,
  and agent-relay's `.claude-plugin/plugin.json` is kept as `plugin.json.retired`. This stops
  plugin loaders and skill indexers from picking these up as live skills.

The code is kept as reference, not maintained. If you need a **synchronous** channel, or one that
works for agentic CLIs other than Claude Code, Agent Junction is still the better starting point:
dead-drop assumes Claude Code on both ends.

### Original commit history

Agent Junction (`danielrosehill/Agent-Junction`, 12 commits):

```
d27b1ea 2026-04-10 Add e2e test harness for peer-to-peer messaging validation
13b1da8 2026-04-10 Add light/dark theme toggle and fix Electron ESM issues
f5419a3 2026-04-10 Add electron-builder config and icons for .deb packaging
cb0a770 2026-04-10 Add real-time monitor app, event system, and Claude skills
3d5b139 2026-04-10 Add context to peer registration and wait_for_peer tool
6b808e6 2026-02-17 Add Claude Code Repos Index badge and footer link
462a6cf 2026-02-17 Add project banner image to README
f4de83b 2026-02-17 Update README with npm install instructions and Claude Code config snippet
e6b1719 2026-02-17 Rename project from Claude Junction to Agent Junction
996446d 2026-02-17 Implement Claude Junction MCP server
28c1313 2026-02-17 commit
fbec652 2026-02-17 Initial commit
```

Agent Relay (`danielrosehill/Claude-Agent-Relay-Plugin`, 4 commits):

```
519e57f 2026-07-23 Point MCP references at the live gateway
4fd8402 2026-05-03 Add onboard skill; document user-data layout
cad28e7 2026-05-03 Initial commit: agent-relay plugin (skills + MCP server)
ba87afd 2026-05-03 Write seven SKILL.md files for agent-relay plugin.
```
