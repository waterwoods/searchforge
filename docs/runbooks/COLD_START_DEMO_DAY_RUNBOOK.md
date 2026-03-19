# Cold-Start Demo Day Runbook

**Purpose:** Avoid 5–15 s Turn 1 surprise when backend was idle.

---

## 1. When to Use

- **Demo day:** Run 2–3 min before broker meeting
- **Cloud Run:** First request after idle → cold start
- **Local:** Backend restarted or idle for a while

---

## 2. One-Command Warmup

```bash
bash scripts/warmup_for_demo.sh
```

**Local (default):** Warms http://127.0.0.1:8001

**Cloud Run:**
```bash
bash scripts/warmup_for_demo.sh --url https://fiqa-api-g7zatxrycq-uw.a.run.app
```
*(Warmup uses /readyz when /healthz returns 404 on Cloud Run.)*

---

## 3. What It Does

1. `/healthz` — basic health
2. `/readyz` — Qdrant/embedder readiness
3. `/api/inbox/triage` — realistic Turn 1 payload (warms triage path)

---

## 4. After Warmup

- Backend is warm for Turn 1
- Open demo URL within 2–3 min
- First broker scenario should feel fast

---

## 5. If Warmup Fails

- **Backend not running:** `bash scripts/run_demo_local.sh`
- **503 / embedding_warming:** `bash scripts/restore_8001_readiness.sh` (local Qdrant)
- **Cloud Run timeout:** Instance may still be cold; consider `min_instances=1` for demo day

---

## 6. min_instances=1 (Optional)

For zero cold-start on demo day:

- **Cost:** ~$15–50/month (approximate; depends on region, memory)
- **When:** Critical demo; willing to pay for guaranteed warm
- **How:** Set in Cloud Run service config

---

*See: `docs/ANDY_2MIN_BEFORE_DEMO.md`, `scripts/warmup_for_demo.sh`*
