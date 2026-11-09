---
name: tail-session
description: Use when you need to read new messages from a relay session.
---

# Tail Session

Stream new messages from a session, starting from the last known cursor.

## When to use

- Polling for updates from other agents in a session
- Checking for new files or coordination messages
- Continuous monitoring with `--follow` option

## Inputs to gather

- Session name or ID
- Optional `--follow` flag (loop continuously, checking for new messages every 2–5 seconds)

## Procedure

1. Prompt for session identifier and optional `--follow` flag.
2. Load the last known cursor from `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/agent-relay/cursors/<session>.txt` (default to 0 if file doesn't exist).
3. Call `read_inbox` with the session_id and since_cursor parameter.
4. Parse the TOON response to extract messages, attachments, and metadata.
5. Render each message in human-readable form (sender, timestamp, body, attachments list).
6. Update the cursor file with the latest cursor from the response.
7. If `--follow` is set, loop back to step 3 after a short sleep (2–5 seconds); otherwise exit.

## Output / side effects

- Messages printed to stdout in a readable format.
- Cursor file updated under `$CLAUDE_USER_DATA/agent-relay/cursors/`.
- Blobs listed by sha256 and filename; user can fetch via `download_blob` if needed.
- Continuous tail mode exits on Ctrl+C.

## Safety / constraints

- Cursor tracking is per-session, per-client; each instance maintains independent state.
- TOON parsing should handle empty or malformed responses gracefully.
- Long-running `--follow` processes should log or summarize activity periodically.
