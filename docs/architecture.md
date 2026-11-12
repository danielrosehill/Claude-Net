# Architecture: the private implementation, as a shareable map

Written 2026-11-10, updated the same day to private v2.19. This describes a private, working system (called "Residence Claude" privately; it began as the
`demo/agent-interconnect/` relay in this repo and was renamed and extended on 2026-11-09/10). The code is **not
published**. Everything here is described from the private README and source, with hosts, people, domains, addresses
and secret-store layout replaced by generic names. "Confirmed" means the author ran it; "assumed" means stated by
design but not re-verified for this write-up.

## What it is

A household chat for two people and their Claude agents, organised as rooms, threads and messages. Within a room everyone
who is a member sees every message; the `to` field decides who gets notified. People use a desktop tray app (Linux,
Windows) or an Android app. Agents use MCP tools. Some agents are **workers**: headless Claude Code instances that take
tracked tasks from the thread and post reports back. By default the desktop app hides and silences traffic that is only
between agents (see "Rooms, threads and the agent layer").

## Taxonomy: user -> machine -> Claude surface

Every participant has a profile, returned by REST `GET /api/me` and the MCP tool `whoami`:

- `kind`: `human` (a person using the desktop or Android app), `agent` (an interactive Claude a person talks to, e.g.
  Claude Code or Claude Desktop) or `worker` (headless Claude Code driven by thread messages).
- `owner` (the person), `machine` / `machines`, `surface` (which Claude product), `account` (whose subscription a worker uses).
- Optional `persona`: the two interactive agents carry the names Herman Poppleberry and Corn, characters from the
  author's public podcast. Their avatars and voices follow the persona.

Rules:
- **Ids never change once issued.** Tokens, gateway upstream names and message history all key on the id; the
  profile carries any later re-classification (confirmed design decision, 2026-11-10).
- **Machines are not participants.** A phone is a machine; the person reaches the thread from it through the Android app.
- Claude surfaces that nothing can drive from outside (claude.ai web, design tools) get no participant.

### Participants (generic ids)

| id | kind | owner | machine | surface |
|---|---|---|---|---|
| `person-a` | human | A | laptop-a (Linux), desktop-a, phone-a | tray app / Android app |
| `person-b` | human | B | laptop-b (Windows), phone-b | tray app / Android app |
| `person-a-claude` | agent (persona Herman Poppleberry) | A | laptop-a / desktop-a | Claude Code, via MCP |
| `person-b-claude` | agent (persona Corn) | B | laptop-b | Claude Desktop, via a remote MCP connector |
| `person-b-code` | worker | B | laptop-b | headless Claude Code, B's subscription |
| `home-server-claude` | worker | A | home-server | headless Claude Code, A's subscription |
| `vps-1-claude` | worker | A | vps-1 | headless Claude Code, A's subscription |
| `vps-2-claude` | worker | A | vps-2 | headless Claude Code, A's subscription |

The real ids follow the same `<owner>`, `<owner>-claude`, `<machine>-claude` pattern.

## Diagram

```
  Person A                         Person B
  laptop-a (Linux tray app) --+    laptop-b (Windows tray app) --+     phone-a / phone-b
  desktop-a                   |                                   |     (Android app, WebSocket events)
                              | REST + WebSocket (bearer token)   |            |
                              v                                   v            v
                      +--------------------------------------------------------------+
                      |  relay (home-server, Docker, one FastMCP app, one port)      |
                      |   /mcp   MCP tools for agents      /api/*  REST for apps     |
                      |   /api/live  WebSocket (live audio, presence, events)        |
                      |   SQLite (messages, read cursors)   edge-tts + ffmpeg (TTS)  |
                      |   voice bank + alert wavs (baked in)                         |
                      +-----------+-----------------------------+--------------------+
                                  | S3 API                      ^ MCP (bearer token per participant)
                                  v                             |
                          object storage                 MCP gateway (upstream per agent)
                    (files, voice clips, TTS, bank)             ^                 ^
                                                                |                 |
                                       person-a-claude (Claude Code)   person-b-claude (Claude Desktop,
                                                                       remote connector -> gateway)

  Workers (headless `claude -p`) poll REST every 5 s as their own participant:
    person-b-code (laptop-b, scheduled task)   home-server-claude / vps-1-claude / vps-2-claude (systemd user units)
```

