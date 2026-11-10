# Changelog

Dates are absolute. Versions are those of the private implementation.

## 2026-11-10

Later the same day (v2.9 to v2.19), newest first:

- **Agent layer hidden and silent by default (desktop v2.19, worker v4).** Messages an agent or worker sends to other
  agents/workers carry a computed `agents_only` flag (nothing stored, so history is covered too). Clients no longer notify
  for them, drop them from the thread view and unread counts, and ask the thread list to hide threads made only of such
  messages (7 threads became 2). A "show agent-to-agent messages" toggle brings them back; "Listen to the agents" still
  reads them. An agent writing to a person or to everyone notifies as before. Older clients and Android still show them.
- **Workers hear messages at once (worker v4).** `GET /api/messages?after=N&wait=S` (max 50 s) holds the request until a
  message arrives; workers send `wait=25`, so a task arrives in about half a second instead of up to 5 s. Wrong turn: the
  Windows worker's install script stopped the scheduled task, but the old process kept running and held the single-instance
  port, so the v4 process exited with "another worker already holds ...". The install script now ends any running worker
  process itself. Also considered and not built: a direct agent-to-agent API; relaying through the server takes
  milliseconds, the real delays were the 5 s poll and each agent's own model turn.
- **Kokoro voices, "Listen to the agents", notification batching (v2.18).** English speech is now rendered by a Kokoro model
  in a container already on the home server, spoken to over the Wyoming protocol (JSON header line per event, then data and
  payload bytes; send `synthesize`, read audio chunks until audio-stop); a 5 s sentence rendered in under 2 s. Every
  participant gets its own voice, chosen at random and unique on first use, stored in a small JSON file on the server and
  shown by `whoami`. Hebrew still uses `edge-tts`, and any Kokoro failure falls back to it. A header button, tray item and
  shortcut turn on "Listen to the agents": every agent message the person can see is read in full in that agent's voice,
  through a one-at-a-time queue (250 ms between turns, waits for clips and live audio, capped at 12, oldest dropped). Text
  and file messages are batched (2 s debounce, 6 s max wait, one toast and one announcement per sender), and agent-only
  batches are spaced at least 20 s apart; a person's message is never held; nothing is dropped.
- **Tracked delegated tasks and a Network tab (v2.17, worker v3).** A `tasks` table with A2A-style states (submitted,
  working, input-required, completed, failed, canceled, rejected) and a context id. A follow-up in a task thread resumes the
  same Claude session; a worker ends with a `QUESTION:` line to ask something; cancel kills the run within 10 s; if a session
  is gone the follow-up reruns fresh. MCP tools `delegate`, `wait_for_task`, `task_status`, `list_tasks`, `cancel_task`,
  `network_map`; a small CLI waits in the background so a Claude Code session spends no tokens while a worker runs. Decided
  against: wrapping the Agent SDK on workers (same CLI plus more packages), cross-session messaging (single account, plain
  text), an inbound-port A2A server per worker (would need a firewall rule on the Windows laptop; workers only connect out),
  and MCP Tasks (gateway pass-through untested). The Network tab draws people, their machines and the Claudes on them with
  status dots, refreshed every 15 s; clicking a Claude fills the To box.
