# Founder Inspection Notes

## What to click / run

1. Local API on **8001** (per `docs/ANDY_QUICK_START.md`): send a **3-turn** add-car thread:
   - T1: `我想加车 2021 Honda`
   - T2: `不是这个，是 2024 Tesla`
2. Read `client_reply_draft` / UI draft: should **name the Tesla**, then ask for **zip** (if missing).

## Red flags (should not see)

- Year-only praise (“好的，2024的”) when make is clearly stated.
- Handoff or reply still talking about **X5** after customer said **X3** in the same thread.

## Green flags

- Office-real tone: **confirm vehicle → one next ask**.
- Broker summary / next step still actionable.

## Trust lens

If a broker reads the thread aloud to a customer, the customer should nod at **“they got the right car.”**
