# Changelog

Dates are absolute. Versions are those of the private implementation.

## 2026-11-10

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