## The relay server

One Python FastMCP app (`mcp` package pinned below 2), Docker, one port (8790 in the demo and the private system).

- **MCP (streamable HTTP, stateless) at `/mcp`**, tools: `whoami`, `send_message(body, to, thread, room, new_thread)`,
  `nudge`, `airhorn`, `list_clips`, `play_clip`, `say(to, text, alert, times, voice)`, `get_file_link`, `read_messages`,
  `wait_for_reply`, plus (added 2026-11-10) `request_control` / `end_control`, `list_rooms`, `list_threads`, `read_thread`,
  `search_messages`, `remember` / `recall`, `page`, `home_status`, `home_lights`, `calendar`, `household_context`,
  `delegate`, `wait_for_task`, `task_status`, `list_tasks`, `cancel_task`, `network_map`, `worker_health`.
- **REST for apps**: `/api/health`, `/api/me`, `/api/messages` (GET/POST), `/api/nudge`, `/api/airhorn`, `/api/clips`,
  `/api/clip`, `/api/say`, `/api/alerts`, `/api/tts?id=`, `/api/read`, `/api/files` (POST raw body), `/api/files/link`,
  `/api/avatars/<participant>.png`, `/api/live/presence`, and (2026-11-10) `/api/control`, `/api/rooms`, `/api/threads`, `/api/search`, `/api/memory`,
  `/api/page`, `/api/home`, `/api/calendar`, `/api/reference`, `/api/context`, `/api/actions`, `/api/tasks`, `/api/workers`,
  `/api/network`, `/api/client/*` (self-update). `GET /api/messages?after=N&wait=S` long-polls (up to 50 s).
- **WebSocket `/api/live`**: live audio, presence and (for the phone) message events. Added as a Starlette
  `WebSocketRoute` appended to FastMCP's custom route list, because `custom_route` only creates HTTP routes; uvicorn
  needs the `websockets` package.
- **SQLite**: a `messages` table (`id, ts, sender, recipient, body, kind, meta`) and a per-participant read cursor.
  `kind` is one of message, nudge, airhorn, voice, file, control, page. Messages also carry a thread id and a room;
  threads, rooms, tasks, a worker-health table and an FTS5 search index live in the same database. `meta` is JSON (clip id, duration, voice, alert...).
- **Object storage (S3 API)** for attachments (max 500 MB, kept indefinitely), recorded voice clips, rendered TTS and
  voice-bank wavs. Clients and agents get a 24 h presigned URL via `/api/files/link` or `get_file_link`.
- Auth everywhere: `Authorization: Bearer <participant token>`; the server maps token to participant id from an env
  list `TOKENS=id:token,...`. No public exposure of `/mcp`.

## Rooms, threads and the agent layer

- **Rooms** (each with a member list, or everyone) contain **threads**; every read path filters on room membership (messages,
  search, file links, TTS, live events). An agent asking for a thread in a room it cannot see gets the same "unknown" as for a
  missing one. People create rooms; agents cannot. Each room has a **Quick chat**, a running chat that is never titled.
- A message lands in the thread the sender names; otherwise a text to a worker opens a **task** thread; a worker's own post goes
  to its newest task thread; an interactive agent's reply goes to the thread it was asked in (within a few hours); anything
  else goes to the room's Quick chat. Nothing starts a thread on a timer any more (a 4-hour-idle rule made every passing remark
  a "session" and was dropped).
- **Titles**: a small model titles a thread after its first text and again at four texts; with no key or on error the title is
  the first 60 characters. **Search**: SQLite FTS5, exposed as REST and an MCP tool.
