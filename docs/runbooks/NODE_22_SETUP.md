# Node 22 setup (UI build gate)

Unified Intake UI uses **Vite 7**, which requires **Node 22.x**. Cursor and some WSL images ship Node 20 — builds fail with cryptic errors unless PATH is fixed.

## Canonical versions

| File | Value |
|------|--------|
| `/.nvmrc` | `22.22.0` |
| `/ui/.nvmrc` | `22.22.0` (must match root) |
| `ui/package.json` `engines.node` | `>=22.22.0` |

## One-time install

```bash
nvm install 22.22.0
nvm use 22.22.0
```

## Every session (repo root)

```bash
source scripts/with_node22_path.sh
bash scripts/check_ui_node_version.sh
cd ui && npm run build
```

Trial scripts (`trial_readiness_check.sh`, `trial_launch_check.sh`, `founder_pre_trial_checklist.sh`) source `with_node22_path.sh` automatically.

Set `SKIP_NVM_NODE22_FOR_UI=1` only when you intentionally use another Node 22 on PATH.

## Verify

```bash
node --version          # v22.22.0 (or same major as .nvmrc)
bash scripts/check_ui_node_version.sh
cd ui && npx --yes madge --circular --extensions ts,tsx src
```

## If it still fails

1. `which node` — must not point to `/usr/bin/node` (20.x) ahead of nvm.
2. Re-open terminal after `nvm use`.
3. Do not mix pnpm/yarn for this repo; use `npm` in `ui/`.
