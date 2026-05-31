# Constitution V1 Recovery Point

**Status:** ✅ **Active** — Constitution V1 committed and tagged  
**Pre-baseline HEAD:** `d64f7829158ebf738ca2150e1f039c264ddb278b`  
**Branch:** `reduction/p1-simplification-loops`  
**Date activated:** 2026-05-31

---

## What This Recovery Point Is

The last **document-only** commit before Sprint A (P16-B) touches product code. It freezes:

- North Star V1
- Capability Map V1 + Scorecard
- 7 Capability Contracts
- Roadmap, Backlog, Scoreboard, Sprint A definition
- P16-A baseline audit trail

**Tag name:** `constitution-v1`

---

## Phase 2 — Exact Commands (Founder executes)

```bash
cd /home/andy/searchforge

# 1. Confirm branch
git branch --show-current
# Expected: reduction/p1-simplification-loops

# 2. Stage ONLY constitution docs (includes P16-A reports)
git add docs/product_constitution/

# 3. Verify staged set — MUST NOT include archive migrations or UI code
git diff --cached --name-only
# Expected: paths under docs/product_constitution/ only

# 4. Commit
git commit -m "$(cat <<'EOF'
Constitution V1 ratified

North Star locked
Capability map locked
Contracts locked
Backlog locked
Sprint framework established
Ready for implementation
EOF
)"

# 5. Record commit hash
CONSTITUTION_COMMIT=$(git rev-parse HEAD)
echo "Constitution V1 commit: $CONSTITUTION_COMMIT"

# 6. Tag (annotated recommended)
git tag -a constitution-v1 -m "Constitution V1 — pre-Sprint A implementation baseline (2026-05-31)"

# 7. Verify tag
git show constitution-v1 --no-patch
git tag -l 'constitution*'
```

**After execution:** Update this file's `Commit hash` field below with `$CONSTITUTION_COMMIT`.

---

## Recovery Point Record (fill after commit)

| Field | Value |
|-------|-------|
| **Commit hash** | `66f7ed593bd307dfa4f437f582cbf4a4c88e0e2f` |
| **Tag** | `constitution-v1` |
| **Branch** | `reduction/p1-simplification-loops` |
| **Parent (pre-constitution)** | `d64f7829158ebf738ca2150e1f039c264ddb278b` |
| **Date** | 2026-05-31 |

---

## Rollback Commands

### Return to Constitution V1 baseline (after Sprint A work)

```bash
git checkout constitution-v1
# Detached HEAD — inspect only, or:
git checkout -b sprint-a-rollback constitution-v1
```

### Hard reset branch to Constitution V1 (destructive — loses uncommitted Sprint A work)

```bash
git checkout reduction/p1-simplification-loops
git reset --hard constitution-v1
```

### Revert specific Sprint A commits (preferred if pushed)

```bash
git log constitution-v1..HEAD --oneline
git revert <commit-hash>   # one or more
```

### Env-only rollback (no git — UI changes in Sprint A)

```bash
# Unset product-only flag → full operator UI returns
unset VITE_UNIFIED_INTAKE_PRODUCT_ONLY
# Rebuild UI
```

---

## What NOT to Include in This Commit

| Exclude | Reason |
|---------|--------|
| 1,225 staged archive renames | P1 simplification — separate commit |
| 95 unstaged reduction edits | Ongoing work |
| `docs/BROKER_ONE_PAGER.md`, trial docs | Sprint B commercial pack |
| UI files (`UnifiedIntakePage.tsx`, etc.) | Sprint A (P16-B) |
| `docker-compose.product.yml` | Deploy — separate track |

---

## Verification After Tag

```bash
# Constitution tree present at tag
git ls-tree -r constitution-v1 --name-only | grep product_constitution | wc -l
# Expected: 33+ (26 original + P16-A docs)

# No UI changes in constitution commit
git diff d64f782..constitution-v1 --name-only | grep -E '^ui/' && echo FAIL || echo OK
```

---

*End of Constitution V1 Recovery Point*