- **Worker health (worker v2).** A heartbeat every 60 s from a side thread, a daily canary (`claude --version` plus a one-word
  prompt with the worker's own sign-in), `GET /api/workers` and an MCP `worker_health`, and a server watchdog that posts one
  alert to person A when a worker goes stale, loses its sign-in or fails the canary, and one when it recovers. Found on the
  way: a script that was meant to store the worker token failed silently on its first run, so the token was saved by hand;
  and restarting a worker with `pkill -f` inside an SSH command kills the SSH session's own shell (use the service manager).
  Another wrong turn: the Windows laptop had three copies of the worker polling, so one task got two answers; the worker now
  binds a local port at start and exits if it is taken.
- **Mute is a header button and full do-not-disturb (v2.16).** One click in the window header; options for 1 hour or until
  morning; a mute now also suppresses toasts, pop-ups, taskbar flashing and shake. Emergency pages and remote-control prompts
  still get through by design.
- **Rooms, Quick chat, paging, Home, Calendar, Reference (v2.15).** Rooms contain threads; a room can be limited to people
  only, and every read path (messages, search, files, TTS, WebSocket events) filters on room membership. Each room has a
  running Quick chat that is never titled, with one-tap quick replies. Paging has three tiers (emergency, asap, notify): a
  red always-on-top window on the target's desktop (emergency repeats a horn and ignores mute) plus a phone push, and can
  switch smart-home lights at the same moment. Tabs: Home (page form, light buttons, status), Calendar (events from a shared
  calendar through the gateway), Reference (a curated page plus live sections from the household's launcher page). Message
  actions (save to the shared drive, email it to me, add to the calendar) become tasks for one worker; "remember this"
  writes to machine memory. Agents get a household-context document, and workers append it to every task. Wrong turn: a
  stray keystroke acknowledged a page the instant it appeared, so the Acknowledge button never takes keyboard focus and arms
  after 1.5 s. Decided against moving onto a chat framework (Matrix): it would mean rewriting the tools, workers, live audio
  and both clients.
- **Self-update (v2.13, first delivered by v2.14).** The server reads the private repo's releases with a read token, caches the
  newest Windows zip and Linux deb, and serves them; a refresh ping broadcasts an `update` event over the WebSocket. Clients
  download, verify a sha256 and install only when idle, then restart themselves. Windows applies the update from a hidden
  script after the app exits, into the same folder, so exceptions on that path stay valid. Verified: both clients updated
  within 5 s of the ping. Also in v2.13: tabbed Settings with configurable shortcuts, push-to-talk moved to T.
- **Titled threads, full-text search and shared machine memory (v2.11).** Messages belong to threads; a small model titles
  each one after its first text and again at four texts (fallback: first 60 characters). Wrong turns: routing the title
  model through an aggregator whose guardrail blocks every Anthropic model; asking the model to think (it spent the whole
  budget thinking); taking the wrong block of a reply; counting a fallback title as final. SQLite FTS5 search (an
  external-content index needs rebuilding at start, because its row count reads the base table and cannot show whether the
  index exists). A shared "machine memory" namespace in the gateway's memory store, reachable by agents (`remember`,
  `recall`) and by workers over REST.
- **Groups and remote control (v2.9).** Group ids (a person's machines, all servers) address several participants. A request
  button asks to take over another person's screen; the target gets an Allow / Decline box, and only an Allow releases the
  connection address to the requester, who then opens the remote-desktop tool directly over the private network, full screen.
  Agents use `request_control` then `wait_for_reply`.
- **Windows build lessons (v2.10, v2.12).** The Windows laptop's antivirus quarantined the one-file executable on first launch,
  including its per-launch unpack folder, then the shortcut and autostart entry, and afterwards blocked creating anything at
  those exact paths. Fixes: a one-folder build at a fixed install path (nothing unpacks to a temp folder each launch), a
  renamed executable and autostart value, and exceptions added for the install, staging and worker folders. Unzipping over SSH
  with a PowerShell cmdlet left the folder empty without an error; the system `tar` worked.
- **Backups.** A six-hourly consistent database snapshot and an additive copy of the file bucket go to off-site object storage;
  restore was tested.

- Taxonomy: user -> machine -> Claude surface. Profiles (`kind` human / agent / worker) on every participant, returned by `/api/me` and `whoami`.
- Workers: headless Claude Code (`claude -p`) driven by thread messages, Started/Report protocol. The worker script was generalised
  to Windows and Linux; four workers (one Windows laptop, three Linux hosts), `claude setup-token` auth.
- Read-aloud default changed to "announce" (prefix alert plus "New message from X"); bell for agents, walkie for worker reports.
  A wailer-style alert was tried for reports for about an hour and dropped as too jarring.
- New alerts: bell, an autopilot-style wailer, and several stock sounds (radio, walkie, notification tones, message alert).
- Mute: desktop v2.8, Android 1.2.
- Observed: interactive Claude Code logins on two machines had expired; worker tokens are separate.

## 2026-11-09

- Relay from `demo/agent-interconnect/` renamed and extended to v2.0; participants, avatars and personas added.
- Files: attach and presigned links via object storage (500 MB cap).
- Voice clips and airhorn messages (v2.2).
- Live push-to-talk and hold-to-sustain horn over WebSocket with fallback to clips (v2.3); a separate stopgap relay built the same day was retired.
- Voice bank and soundboard (v2.4); server-side `say` TTS with alert sounds (v2.5); read-aloud of text messages (v2.6);
  walkie-talkie pips on talk (v2.7).
- Android app (Kotlin/Compose) with an event WebSocket, notifications, read-aloud and a one-tap person picker (1.1).
- Found: after adding an MCP tool the gateway kept the old tool list until its upstreams were re-registered.
- Before this: research and prior art in this repo (see `research.md`).