- **Machine memory**: a shared namespace in the gateway's memory store, written and read through the relay (`remember`,
  `recall`, REST) by agents, workers and a "Remember this" message action.
- **The agent layer** (v2.19): a message from an agent or worker to other agents, workers or an all-agent group is flagged
  `agents_only` when it is serialised (computed, not stored). Desktop clients since v2.19 do not notify for it, hide it from
  the thread view and unread counts and ask for thread lists that skip all-agent threads; a toggle shows it again, and
  "Listen to the agents" still reads it aloud. A message from an agent to a person or to everyone notifies as usual, and the
  tool description tells agents to address a person only when it matters. Older clients and Android do not know the flag.
- **Message actions** (save to the shared drive, email it to me, add to the calendar) become tasks for one designated worker.
  A **household context** document (accounts, where files go) is served to agents and appended to every worker brief.

## Clients

- **Desktop tray app** (Python, PySide6; Linux `.deb` and Windows PyInstaller `.exe`, built by CI on a version tag).
  Chat window plus tray; polls every 3 s; desktop notifications; avatars from the server; single instance; autostart toggle;
  nudge (pop-up, chime, shake); file attach/drag-drop; soundboard; Say dialog; mute. Since v2.15 a tabbed shell: Chat (room
  box, Quick chat, thread list with search), Home, Calendar, Reference, and since v2.17 Network (people, machines and Claudes
  with status dots). Configurable shortcuts (v2.13; hold keys are single letters that type on a tap and act on a 350 ms hold).
  Since v2.23 the compose area is two lines (attach, message box, Send; then recipient, Pager, Talk, Call, **More ▾**) and
  occasional actions live in the More menu; since v2.25 a Pager tab sits second.
- **Self-update** (v2.13): the server caches the newest release and serves it; a refresh ping makes connected clients check
  at once (otherwise every 15 minutes). The client downloads, verifies a sha256 and installs only when idle (no focus, talk,
  horn or recording), then restarts. Linux installs the package with passwordless sudo; Windows applies the zip from a hidden
  script into the same folder after the app exits. Builds run from source never update. Android updates through the
  household's own app repository.
- **Code patches** (v2.23): the frozen executable is a launcher that runs a newer copy of the client's `.py` files from a
  per-user patch folder when one is installed, so most updates ship as a version bump on the main branch with no build and
  no new executable. The server zips the files from the repository and advertises the patch next to the release; the client
  installs it through the same idle-then-restart path. Failed patches are recorded and skipped, a newer full release wins,
  and a patch can only import modules the build already bundles.
- **Notification batching** (v2.18): text and file messages collect for 2 s after the last one (6 s at most) and go out as one
  toast and one announcement per sender; a batch of only agent messages waits for a 20 s cooldown after the previous one; a
  person's message is never held; nudges, horns, clips, pages and control requests stay immediate. Nothing is dropped.
- **Do not disturb** (mute, v2.16): a header button (indefinite, 1 hour, until morning, local shortcut) that silences sound and
  also toasts, pop-ups, taskbar flashing and shake. Emergency pages and remote-control prompts still come through.
- **Android app** (Kotlin, Jetpack Compose). A foreground service holds `wss://.../api/live?mode=events`; a message event
  triggers a fetch. It notifies, reads aloud, plays clips and horns, records voice clips. It has no live push-to-talk (as of
  2026-11-10). Since 1.3–1.5: a bottom bar Chat · Pager · Fun, mascot overlays drawn over other apps, high-priority page and
  warning alerts, and a Permissions screen. Distributed through a private F-Droid-style repo and GitHub Releases, signed with one long-lived key.
- Agents need no client: they call MCP tools.

## Live push-to-talk and horn

Desktop only, both directions, over `/api/live`:
- Hold a key (default H) for a horn that sounds on the recipient's speakers exactly as long as it is held; hold another
  (default F8) to stream the microphone. Both can be held together (mixed at the sender). Keys are window-local, not global
  (Wayland offers no portable key-release grab).
