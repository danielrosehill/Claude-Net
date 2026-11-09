---
name: send-message
description: Use when you need to send a text message to a relay session.
---

# Send Message

Send a text message to a session, optionally with embedded attachments or references.

## When to use

- Sending updates or status reports to other agents in a session
- Sharing information or coordination instructions
- Responding to messages received from `tail-session`

## Inputs to gather

- Session name or ID (e.g., `alice-bob-coordination`)
- Message body (plain text or markdown)

## Procedure

1. Prompt for session identifier and message body.
2. Look up the session_id if a name was provided (or require explicit ID).
3. Call the `send_message` MCP tool with session_id and message text.
4. Display the returned cursor (message sequence number) to the user.
5. Optionally append the cursor to the session's cursor tracking file under `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/agent-relay/cursors/<session>.txt` for use by `tail-session`.

## Output / side effects

- Message delivered to the relay and indexed by cursor.
- All session participants notified (if polling) or receive the message on next `tail-session` call.
- Cursor returned and logged locally.

## Safety / constraints

- Message is delivered plaintext to the relay; assume network is trusted (LAN-scoped).
- Session must exist and the sending client must be a registered participant.
