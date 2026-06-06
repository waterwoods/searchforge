> **HISTORICAL / ARCHIVE — P9 Broker Surface Collapse (2026-05-30)**
> **Read instead:** [`docs/DEMO_STORY.md`](../../../DEMO_STORY.md), [`docs/BROKER_DEMO_FLOW.md`](../../../BROKER_DEMO_FLOW.md)

# Pre-Demo Preparation Flow

Repeatable flow to run before every broker demo.

**Note:** Offline pack now has 5 questions (not 3). See `docs/standards/BROKER_DEMO_QUALITY_STANDARD.md`.

## Flow (5–10 minutes)

```
1. Run pre-demo checklist
2. Read checklist output
3. Start demo
4. Confirm mode (Live or Offline)
```

## Step-by-Step

### 1. Run pre-demo checklist

```bash
bash scripts/demo_pre_checklist.sh
```

**Output:** `results/demo_pre_checklist/<timestamp>/CHECKLIST.md`

### 2. Read the checklist

Open the latest `CHECKLIST.md`. Check:

| Check | Meaning |
|-------|---------|
| Qdrant env ✅ | QDRANT_URL + QDRANT_API_KEY set (needed for Live) |
| Offline pack ✅ | demo_fallback.json has 3+ items (or DEFAULT used) |
| Backend ✅ | Backend running on 8001 |
| Live validate ✅ | 3 demo questions returned OK (Live path works) |

**Which path to use:** The checklist says "Use Live path" or "Use Offline path."

### 3. Start the demo

```bash
bash scripts/run_demo_local.sh
```

Wait for "Demo ready". Note the Mode line:
- **Live** — backend connected, use any question
- **Offline** — use only 5 recommended questions

### 4. Confirm mode in browser

Open http://localhost:5173/demo

- **Green "Live" badge** → Use any question
- **Orange "Offline" badge** + orange banner → Use only 3 questions

## What Gets Checked

| Check | Script / Location |
|-------|-------------------|
| Qdrant env | demo_pre_checklist.sh |
| Offline pack (3 items) | demo_fallback.json |
| Backend health | curl /healthz |
| Live path (3 queries) | demo_quick_validate.sh |
| Which path to use | CHECKLIST.md |

## If Offline Path

- Offline pack is always ready (DEFAULT_FALLBACK_ITEMS in code)
- No backend needed for the 5 questions
- Run `run_demo_local.sh` anyway — UI will start; backend may fail, that's OK

## If Live Path Fails Mid-Demo

See `docs/BROKER_DEMO_FALLBACK_SCRIPT.md`.