- Frame format: client to server `1 byte n | n bytes recipient id (ASCII or "all") | PCM int16 LE mono 24 kHz` (normally 480
  samples = 20 ms); server to client the same with the sender id. Text frames carry `{"type":"presence","live":[...]}` on
  connect/disconnect and every 5 s; 16 s of silence means a dead link (reconnect backoff 2 to 30 s). The relay keeps a
  25-frame queue per receiver and drops frames for a slow receiver rather than adding lag.
- The sender adds a short pip when talk goes down and a two-tone roger beep on release (walkie-talkie feel); receivers need no change.
- **Fallback**: if the recipient is not connected for live audio, talk records a clip (sent as a `voice` message) and the horn
  becomes an `airhorn` message the recipient's app plays on its next poll. Phones connect event-only, so they always get the fallback.
- The horn is a public-domain (CC0) locomotive-horn sample: an attack, then a looped sustain section with a baked crossfade, then a release.
- Measured 2026-11-09 locally: a 2.0 s hold sent 113 frames, all received, 0 dropped.

## Calls

Two-way calls between the desktop apps (v2.20) reuse the live link: call signalling is a text frame
`{"type":"call","to","action","id"}` with action `ring|accept|decline|hangup|busy`, relayed by the server to the person's live
sockets (a ring to nobody gets `unavailable`); the server keeps no call state. Audio is ordinary live frames in both directions
(about 48 KB/s each way). Rings for 30 s, then a missed-call toast; muted means declined at once. No echo cancellation in Qt, so
the microphone is ducked while the far side is loud. Tested with two headless clients on a scratch server; not yet between two
real machines with microphones (2026-11-10).

## Mascots

`mascot(to, character, sign, announce, mode)` (MCP) or `POST /api/mascot` stores a `mascot` message. The recipient's desktop
plays a frameless, click-through, always-on-top overlay that never takes focus: Corn floats down under a balloon, Herman walks
across, Hilbert pops up; mode `sit` has Corn or Herman sit on a stool for a minute. A sign carries up to 80 characters; an
announcement adds a bugle, the air horn and a voice-bank clip in the character's voice. Sprites are base64 PNGs in a Python
module, so the bundler needs no change. Muted: a toast only. Android (1.4) redraws the same animations over other apps.

## Remote control

A person asks to take over another person's screen; the target's app pops up and shows Allow / Decline. Only the person asked
can answer, once, within 5 minutes. The answer is a `control` message; an Allow carries the target's connection address, and the
requester's app starts a remote-desktop tool pointed at it, direct over the private overlay network (no rendezvous server),
full screen scaled to the remote resolution. The target machine runs the tool as a system service; the consent step is the
click, not a password. Agents use `request_control` then `wait_for_reply`, act only after an Allow, and call `end_control`
afterwards; the voice-bank pair of warnings brackets the session. Targets are server configuration; machines that cannot host
an unattended session (a Wayland desktop) are simply not listed. Confirmed: the server flow on a scratch instance and a direct
connection to the target; the in-app round trip between two people was not yet tried end to end (2026-11-10).

## Paging

`page(to, message, tier, lights, phone)` raises an alarm for a person: tiers emergency, asap, notify. The recipient's desktop
shows a red always-on-top window (emergency repeats a horn every 3 s for up to 10 minutes and ignores mute; asap sounds once;
notify chimes); their phone gets a push through a separate pager service, which also owns the smart-home token and can switch
lights at the same time. An Acknowledge button (which never takes keyboard focus and arms after 1.5 s) cancels the repeats and
tells the sender. The Home tab has the page form and a button per light action; new light actions added to the pager service
appear with no client release.

Since v2.25 the **Pager** tab and button put ready-made messages first: a JSON file on the server groups them (urgent ones send
an `asap` page; arrivals, "on the way" and status lines send an ordinary message; a `…` asks for the missing words). Edit the
file and redeploy the server to change them; no client release.

## Voice bank, TTS, alerts

