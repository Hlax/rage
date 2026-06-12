# Public Site Static Hosting and Pre-Deploy Checklist

This guide describes how to build, verify, and deploy the Research Graph Engine
public site. The site is a **read-only static export** from Next.js. It serves
committed JSON snapshots only and has **no server runtime**, API routes, or
connection to the private local engine.

Deploy artifact directory:

```txt
apps/public-site/out/
```

Generate it with `npm run build` inside `apps/public-site/`.

## What you are deploying

| Included | Excluded |
|---|---|
| HTML/CSS/JS static pages from `out/` | Private SQLite (`data/db/`) |
| Static JSON under `out/data/` (copied from build) | `data/exports/`, `data/reports/`, `data/tickets/` |
| Pre-rendered card and concept pages | Raw sources, prompts, secrets, `.env` files |

The public site never reads live database state at runtime. Production content
comes from **reviewed** snapshots in `apps/public-site/public/data/` that were
built into `out/` at compile time.

## Prerequisites

```bash
python -m pip install -e ".[dev]"
cd apps/public-site && npm install
```

Set mock mode for verification (no Ollama required):

```powershell
$env:RGE_LLM_MODE = "mock"
```

```bash
export RGE_LLM_MODE=mock
```

## Build

From the repository root:

```bash
cd apps/public-site
npm run build
```

Output lands in `apps/public-site/out/`. The directory is gitignored; deploy the
**contents** of `out/` (not the repo root).

### Local preview (dry run)

After building:

```bash
cd apps/public-site
npm run preview:static
```

This serves `out/` on `http://localhost:3000` using a one-shot `serve` invocation
(no extra dependency in `package.json`). Stop with Ctrl+C.

Alternative without npm script:

```bash
cd apps/public-site/out
python -m http.server 3000
```

## Pre-deploy checklist (required)

Complete **every** step before publishing `out/` to any external host.

### 1. Safety audit (hard gate)

```bash
python -m rge.modules.safety_auditor --audit full
```

Deployment must **not** proceed unless `status` is `pass`. If the audit reports
`blocked_reasons`, fix violations on a ticket branch and re-run.

### 2. Review public snapshot diff

If you changed export data or ran `export-public`:

```bash
git diff apps/public-site/public/data/
```

Confirm:

- No secrets, local paths, raw prompts, or private notes
- Only intentional public-safe fields per `docs/agents/10_SAFETY_MODEL.md`
- `build_info.json` and `public_cards.json` changes are expected and reviewed

Fixture-mode runs write to gitignored `data/` by default; only commit changes
under `apps/public-site/public/data/` after human review.

### 3. Rebuild and smoke-check locally

```bash
cd apps/public-site
npm run build
npm run preview:static
```

Manually verify:

- `/` — card list (or empty state)
- `/about` — methodology page
- `/cards/<id>` — at least one known card from `public_cards.json`
- `/concepts/<slug>` — at least one concept page
- Custom 404 for unknown paths

### 4. Golden tests (recommended)

```bash
RGE_LLM_MODE=mock python -m pytest tests/golden -q
```

Golden Test 12 and 25 cover public-site static render and debug details.

## Snapshot refresh workflow

When private research produces new public-safe cards:

```bash
RGE_LLM_MODE=mock python -m rge.cli export-public --limit 100
python -m rge.modules.safety_auditor --audit full
```

Mock-mode `export-public` writes scratch exports to gitignored `data/exports/`
and appends `data/exports/snapshot_manifest.json` plus a copy under
`data/exports/history/<bundle_id>/` for operator review. Use
`--no-snapshot-history` to skip history in tests or automation.

Review scratch history before any publish:

```bash
# Latest scratch trio
ls data/exports/
# Manifest entries (newest last)
cat data/exports/snapshot_manifest.json
# Compare a prior bundle
diff -ru data/exports/history/<older_bundle_id> data/exports/
```

To update committed public-site snapshots (after human review), use fixture-mode
or live-mode `--publish` per ticket-047/038 guards, then:

```bash
git diff apps/public-site/public/data/
```

### `export_schema_version` bump checklist

When changing public export field shapes or `build_info` keys:

1. Bump `EXPORT_SCHEMA_VERSION` in `rge/modules/card_exporter.py`.
2. Update golden tests (GT11/GT23) and any fixture snapshots as needed.
3. Run `python -m rge.modules.safety_auditor --audit full`.
4. Document the change in the ticket agent report.
5. Publish to `apps/public-site/public/data/` only after reviewed `--publish`
   or fixture-mode refresh — never from an unreviewed scratch export alone.

After review and commit of snapshot files:

```bash
cd apps/public-site && npm run build
```

Then run the pre-deploy checklist again before publishing `out/`.

**Do not** use `export-public --publish` unless live LLM mode is explicitly
enabled and you understand the live-mode guards in ticket-038.

## Deploying to a static host

Upload or sync the **contents** of `apps/public-site/out/` to any static host.
Examples (operator choice; not endorsed or automated by RGE):

| Host type | Typical approach |
|---|---|
| Object storage + CDN | Upload `out/` to bucket; enable static website hosting |
| Netlify / Vercel / Cloudflare Pages | Point build output to `apps/public-site/out` or CI artifact |
| GitHub Pages | Publish `out/` contents to `gh-pages` branch or Actions artifact |
| nginx / Apache | `root` directive to extracted `out/` directory |

Requirements for any host:

- Serve `index.html` for directory routes
- Support clean URLs for pre-rendered paths (`/about`, `/cards/...`, `/concepts/...`)
- **HTTPS** in production
- No server-side execution (static files only)
- No environment variables required at runtime (static export)

### CI alignment

The repository golden gate (`.github/workflows/golden-gate.yml`) runs
`npm run build` on Ubuntu in CI. Local builds should match CI Node 22+ and
`npm ci` from `apps/public-site/package-lock.json`.

## What not to deploy

- Repository root or `.next/` cache (use `out/` only)
- `apps/public-site/public/data/` without rebuilding (stale vs `out/`)
- Private `data/` tree
- `.env`, `.env.local`, or credentials
- Next.js `next start` production server (not used; static export only)

## Post-deploy verification

- Load the live URL over HTTPS
- Confirm `/about` renders safety boundaries copy
- Spot-check one card and one concept page
- Confirm no network calls to `localhost`, private APIs, or database ports
- Re-run safety audit locally if snapshots changed since last deploy

## Rollback

Redeploy the previous known-good `out/` artifact from backup or rebuild from the
last reviewed git commit of `apps/public-site/public/data/`.

## Related docs

- Safety model: `docs/agents/10_SAFETY_MODEL.md`
- Runtime config: `docs/agents/12_RUNTIME_CONFIG.md`
- Operator loop: `python -m rge.modules.operator_loop --mode plan`
- Root quickstart: `README.md` (Public Site section)
