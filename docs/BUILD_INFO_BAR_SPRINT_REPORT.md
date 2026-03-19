# Build Info Bar + LA Time Release Identity Sprint Report

## 1. Placement decision

**Where:** Right side of the main header bar, next to KpiBar.

**Why:**
- Visible on every page (Showtime, Workbench, Unified Intake, Vitals, etc.)
- No extra vertical space — stays within the existing header
- Desktop-first: header is always visible; release info is in the corner
- Low clutter: small font (11px), muted color (rgba white 0.6–0.7)
- Founder can glance at the top-right to confirm version/build/env

## 2. Build info model

| Field | Source | Notes |
|-------|--------|------|
| **Version** | `package.json` version | Read at build time; bumped to `0.1.0` |
| **Build time** | `new Date().toISOString()` at build | Injected via Vite `define`; formatted to LA at runtime |
| **Build ID** | `VERCEL_GIT_COMMIT_SHA` (Vercel) or `git rev-parse --short HEAD` (local) | 7-char commit hash; falls back to `dev` if unavailable |
| **Environment** | `VITE_APP_ENV` (Vercel) or `import.meta.env.DEV` | `production` / `preview` / `local` |

**Vite config:** `ui/vite.config.ts` injects `__APP_VERSION__`, `__BUILD_TIME_ISO__`, `__BUILD_ID__` at build time.

## 3. Implementation changes

| File | Change |
|------|--------|
| `ui/package.json` | Version `0.0.0` → `0.1.0`; added `@types/node` devDep |
| `ui/vite.config.ts` | Added `getBuildId()`, `getAppVersion()`, `define` block |
| `ui/src/vite-env.d.ts` | Declared `__APP_VERSION__`, `__BUILD_TIME_ISO__`, `__BUILD_ID__`, `VITE_APP_ENV` |
| `ui/src/components/layout/ReleaseIdentityBar.tsx` | **New** — compact bar with LA time formatting |
| `ui/src/components/layout/AppLayout.tsx` | Import `ReleaseIdentityBar`; add to Header with `justifyContent: space-between` |

## 4. Practical usefulness check

- **Clear enough?** Yes — version, built time (LA), build id, env in one line
- **Too noisy?** No — 11px font, muted color, single row
- **Refinements:** Kept labels short (`Built:`, `v`, env as uppercase); no extra badges

## 5. Validation summary

- `cd ui && npm run build` — **success**
- Values injected: version `0.1.0`, build time ISO, short commit hash
- LA time formatting: `toLocaleDateString` + `toLocaleTimeString` with `America/Los_Angeles`
- Graceful fallbacks: `—` when values missing; `dev` when git unavailable

## 6. Redeploy readiness

- **Frontend-only** — no backend changes
- **Vercel env (optional):** Add `VITE_APP_ENV` for production/preview:
  - Production: `VITE_APP_ENV=production`
  - Preview: `VITE_APP_ENV=preview`
  - If unset: defaults to `production` (prod build) or `local` (dev)
- **Vercel build:** Uses `VERCEL_GIT_COMMIT_SHA` automatically — no extra config
- **After redeploy:** Check header top-right for `v0.1.0`, `Built: YYYY-MM-DD H:MM PM PT`, short hash, env

## 7. 中文总结

- **一眼看出最新版本：** 会。版本号、构建时间、commit 短 hash 都在 header 右上角。
- **LA 时间：** 有。格式为 `Built: 2026-03-12 X:XX PM PT`。
- **版本 / build / env 信息：** 够用。v0.1.0、构建时间、7 位 commit、环境（production/preview/local）。
- **占地方：** 不占。单行小字，在 header 右侧。
- **下一步：** 需要重新发布前端（`vercel --prod` 或推送触发部署）。

## 8. COPY/PASTE RELEASE IDENTITY BLOCK

**What is shown:** `v0.1.0` | `Built: 2026-03-12 X:XX PM PT` | `a1b2c3d` (short commit) | `PRODUCTION` / `PREVIEW` / `LOCAL`

**Where it appears:** Top-right of the main header bar, on all AppLayout pages (Showtime, Workbench, Unified Intake, Vitals, etc.)

**Why it is useful:** Founder can instantly see version, build time in LA, commit, and environment — no guessing whether this is latest or which deploy is live.

**Redeploy needed:** Yes — frontend-only. Run `vercel --prod` (or push to trigger Vercel). Optionally set `VITE_APP_ENV=production` in Vercel for explicit env label.