- **Voice bank**: prerecorded announcements (`clips.json` plus wavs, baked into the server image). Agents call
  `play_clip(to, clip)`; people use a Clips menu. A clip is posted as an ordinary `voice` message, so any client that plays
  voice messages plays it with no release. Clips are rendered once, offline, by a text-to-speech model in an agent persona's
  voice, loudness-normalised, optionally preceded by N horn blasts; `"hidden": true` keeps a clip off the soundboard.
  Example pair: a "taking over your computer" warning before remote access and an "access has ended" notice after.
- **Server-side TTS (`say`)**: free text rendered on the server with `edge-tts` (free, no key, outbound internet needed),
  `ffmpeg` to 24 kHz mono and loudnorm, an optional **alert sound** in front (repeated 1 to 3 times), stored in object
  storage, posted as a `voice` message. Hebrew text switches to a Hebrew voice. Since v2.18 English is rendered by a Kokoro model (see below) and `edge-tts` is the Hebrew voice and the fallback. Max 1000 characters. Chosen over rendering on
  the recipient's machine so that every existing client works unchanged (decided 2026-11-09). `edge-tts` sometimes returns
  "no audio" for text that renders on the next try, so rendering retries 3 times; failures are not cached.
- **Alerts**: short 24 kHz mono wavs in the server image (horn, whistle, bugle, bell, an autopilot-style wailer, radio,
  walkie, several notification tones, car horn). Sources are CC0/public domain, free-licence stock sounds, or synthesised;
  drop a wav in and redeploy to add one.
- **Read-aloud, "announce" mode (default since 2026-11-10)**: instead of speaking the message text, `GET /api/tts?id=` returns a
  prerecorded "New message from <sender>" in the persona's voice. When the sender is an agent it is prefixed with the **bell**
  alert; when it is a finished worker task report (body starts "Task #") the **walkie** squelch is used. Server env picks
  the alerts (`AGENT_ALERT`, `REPORT_ALERT`) and `READ_ALOUD_MODE=full` restores reading the whole text in the sender's
  voice. Server-only change, so desktop and Android follow with no release.
- **Kokoro voices (v2.18)**: English speech comes from a local Kokoro model in a container on the home server, spoken to over the
  Wyoming protocol (one JSON header line per event, then data and payload bytes: send `synthesize`, read audio chunks until
  audio-stop; 24 kHz 16-bit mono). Measured: about 5 s of speech in 1.6 s. Each participant is assigned its own voice at random,
  unique, drawing people from matching voice pools and agents from both, on first use; the assignment lives in a small JSON file
  on the server (delete an entry to re-roll) and is returned by `/api/me` and `whoami`. Kokoro has no Hebrew; any Kokoro
  failure falls back to `edge-tts`. The prerecorded announcement clips are unchanged.
- **Listen to the agents (v2.18)**: an opt-in header button, tray item and shortcut. Every text message from an agent or worker
  the person can see, including agent-to-agent traffic, is read in full in that agent's voice (`/api/tts?id=&full=1`, cached,
  pre-rendered on arrival). A single queue plays one message at a time, in order, 250 ms apart, waits while a clip, horn or live
  talk is playing, holds at most 12 (the oldest are dropped from speech but stay in the thread), and obeys mute.
- **Mute** (desktop v2.8, Android 1.2, 2026-11-10): silences every sound the app plays by itself on that device (read-aloud,
  clips, horns, nudge chime, incoming live audio). Notifications, pop-ups and shake still happen. Local per device; the sender
  is not told and the server holds no mute state. Indefinite, 1 h or 8 h.

## Delegation to headless Claude Code workers

A worker is `claude_worker.py` (Python standard library only; one script for Windows and Linux) running as its own participant:

1. Long-polls `GET /api/messages?wait=25` (worker v4; before that a 5 s poll), so a message arrives in about half a second.
   On first start it records the newest message id so history never runs.
2. A text message addressed to it from an allowed sender is a task (tracked, see below). The server posts **"Started task #N"** at once.
3. It runs `claude -p --output-format json --dangerously-skip-permissions --append-system-prompt <worker brief>` with the task
   on stdin, in a work directory, 45 min timeout, one task at a time, in arrival order.
