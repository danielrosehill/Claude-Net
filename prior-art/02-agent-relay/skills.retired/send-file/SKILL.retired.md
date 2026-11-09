---
name: send-file
description: Use when you need to send a file to a relay session.
---

# Send File

Upload a file to the relay blob store and attach it to a session message in one operation.

## When to use

- Sharing logs, config files, or reports between agents
- Sending binary or large-ish data (up to the relay's blob limits)
- Including files in a coordinated workflow

## Inputs to gather

- Local file path to upload
- Session name or ID
- Optional message text to accompany the file (e.g., "See attached log")

## Procedure

1. Validate that the file exists and is readable.
2. Call `upload_blob` with the local file path; receive the sha256 hash.
3. Call `attach_blob` with the session_id, sha256, filename, and guessed MIME type.
4. Optionally call `send_message` with a short description (e.g., "Attached: log.txt").
5. Display the sha256, file size, and resulting message cursor to the user.

## Output / side effects

- File stored in the relay blob store at `${sha256}`.
- Blob attached to the session as a named reference.
- Session participants can download via `download_blob` using the sha256.
- Local cursor advanced (if message sent).

## Safety / constraints

- Files are stored in plaintext on the relay; assume trust and LAN scope.
- Blob storage is content-addressed; duplicate file uploads reuse existing blobs.
- Large files may impact relay memory; document recommended limits or offer streaming download option.
