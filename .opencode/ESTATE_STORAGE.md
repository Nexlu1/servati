# Estate Storage Policy

- Treat `C:` as the Windows/system drive. Do not intentionally create, edit,
  extract, build, cache, or store project data there.
- Use `E:` for persistent repositories, tools, and application assets.
- Use `F:` for build output, caches, temporary files, downloaded dependencies,
  extraction, logs, generated artifacts, and other high-write workloads.
- Use `G:` for archives, backups, and final large result packages when useful.
- For this project, use `F:\RIG_LAB\10_TEMP\USER\opencode\servati-codex` as the
  writable scratch root. Never use `%USERPROFILE%`, `%LOCALAPPDATA%`, or a path
  under `C:\Users` as project scratch space.
- Existing Windows software may execute from `C:` and Windows may perform normal
  system writes there. Do not move or alter system components.
- Never read or edit `.env`, private keys, credentials, tokens, or secrets unless
  the user explicitly authorizes that exact need. Keep unrelated personal
  directories outside the project boundary.
- Keep recursive deletion, history rewriting, force pushes, disk operations, and
  other genuinely destructive actions behind explicit safeguards.
- Follow local-first delivery: FOSS discovery, local integration, local
  development, local testing, then a local release candidate. Use GitHub only
  when publication, CI, source provenance, or repository collaboration makes it
  genuinely necessary.