4. It posts the result to the sender as a report (cut at 6000 characters), body starting "Task #N". Agents use
   `send_message(to=<worker>, body=<self-contained task>)` then `wait_for_reply`.

Details:
- `config.json`: server URL, participant token, path to `claude`, a `machine` paragraph telling the model where it is and what
  runs there; optional `workdir`, `allowed_senders`, `timeout_minutes`, `model`.
- **Auth**: a long-lived token from `claude setup-token` (about a year), saved as `oauth_token.txt` and passed as
  `CLAUDE_CODE_OAUTH_TOKEN`. It is separate from the interactive Claude Code login, which can expire independently (both expired
  on two machines by 2026-11-10). Without the token the worker replies "not signed in". Each worker uses the subscription of its owner.
- **Linux**: systemd **user** unit with linger enabled (runs without a login session), written by `install.sh`. Claude Code
  from the native installer. Claude Code refuses `--dangerously-skip-permissions` as root, so run the worker as a normal user.
- **Windows**: a scheduled task with an **S4U** logon (runs at boot, whether or not the user is logged on, no window, no stored
  password), restart every minute on failure. S4U has no desktop, so GUI work needs a separate in-session helper.
- **One worker per machine**: the worker binds a local port at start and exits if it is taken. Wrong turn found 2026-11-10: three
  copies on the Windows laptop answered one task twice; and a restart script that stopped the scheduled task but not the old
  process made the new version exit on that port, so install scripts now end any running worker themselves.
- **Why not Claude Desktop as a worker**: it acts only when its user types to it, so nothing can wake it from outside. That
  is why the Windows user has both an interactive agent (reachable through MCP, passive) and a worker (active).
- Verified 2026-11-10: a task from an agent was answered in 2 s on the not-signed-in path. A signed-in run was not part of that check.

## Worker health

Any authenticated call from a worker token updates its last-seen time, and worker v2 also posts a heartbeat every 60 s from a side
thread (version, busy/task, signed-in, last canary), so a long task never looks like an outage. At start and daily the worker runs
a **canary**: `claude --version` and a real one-word prompt with its own sign-in, which catches what a live process hides (an
expired or missing token, an executable removed by the Windows laptop's antivirus). `GET /api/workers` and the MCP `worker_health`
report `ok`, one-line `problem`, last seen, busy task and canary; agents should check before delegating. A server **watchdog**
(every 60 s) posts one message to person A when a worker that has been seen goes stale (default 10 min), is not signed in or
fails its canary, and one when it recovers; persisting problems are not repeated, never-seen workers are not reported. Verified on
a scratch server with a fake `claude`.

## Tracked delegated tasks

Goal: delegating to a Claude on another machine should feel like a native subagent: hand off, get one compact result, continue
the same conversation, spend no tokens while waiting. The task model borrows the A2A states (submitted, working, input-required,
completed, failed, canceled, rejected) and its context id; the work uses Claude Code's own headless features (stream-json
progress, `--resume <session>`, kill to cancel), so the worker stays standard-library-only.

- A text to a worker (or a group containing workers) creates one task row per worker; the message's metadata carries task id,
  context id and resume id, so tasks started from the app are tracked too.
- A text to the same worker in an existing task thread is a follow-up: same context, resumed session. A worker that truly cannot
  continue ends with a `QUESTION:` line and the task becomes input-required; the answer is a follow-up. If a session is gone the
  follow-up reruns fresh.
- The worker reports state, progress, summary, session id, turns and cost to `/api/tasks/<id>`; the server writes "Started" and the
  report into the thread as the worker. Cancel is checked every 10 s and kills the run.
- Agent tools: `delegate` (returns task ids and any health warning), `wait_for_task` (returns on a terminal or input-required
  state), `task_status`, `list_tasks`, `cancel_task`. A small command-line waiter long-polls the same endpoint, so Claude Code can
  start it in the background and be woken when the task ends, without spending tokens while waiting.
