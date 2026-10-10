# Neon CLI project setup

Project requested: `mute-silence-39082005`, branch `production`.

The local `neon.ts` contains the requested `preview.buckets.uploads` configuration with private access. Neon CLI 8.3.5 supports this legacy `preview` syntax; it can emit a deprecation notice because newer versions also accept top-level `buckets`. The supplied configuration was preserved exactly.

## Installed and validated

- Neon CLI is installed globally under `/workspace/.neon-tools` in this cloud machine and pinned locally as a development dependency.
- `@neon/config`, `@neon/env`, TypeScript and a reproducible npm lockfile are present.
- Neon agent skills were installed for Codex in this checkout.
- `.codex/config.toml` declares the OAuth MCP server scoped to this project. The agent will request Neon sign-in when that server becomes available; writing the config does not activate tools in an already-running chat.
- `npm run check:neon` type-checks the policy. Loading the policy confirms private bucket access.
- The Django application still passes its 22 tests.

## Blocked remote steps

The network proxy returned HTTP 403 for Neon. CLI browser login, project linking and deployment have not succeeded. The project/branch existence and supported storage region have not been verified.

The cloud environment configuration draft adds `console.neon.tech`, `oauth2.neon.tech`, `neon.com` and `mcp.neon.tech`, preserving existing package-manager presets. Review and save the network settings and publish the environment as required by the UI. A draft save alone does not apply runtime access.

When access is applied, from the checkout:

```sh
cd /workspace/codex-daisitails
npm ci
npm run neon -- login
npm run neon -- link --project-id mute-silence-39082005 --branch production -y
npm run neon -- projects get --project-id mute-silence-39082005
npm run check:neon
npm run neon -- config plan --project-id mute-silence-39082005 --branch production
npm run neon -- deploy --project-id mute-silence-39082005 --branch production --no-env-pull
npm run neon -- buckets list --project-id mute-silence-39082005 --branch production
```

Complete the browser login requested by the CLI. Verify the region supports Neon Object Storage before deployment. Confirm the plan's real changes before applying; do not automatically override protected production branch restrictions or upgrade billing. Do not paste credentials into chat. CLI authentication and `.neon` context are ignored by Git.

`--no-env-pull` prevents fetching connection/storage secrets as part of deploy. Retrieve credentials through Neon/hosting secure settings when needed. Never print a connection string or credential file.

## Website integration

This provisions a Neon backend bucket, not Django hosting. The existing app still uses Neon PostgreSQL plus Cloudflare R2 when persistent hosting is configured. The new Neon bucket is not yet connected to the app's storage backend; that change needs the verified endpoint/credentials and a separate upload/playback validation. Existing local/R2 content has not been copied or removed.
