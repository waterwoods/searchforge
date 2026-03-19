# Insurance Autonomous Progress Report 2

## 1. Local Qdrant path

### What was checked

- Docker Compose `qdrant` service
- `build_demo_core_collection.py` for seeding `auto_insurance_demo_core`
- Backend `clients.py` Qdrant connection logic
- `run_demo_ingest_oneclick.sh` (Cloud-only; requires QDRANT_URL)
- `results/auto_insurance_discovery/passing.json` for URL list

### What works

- **Docker Qdrant:** `docker compose up -d qdrant` — runs on localhost:6333
- **Local seed:** `bash scripts/seed_local_qdrant.sh` — seeds 30 docs from passing.json into local Qdrant (no Cloud secrets)
- **Backend local mode:** `USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh` — backend uses localhost:6333
- **demo_quick_validate:** All 3 questions PASS with local Qdrant

### What is blocked

- **Cloud path:** Qdrant Cloud still returns 404 (cluster paused). External; requires Andy to wake cluster at cloud.qdrant.io.

### Exact runnable sequence (local live mode)

```bash
# 1. Start Qdrant
docker compose up -d qdrant

# 2. Seed collection (once; ~1 min)
bash scripts/seed_local_qdrant.sh

# 3. Run demo
USE_LOCAL_QDRANT=1 bash scripts/run_demo_local.sh

# 4. Open
# http://localhost:5173/demo
```

---

## 2. Demo polish completed

### Files changed

| File | Change |
|------|--------|
| `ui/src/pages/DemoPage.tsx` | Value prop, 5 recommended questions, fallback for Q4/Q5, brokerUse wording, buildHighlights for savings/claims |
| `ui/src/pages/DemoPage.css` | `.demo-value-prop` style |
| `docs/BROKER_DEMO_FALLBACK_SCRIPT.md` | 5 questions, removed "Q4/Q5 no pre-saved" |
| `docs/BROKER_DEMO_SCRIPT_15MIN.md` | Opening script, fallback transition, Q4/Q5 now offline-safe |

### Why it improves broker demo quality

- **Value prop:** "帮经纪快速回答客户问题，附官方 / 权威来源链接，可直接发微信" — clearer broker benefit
- **5 questions:** Savings and claims now work offline; full 15-min script runs without live backend
- **brokerUse labels:** Shorter, scenario-specific (e.g. "新车投保：快速给客户权威答复 + 官方链接")
- **Fallback merge:** JSON + DEFAULT_FALLBACK_ITEMS so Q4/Q5 always have preset answers when offline

---

## 3. Operator simplification

### New or updated scripts/docs

| Item | Purpose |
|------|---------|
| `scripts/seed_local_qdrant.sh` | Seed local Qdrant without Cloud secrets |
| `docs/ANDY_QUICK_START.md` | One-file quick start |
| `docs/ANDY_2MIN_BEFORE_DEMO.md` | 2-minute pre-demo checklist |
| `docs/ANDY_IF_SOMETHING_GOES_WRONG.md` | Troubleshooting cheat sheet |
| `docs/BROKER_MEETING_PACKAGE.md` | Consolidated meeting flow |
| `scripts/demo_prep_one_command.sh` | USE_LOCAL_QDRANT path, quick ref link |

### What Andy can now ignore

- Cloud Qdrant setup when using local path
- Manual discovery/ingest when `passing.json` exists
- Scattered docs — `ANDY_QUICK_START.md` points to everything

---

## 4. Meeting package

| Section | Location |
|---------|----------|
| **Opening** | `docs/BROKER_MEETING_PACKAGE.md`, `BROKER_DEMO_SCRIPT_15MIN.md` |
| **Demo flow** | 5 questions, 15 min, table in BROKER_MEETING_PACKAGE |
| **Fallback transition** | "Let me switch to our offline demo mode..." in BROKER_DEMO_SCRIPT_15MIN |
| **Closing questions** | "What would make this most useful for your day-to-day work?" |
| **Follow-up** | `docs/BROKER_FOLLOWUP_MESSAGE.md` |

---

## 5. Smallest remaining blockers

1. **Cloud path:** Qdrant Cloud 404 — wake cluster at cloud.qdrant.io (external).
2. **Embedding mismatch (low risk):** Seed uses fastembed `bge-small-en-v1.5`; backend may use `all-MiniLM-L6-v2` depending on env. Both 384 dim; if backend uses SBERT, results may differ slightly. Current test passed.

---

## 6. Next 12 actions

1. **Run demo prep before broker meeting:** `bash scripts/demo_prep_one_command.sh`
2. **Use local Qdrant if Cloud down:** `seed_local_qdrant.sh` + `USE_LOCAL_QDRANT=1 run_demo_local.sh`
3. **Read ANDY_QUICK_START.md** when returning
4. **Use ANDY_2MIN_BEFORE_DEMO.md** right before demo
5. **Use ANDY_IF_SOMETHING_GOES_WRONG.md** if issues
6. **Wake Qdrant Cloud** at cloud.qdrant.io to restore Cloud live path
7. **Run `snapshot_demo_answers.py`** after ingest to refresh `demo_fallback.json` (optional; DEFAULT covers 5)
8. **Update BROKER_FOLLOWUP_MESSAGE** if needed for specific broker
9. **Schedule broker demo** with 陈魁
10. **Test offline path** once: refresh, click 5 questions, confirm
11. **Test local live path** once: seed + USE_LOCAL_QDRANT=1 run
12. **Keep discovery data** — ensure `passing.json` exists for future seeds
