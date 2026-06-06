# Founder Inspection Notes — Client Identity Persistence Sprint

---

## What Founder Should Inspect After This Sprint

1. **Case creation:** Create case with `?client=chen_kui`. Check GET /api/inbox/cases → case has `client_id: "chen_kui"`.
2. **Append flow:** Open same case with `?client=demo_broker`. Append "我发了ZIP 90210". Draft should still say "办公室" (chen_kui), not "客服团队" (demo_broker).
3. **Client B case:** Create case with `?client=demo_broker`. Append to it. Draft should say "客服团队".

---

## What Should Now Feel More Reusable

- Cases are client-aware end-to-end
- Append does not depend on current URL
- Same base product, different client lifecycle behavior

---

## How Founder Should Explain Lifecycle-Deep Client Variation

- "Each case stores which client it belongs to. When you append a follow-up, we use the case's client for handoff wording. So Client A stays Client A through the whole flow, even if you switch clients in the URL."