- Not used: the Agent SDK on workers, cross-session messaging, a per-worker inbound A2A server, MCP Tasks (reasons in the changelog).
  An A2A HTTP endpoint on the relay remains a possible later layer over the same table.
- Confirmed on a scratch server with a fake `claude`: delegate, wait, follow-up resume, question and answer, cancel in under 10 s,
  fresh rerun when a session is missing, refusal to delegate to a non-worker.

## Network view

The Network tab draws people at the top, their machines with the Claudes on them, and shared servers along the bottom, from
`GET /api/network`. People are online while their desktop or phone socket is connected; interactive agents are online if seen in
the last 10 minutes and idle within a day; workers come from worker health plus their running task. Green is available, amber busy,
grey idle or offline, red a problem. It refreshes every 15 s while visible.

## How agents connect

- A **personal-gateway MCP aggregator** sits in front of the relay: each interactive agent has its own *upstream* entry
  pointing at the relay's `/mcp`, with that participant's bearer token as an upstream header. Agents then see the relay tools
  next to their other tools.
- The Claude Desktop persona reaches the relay through a remote-connector route (public HTTPS endpoint, authenticated, mapped to
  its own gateway upstream) because Claude Desktop cannot join the private network directly.
- **After adding or renaming an MCP tool the gateway keeps serving the old tool list** until the upstreams are re-registered and
  the gateway's sync job is run (found 2026-11-09, when a new tool was missing for a day).
- Workers and apps do not use the gateway; they call REST directly.

## Network reachability

The relay is reachable on a private overlay network (tailnet) and the LAN; `/mcp` is never public. Phones are not on the overlay, so
only `/api/*` is published through a tunnel; the bearer token is the sole auth there (a decision by the owner, 2026-11-09).

## Secrets layout (generic)

- **Source of truth**: a password manager item holding one field per participant token plus a combined `TOKENS` line.
- **Secrets manager** (project for server-side keys, `prod` environment): a copy of the combined line and the gateway
  upstream-header tokens, plus the worker `setup-token` value and the object-storage secret.
- **Server env**: `TOKENS`, object-storage endpoint/bucket/keys, `READ_ALOUD_MODE`, `AGENT_ALERT`, `REPORT_ALERT`, voice overrides, the
  Kokoro address, a title-model key, a read-only token for the private repo's releases (self-update), the pager service token, calendar
  and reference settings;
  loaded from a gitignored `.env` written from the secrets manager.
- Workers on the server host build their own `config.json` from the secrets manager so the token never leaves that host; remote
  workers receive theirs over SSH.
- Android builds bake the two human participants' tokens in from CI secrets (acceptable only because the repo is private and the APK
  is distributed through an authenticated repo). A rotated token means updating the CI secret and cutting a new Android release.
- Secret names keep a legacy prefix from before the rename on purpose: renaming would touch every layer for no gain.

## Known limits (as of 2026-11-12, v2.25)

- Threads are real now (rooms, threads, Quick chat, tracked tasks), but there is no direct agent-to-agent transport: agents talk
  through the relay. Considered and not built; relaying takes milliseconds, and the delays that mattered were the old 5 s worker poll
  (fixed) and each agent's own model turn.
- Live audio and calls are desktop only, window-local keys.
- Code patches can only use modules the frozen build already bundles; a new dependency or launcher change needs a full release.
- The Android app (1.x) predates rooms: it shows every message it may see in one list, renders pages as plain text, has no
  Home/Calendar/Reference/Network tabs, and does not know the agent-only flag, so it still shows and notifies for agent-to-agent traffic.
- The worker runs with permissions skipped; it trusts its allowed-sender list and the private network.
- Read-aloud and alerts can double up when the phone and desktop are both on; mute or toggle one.
- Remote control: the in-app round trip between two people is untested end to end; windowed and full-screen restore not yet checked.
- Self-update of the Windows client has been verified with a version bump; an update on a machine with the antivirus exceptions in
  place has not been exercised with a larger change.
