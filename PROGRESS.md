# Project handoff

## Current application
- General-purpose Django video library with categories, drafts, featured videos, upload admin, editorial ratings, view counts and responsive white/blue UI with dark mode.
- Local SQLite and media files are preserved. Local admin credentials are in ignored `.admin-credentials.txt`.
- Six local demo videos and real MP4 playback were verified in Chromium.

## Persistent hosting integration
- Render Free Blueprint now requires Neon PostgreSQL and Cloudflare R2 settings.
- PostgreSQL enforces certificate/hostname verification and pooler-compatible short-lived connections.
- Private R2 storage uses one-hour signed URLs, bucket-scoped credentials and no overwriting of existing filenames.
- 22 Django tests pass, including simulated S3 upload/read/delete, signed URLs, TLS settings and missing-credential failures. Dependency checks also pass.
- Startup checks database access and temporary storage write/read/delete before migrations/admin bootstrap. Existing admin accounts are preserved.
- Optional demo seeding uses bundled original assets; it does not migrate existing local content.
- Setup guide: docs/HOSTING.md. No secrets are committed.

## External prerequisites and remaining work
- User chose Neon PostgreSQL after discussing MongoDB. Render, Neon and Cloudflare accounts still need to be created.
- No cloud credentials are available in this machine or configuration; actual cloud connectivity is not verified.
- User must create accounts and configure values securely in Render, then deploy and check real upload/playback and persistence after restart.
- No public URL has been issued or verified. Provider free allowances and billing requirements must be checked by the account owner.
- Source updates are saved on GitHub main; inspect Git history for the resulting revision.

## Neon CLI setup request
- User supplied project `mute-silence-39082005`, branch `production`, and an exact private uploads bucket policy.
- CLI, config/env packages, TypeScript, agent skills and project-scoped OAuth MCP config installed locally.
- Policy type-check and load pass; 22 Django tests still pass.
- Login/link/deploy attempts are blocked by the network proxy (HTTP 403); remote project, region and bucket state remain unverified.
- Required Neon domains are saved in the cloud network draft. Runtime access and Neon login must be completed before deployment can resume.
- See docs/NEON.md. Django uploads still use the existing R2 configuration; Neon object storage has not been connected.

## Current access update
- Neon API now responds over the configured network; the previous network block is resolved for Neon.
- CLI browser login starts but its loopback callback cannot be completed from the user's external browser through available tools.
- No CLI credential or injected NEON_API_KEY exists yet. A destination-scoped NEON_API_KEY requirement is saved for secure entry in Codex environment settings.
- Link/deploy and private bucket verification remain pending that credential. Render API access remains blocked; no public website URL exists yet.

## Verified Neon completion
- Authenticated project access now works. Project/region: video-tales, aws-us-east-2.
- Checkout linked to production; deployment plan has no conflicts; deploy succeeded.
- Subsequent remote inspection confirms uploads bucket is private.
- No connection strings or storage secrets were retrieved. Public website hosting and app-to-Neon-storage integration remain pending.
- Render API remains network-blocked and no Render API key is present; a secure RENDER_API_KEY requirement is saved for api.render.com.
- Existing Neon secret was misnamed with a key-like string: user should rotate it and correct the secret name to NEON_API_KEY without sharing values in chat.

## Render deployment continuation
- `RENDER_API_KEY` is injected and authenticated; the account currently has no services.
- Django now accepts Neon Object Storage's standard `AWS_*` variables, replacing the separate R2 requirement.
- Live Neon runtime variables were retrieved to an ignored temporary file without printing values. Actual database/storage connectivity from this machine remains blocked until the newly saved dynamic Neon hostnames are applied to the environment network policy.
- The Render Blueprint no longer prompts the user for secret values. It can create the service first; the authorized deployment flow will then set secrets through Render's API.
