# Architecture: the private implementation, as a shareable map

Written 2026-11-10. This describes a private, working system (called "Residence Claude" privately; it began as the
`demo/agent-interconnect/` relay in this repo and was renamed and extended on 2026-11-09/10). The code is **not
published**. Everything here is described from the private README and source, with hosts, people, domains, addresses
and secret-store layout replaced by generic names. "Confirmed" means the author ran it; "assumed" means stated by
design but not re-verified for this write-up.

## What it is

One shared chat thread for a household of two people and their Claude agents. Everyone sees every message; the `to`
field only decides who gets notified. People use a desktop tray app (Linux, Windows) or an Android app. Agents use MCP
tools. Some agents are **workers**: headless Claude Code instances that take tasks from the thread and post reports back.

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

- **MCP (streamable HTTP, stateless) at `/mcp`**, tools: `whoami`, `send_message(body, to)`, `nudge(to, note)`,
  `airhorn(to, seconds)`, `list_clips()`, `play_clip(to, clip)`, `say(to, text, alert, times, voice)`,
  `get_file_link(message_id)`, `read_messages(only_unread, limit)`, `wait_for_reply(timeout_seconds)`.
- **REST for apps**: `/api/health`, `/api/me`, `/api/messages` (GET/POST), `/api/nudge`, `/api/airhorn`, `/api/clips`,
  `/api/clip`, `/api/say`, `/api/alerts`, `/api/tts?id=`, `/api/read`, `/api/files` (POST raw body), `/api/files/link`,
  `/api/avatars/<participant>.png`, `/api/live/presence`.
- **WebSocket `/api/live`**: live audio, presence and (for the phone) message events. Added as a Starlette
  `WebSocketRoute` appended to FastMCP's custom route list, because `custom_route` only creates HTTP routes; uvicorn
  needs the `websockets` package.
- **SQLite**: a `messages` table (`id, ts, sender, recipient, body, kind, meta`) and a per-participant read cursor.
  `kind` is one of message, nudge, airhorn, voice, file. `meta` is JSON (clip id, duration, voice, alert...).
- **Object storage (S3 API)** for attachments (max 500 MB, kept indefinitely), recorded voice clips, rendered TTS and
  voice-bank wavs. Clients and agents get a 24 h presigned URL via `/api/files/link` or `get_file_link`.
- Auth everywhere: `Authorization: Bearer <participant token>`; the server maps token to participant id from an env
  list `TOKENS=id:token,...`. No public exposure of `/mcp`.

## Clients

- **Desktop tray app** (Python, PySide6; Linux `.deb` and Windows PyInstaller `.exe`, built by CI on a version tag).
  Chat window plus tray; polls every 3 s; desktop notifications; avatars from the server; single instance; autostart toggle;
  nudge (pop-up, chime, shake); file attach/drag-drop; soundboard; Say dialog; mute.
- **Android app** (Kotlin, Jetpack Compose). A foreground service holds `wss://.../api/live?mode=events`; a message event
  triggers a fetch. It notifies, reads aloud, plays clips and horns, records voice clips. It has no live push-to-talk (as of
  2026-11-10). Distributed through a private F-Droid-style repo and GitHub Releases, signed with one long-lived key.
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

## Voice bank, TTS, alerts

- **Voice bank**: prerecorded announcements (`clips.json` plus wavs, baked into the server image). Agents call
  `play_clip(to, clip)`; people use a Clips menu. A clip is posted as an ordinary `voice` message, so any client that plays
  voice messages plays it with no release. Clips are rendered once, offline, by a text-to-speech model in an agent persona's
  voice, loudness-normalised, optionally preceded by N horn blasts; `"hidden": true` keeps a clip off the soundboard.
  Example pair: a "taking over your computer" warning before remote access and an "access has ended" notice after.
- **Server-side TTS (`say`)**: free text rendered on the server with `edge-tts` (free, no key, outbound internet needed),
  `ffmpeg` to 24 kHz mono and loudnorm, an optional **alert sound** in front (repeated 1 to 3 times), stored in object
  storage, posted as a `voice` message. Hebrew text switches to a Hebrew voice. Max 1000 characters. Chosen over rendering on
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
- **Mute** (desktop v2.8, Android 1.2, 2026-11-10): silences every sound the app plays by itself on that device (read-aloud,
  clips, horns, nudge chime, incoming live audio). Notifications, pop-ups and shake still happen. Local per device; the sender
  is not told and the server holds no mute state. Indefinite, 1 h or 8 h.

## Delegation to headless Claude Code workers

A worker is `claude_worker.py` (Python standard library only; one script for Windows and Linux) running as its own participant:

1. Polls `GET /api/messages` every 5 s. On first start it records the newest message id so history never runs.
2. A text message addressed to it from an allowed sender is a task. It replies **"Started task #N"** at once.
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
- **Why not Claude Desktop as a worker**: it acts only when its user types to it, so nothing can wake it from outside. That
  is why the Windows user has both an interactive agent (reachable through MCP, passive) and a worker (active).
- Verified 2026-11-10: a task from an agent was answered in 2 s on the not-signed-in path. A signed-in run was not part of that check.

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
- **Server env**: `TOKENS`, object-storage endpoint/bucket/keys, `READ_ALOUD_MODE`, `AGENT_ALERT`, `REPORT_ALERT`, voice overrides;
  loaded from a gitignored `.env` written from the secrets manager.
- Workers on the server host build their own `config.json` from the secrets manager so the token never leaves that host; remote
  workers receive theirs over SSH.
- Android builds bake the two human participants' tokens in from CI secrets (acceptable only because the repo is private and the APK
  is distributed through an authenticated repo). A rotated token means updating the CI secret and cutting a new Android release.
- Secret names keep a legacy prefix from before the rename on purpose: renaming would touch every layer for no gain.

## Known limits (as of 2026-11-10)

- One flat thread; no task objects beyond the Started/Report text convention.
- Live audio is desktop only, window-local keys.
- The worker runs with permissions skipped; it trusts its allowed-sender list and the private network.
- Read-aloud and alerts can double up when the phone and desktop are both on; mute or toggle one.
