# P20 Experience-Version / Release Checklist (Mini Program)

**Date:** 2026-07-13  
**Scope:** Pre-commit and pre-upload gate for Mini Program component integrity and DevTools compile safety.  
**Stabilization freeze (2026-07-13):** Gate1 + Gate2 verified via `npm run test:component-gates`. Gate3 remains **unsigned** — do not upload experience version until Founder DevTools compile is recorded.

---

## Hard stop rules

- Never mark PASS from unit tests alone.
- Never upload experience version before real DevTools compile gate.
- Never commit private/local config:
  - `miniapp/config.local.ts`
  - `miniapp/project.private.config.json`
  - local token values / AppID overrides

---

## Gate 1 — Component file completeness

Every Mini Program component directory must include:

- `index.ts`
- `index.json`
- `index.wxml`
- `index.wxss`
- `index.json` contains `"component": true`

Automated check:

- `cd /home/andy/searchforge/miniapp`
- `npm run test:component-gates`

PASS criteria:

- No Gate1 failures in validator output.

---

## Gate 2 — `usingComponents` path validation

Validate all `usingComponents` entries:

- path exists
- filename/path casing matches exactly
- referenced component target files exist (`.json/.ts/.wxml/.wxss`)
- untracked component files are explicitly reviewed (strict mode for release)

Automated check:

- Standard: `npm run test:component-gates`
- Strict release mode: `node ../scripts/validate_miniapp_component_gates.mjs --strict-git`

PASS criteria:

- Standard check passes.
- Strict mode has zero untracked component files before upload/merge.

---

## Gate 3 — Real WeChat DevTools compile

Manual required (cannot be replaced by CLI tests):

1. Clear DevTools cache / rebuild project.
2. Full compile in WeChat DevTools.
3. Confirm **no**:
   - `component not found`
   - `module ... is not defined`
4. Open key pages (Entry/Task Home/Review/Receipt) once after compile.

PASS criteria:

- Human verifier checks PASS in DevTools checklist.
- Any compile/runtime module issue blocks release.

---

## Required evidence update

Before Pilot upload, attach:

- validator command output (`npm run test:component-gates`, strict mode when applicable),
- DevTools compile screenshot/log,
- updated rows in:
  - `docs/qa/p20_devtools_walkthrough_checklist.md`
  - `docs/qa/p20_pilot_blockers.md`
