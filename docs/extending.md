# Extending the system: checklists

Generic versions of the private system's runbooks, written 2026-11-10. Paths are relative to the (unpublished) repo.
Ids, once issued, never change.

## Add a participant

1. Choose an id (`<owner>`, `<owner>-claude` or `<machine>-claude`) and a profile: `kind` (human / agent / worker), `owner`,
   `machine`, `surface`, `account`, optional `persona`.
2. Add it to `PROFILES` in `server/app.py` (display names, the worker list and `to` validation derive from it).
3. Generate a token; add a field to the password-manager item, rebuild the combined `TOKENS` line, copy it to the secrets
   manager, write the server `.env`.
4. Add an avatar PNG (256 px circle) at `data/avatars/<id>.png` and, if it speaks, a voice in `TTS_VOICES`.
5. Add an announce clip `msg-from-<id>` to the voice bank (hidden), or senders fall back to the generic "new message" clip.
6. Redeploy the server (`git pull && docker compose up -d --build`).
7. For an interactive agent: add a gateway upstream with the token header, **re-register the upstreams and run the gateway sync**.
8. Verify: `whoami` as that participant, then send and read one message.

## Add a worker on a new machine

1. Add the profile (kind `worker`) and token as above; redeploy.
2. On the machine, as a normal (non-root) user: install Claude Code with the native installer.
3. Create `~/residence-claude-worker/` with `claude_worker.py`, `config.json` (server, token, `claude` path, `machine`
   paragraph) and `oauth_token.txt` from `claude setup-token` on the owning account (store it in the password manager and
   secrets manager first).
4. Linux: run `install.sh` (systemd user unit, linger). Windows: copy the files, run `install.ps1` (S4U scheduled task, restart
   every minute) elevated.
5. Install scripts must end any running copy of the worker (a stopped task with a surviving old process holds the single-instance port).
6. Check `worker.log` and `GET /api/workers` (heartbeat and canary should be ok), then send a trivial task from an allowed sender and expect "Started task #N" then a report.
7. If the reply is "not signed in", the token is missing or expired; the interactive login does not count.

## Add a page light action

1. Add the action to the pager service's configuration (an id, a label, the smart-home entity it switches).
2. Nothing else: the relay reads the list (cached about a minute) and the Home tab shows a button; no client release.
3. Check which lights an "all" action includes before using it for an emergency page.

## Give a participant a different voice

1. Edit the voice-assignment JSON file on the server, or delete the participant's entry to re-roll it; restart the container.
2. `whoami` and the Listen button's tooltip show the result. Voice names are Kokoro voice ids; Hebrew always uses the fallback voice.

## Add a room, a message action or a reference entry

- **Room**: created by a person in the app (members list or everyone); agents cannot create rooms.
- **Message action**: add it to the actions list on the server and name the worker that runs it; it becomes a task with the message text and the person's note.
- **Reference entry**: edit the curated reference JSON and redeploy the server; no client release.

## Add an alert sound

1. Prepare a 24 kHz mono wav; cut and fade it (`ffmpeg -ss/-to`, 20 ms fade in, 80 ms fade out, `-ac 1 -ar 24000`), peak about -4.4 dBFS.
2. Put it in `server/alerts/<name>.wav`; check the licence (CC0, public domain, free-use stock, or synthesised) and note the source.
3. Redeploy. It appears in `GET /api/alerts`; to use it as a read-aloud prefix set `AGENT_ALERT` / `REPORT_ALERT`.
4. The desktop Say dialog lists alerts from the server; the Android dialog has a fixed list and needs an app release to show a new one.

## Add a voice-bank clip

1. Add the id and text to `voicebank/clips.json` (`{"text": ..., "horns": N}` for horn blasts first; `"hidden": true` to keep it off the soundboard).
2. Run the render script (it skips existing wavs; `--force` re-renders). Occasionally one segment comes back missing: re-run to fill it.
3. Commit the wav and JSON, redeploy the server. Clips upload to object storage on first play under a content-hashed key.
4. Clients show it after their next start; no client release.

## Cut a client release

- **Desktop**: bump `__version__` in the client, commit, tag `v<that version>` (the tag must equal `__version__` or CI fails), push the
  tag. CI builds the Windows exe and Linux deb and publishes a GitHub Release. Install on each machine with the update helper.
- **Android**: no code bump (version name comes from the tag, version code from the CI run number); push `android-v<N>`. CI builds
  the signed APK, publishes the release and notifies the app repo. Use the same signing key forever. If a baked-in token changed,
  update the CI secret first.
- **Rollout**: after the release workflow is green, ping the server's refresh endpoint with any participant token; connected clients install it in the background when idle (otherwise within 15 minutes). A client older than the updater needs one manual install.
- **Server-only features** (clips, alerts, read-aloud mode, TTS, voices, reference entries, light actions) need no client release; only new client UI does.
- **Adding or renaming an MCP tool**: redeploy the server, then re-register the gateway upstreams and run its sync, or agents keep the old tool list.
