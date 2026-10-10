# Render + Neon + Cloudflare R2 setup

The application integration is prepared. The external accounts and services have not been created or verified. Account creation, billing selection and credentials must be handled by the account owner. Never send secret values in chat or commit them to GitHub.

## 1. Neon: persistent PostgreSQL database

1. Sign up at https://console.neon.tech/ using your own account.
2. Create a project and database; choose the free plan if available. Choose a region close to your Render service.
3. In the connection dialog, select a **pooled PostgreSQL connection string**. Copy it directly into Render's `DATABASE_URL` variable. It contains a password; keep it private.
4. Keep TLS enabled. The application enforces certificate and hostname verification using the system CA bundle, even if the supplied URL says `sslmode=require`.

The app uses short-lived connections and disables server-side cursors for pooler compatibility. Do not revoke/delete the database when restarting Render.

## 2. Cloudflare R2: persistent private video storage

1. Sign up at https://dash.cloudflare.com/ and open **R2 Object Storage**. Check current prices, free allowances and any billing requirement before enabling it. This repository does not authorize paid upgrades or additional billing.
2. Create a Standard storage bucket, for example `video-tales-media`. Keep it **private**; a public development URL or custom domain is not required.
3. Create an R2 S3 API credential with **Object Read & Write** access scoped to this bucket. The application needs read, write and delete permissions for its startup check. Do not use a broad account management token.
4. From the R2 connection information, copy the S3 endpoint URL, bucket name, Access Key ID and Secret Access Key directly into Render's environment settings.

The application serves videos and thumbnails through one-hour signed HTTPS URLs. Refresh the video page if a URL has expired. Original upload data stays in R2 when Render restarts. Application-level publishing controls which media URLs are shown, but anyone given a valid signed URL can use it until it expires.

## 3. Render: run Django

Deploy link: https://render.com/deploy?repo=https://github.com/arpit1344/codex-daisitails

1. Sign in at https://dashboard.render.com/ and connect GitHub. Grant access to `arpit1344/codex-daisitails` if needed.
2. Use the `main` branch and the Blueprint in `render.yaml`. Keep the web service plan **Free**.
3. Set the following values in Render's secure environment settings:

| Variable | Where it comes from |
| --- | --- |
| `DATABASE_URL` | Neon pooled connection dialog; includes a secret |
| `R2_ENDPOINT_URL` | Cloudflare's HTTPS S3 endpoint, e.g. `https://<account-id>.r2.cloudflarestorage.com` |
| `R2_BUCKET_NAME` | Your private R2 bucket name |
| `R2_ACCESS_KEY_ID` | R2 bucket-scoped S3 credentials |
| `R2_SECRET_ACCESS_KEY` | R2 bucket-scoped S3 secret |
| `DJANGO_SUPERUSER_PASSWORD` | A new strong password you choose |

The Blueprint sets username `admin`, creates a Django secret and enables persistent mode. It disables local preview media serving. Leave `DJANGO_PERSISTENT_MODE=1`; missing cloud credentials will stop deployment rather than silently storing content on Render's temporary disk.

4. Deploy. Build collects static assets. Startup checks the database and performs a temporary R2 write/read/delete, runs database migrations, and creates the admin only if it is missing. It does not reset an existing password.
5. Open the URL Render supplies. Log in at `/admin/`, add categories, upload a small MP4 and thumbnail, publish it, and verify playback.
6. Restart the service once and verify that the same user, video record and uploaded media still work. Only this live check demonstrates persistence in your real accounts.

For demo content, temporarily set `SEED_DEMO=1` and deploy, then set it back to `0`. Demo seeding is idempotent for existing slugs. It writes six labelled test entries into Neon and R2; it does not migrate local user uploads.

## Existing local data

The current local database contains demo records and a development admin. It remains unchanged. Switching to Neon starts with the selected Neon database; switching storage does not automatically copy local files. Real local content needs a separate export/import and media-copy operation before changing services. Do not import the local development admin password into the public service.

## Limits and verification

Free allowances vary and are not unlimited. Render can sleep when idle. R2 may require a billing method and charges beyond its free allowance; Neon has database/compute limits. Review dashboards and monitor usage. This app does not include transcoding, a CDN custom domain, direct-to-R2 multipart uploads or automated backups. Large videos still upload through Django and are subject to hosting request limits; begin with small files.

Accounts and credentials are currently missing, so real Neon/R2 connectivity and the public deployment have not been tested. Local tests exercise TLS configuration, fail-fast missing settings, signed URLs, and a simulated S3 write/read/delete contract. These simulations do not prove live service access. Review provider backup/recovery options and keep separate backups before storing important content.
