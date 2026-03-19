# A/B End-to-End Variation Demo Spec

**Purpose:** Define how to prove Client A vs Client B variation beyond entry.

---

## 1. Lifecycle Scenarios That Should Differ

| # | Scenario | Client A (chen_kui) | Client B (demo_broker) |
|---|----------|---------------------|------------------------|
| 1 | Initial triage handoff | "办公室" / "陈奎办公室" | "客服团队" |
| 2 | Case created | case.client_id = "chen_kui" | case.client_id = "demo_broker" |
| 3 | Append follow-up | Draft uses same client phrases | Draft uses same client phrases |
| 4 | Reopen case, append | Uses case.client_id → chen_kui phrases | Uses case.client_id → demo_broker phrases |

---

## 2. Exact Lifecycle Steps to Prove

1. **Create case as Client A:** Open `?client=chen_kui`, triage "我想加新车报价", persist. → `client_reply_draft` contains "办公室".
2. **Verify case has client_id:** GET `/api/inbox/cases` → case has `client_id: "chen_kui"`.
3. **Append as Client B URL:** Open `?client=demo_broker`, open case from step 1, append "我发了ZIP 90210". → Draft should still use **chen_kui** (from case), not demo_broker.
4. **Create case as Client B:** Open `?client=demo_broker`, triage "我想联系客服", persist. → `client_reply_draft` contains "客服团队".
5. **Append to Client B case:** Append "我发了ZIP 90210" to case from step 4. → Draft should use **demo_broker** phrases.

---

## 3. What Founder Should Show

- Same base product, different client lifecycle behavior
- Case "remembers" which client it belongs to
- Append does not change client based on current URL

---

## 4. How to Explain "Same Base, Different Client Lifecycle Behavior"

- "We persist client_id on each case. When you append a follow-up, we use the case's client, not the current page URL. So Client A stays Client A through the whole flow."
