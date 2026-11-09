---
name: create-session
description: Use when you need to create a new session for participants to communicate through.
---

# Create Session

Create a named messaging session on the relay between two or more client participants.

## When to use

- Starting a conversation between agents for the first time
- Creating separate communication channels for different projects or purposes
- Organizing message groups by topic or team

## Inputs to gather

- Session name (kebab-case, e.g., `alice-bob-coordination`)
- List of participant client_ids (e.g., `claude-alice-desktop`, `claude-bob-laptop`)
- Optional description (purpose or context for the session)

## Procedure

1. Prompt for session name, participants list, and optional description.
2. Validate that the session name is kebab-case and participants list is non-empty.
3. Call the `create_session` MCP tool with name, participants array, and description.
4. Display the returned session_id to the user.
5. Optionally save the session_id locally to `${CLAUDE_USER_DATA:-${XDG_DATA_HOME:-$HOME/.local/share}/claude-plugins}/agent-relay/sessions.txt` for reference.

## Output / side effects

- New session created on the relay with a unique session_id.
- Session is immediately available for `send-message` and `tail-session` operations.
- Local reference file (optional) updated with session name and id.

## Safety / constraints

- Session names are unique on the relay; duplicates are rejected by the server.
- All participants must be registered clients; the relay validates this at creation time.
