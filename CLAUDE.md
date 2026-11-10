# Claude-Net (PUBLIC repo about a PRIVATE system)

This repo is **public**. It describes a **PRIVATE** implementation (privately named Residence Claude) that is never
published. Updates to the docs here come from that private repo, through its project skill
`.claude/skills/update-public-companion/` (read it before editing `docs/`). When updating from the private repo:

- **Describe, never copy.** Write the docs fresh: descriptions, generic diagrams, small code samples with every private
  value replaced, and screenshots from a demo instance with an invented conversation. Never paste private README text,
  config, logs or real chat messages.
- **No PII, no private infrastructure.** No names except the author's as repo owner; the second person never appears in
  any form. No host or machine names, IPs, domains, tunnels, secret names, vault/item IDs, bucket names, or a person's
  devices or security software. Use the existing generic names: person-a / person-b, laptop-a, laptop-b, home-server,
  vps-1, vps-2, "a password manager", "a secrets manager", "object storage", "the gateway".
- **Screenshots:** demo instance only, metadata stripped (`exiftool -all=`), every image looked at before commit.
- **Pre-push hook:** enable once per clone with `git config core.hooksPath .githooks`. It runs the PRIVATE checker
  (denylist kept in the private repo, never copied here) over every commit being pushed, and falls back to generic IP
  and email checks if that isn't on the machine. A blocked push means rewrite the commit, not bypass the hook
  (never `--no-verify`).
- `.companion-sync.json` records the private commit and version these docs describe.
