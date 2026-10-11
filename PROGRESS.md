# Project handoff

## Current application
- General-purpose Django video library with categories, drafts, featured videos, upload admin, editorial ratings, view counts and responsive white/blue UI with dark mode.
- Catalog discovery includes search, category/language/duration filters, latest/popular/top-rated sorting and filter-preserving pagination.
- New thumbnails are resized within 1280×720 and stored as compressed WebP; cards use lazy decoding, stable 16:9 artwork and clear duration badges.
- SEO includes admin-editable titles/descriptions, canonical URLs, social preview tags, VideoObject structured data, a public-content-only sitemap and robots rules that keep admin pages out of search results.
- Local SQLite and media files are preserved. Local admin credentials are in ignored `.admin-credentials.txt`.
- Six local demo videos and real MP4 playback were verified in Chromium.
- Live site: https://video-tales.onrender.com/videos/
- Live admin: https://video-tales.onrender.com/admin/

## Persistent hosting integration
- Render Free hosts Django; Neon provides PostgreSQL and private object storage.
- PostgreSQL enforces certificate/hostname verification and pooler-compatible short-lived connections.
- Private R2 storage uses one-hour signed URLs, bucket-scoped credentials and no overwriting of existing filenames.
- 22 Django tests pass, including simulated S3 upload/read/delete, signed URLs, TLS settings and missing-credential failures. Dependency checks also pass.
- Startup checks database access and temporary storage write/read/delete before migrations/admin bootstrap. Existing admin accounts are preserved.
- Optional demo seeding uses bundled original assets; it does not migrate existing local content.
- Setup guide: docs/HOSTING.md. No secrets are committed.

## Live deployment verification
- Render service `video-tales` is deployed from GitHub `main` on the free plan.
- Render's `/health/` deployment check passed on the initial deploy and again after a clean restart with demo seeding disabled.
- The restart reused the existing Neon PostgreSQL database and private `uploads` bucket.
- Required Render secrets are configured in the service and are not committed to Git.
- Live admin credentials are stored only in ignored `.render-admin-credentials.txt`.
- Render free services may sleep when idle; the first request after inactivity can take longer.

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

## Render deployment completion
- Django uses Neon Object Storage's standard `AWS_*` variables.
- The Blueprint service was created, all runtime secrets were set through Render's API, migrations and admin bootstrap completed, and demo content was seeded once.
- `SEED_DEMO` is now disabled in Render and in `render.yaml`; a second deployment reached `live`, confirming repeatable startup against persistent services.
