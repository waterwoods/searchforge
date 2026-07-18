# User Journey Contract Template (P26G)

**Status:** Permanent checklist for every future customer task type  
**Governing SSOT:** `docs/product/p20_product_north_star.md` §J2  
**Rule:** No future task type is production-ready without this contract filled.

Copy for each new task type:

```text
TASK TYPE: <semantic_id e.g. accident_story>

1. Who initiates this task?
   - [ ] system_default (intake policy)
   - [ ] conditional (policy rule)
   - [ ] broker_requested (Request More / Send Request)

2. When does it become visible?
   - First claim create / resume:
   - After which facts/evidence:

3. Who may complete it?
   - Customer / Broker / either:

4. What canonical fact or evidence completes it?
   - Field / slot / attachment identity:

5. Does completion require broker confirmation?
   - Yes / No — if yes, customer state while waiting:

6. Can the customer return later?
   - Resume token / session behavior:

7. What happens after refresh / re-entry?
   - Same task state? Same Today Focus?

8. What Timeline event is written?

9. What does Constitution output?
   - task_id, task_source, state, actionable, route:

10. What does Broker see?
    - Workbench band / next action / evidence row:

11. What security boundary protects it?
    - Token claims, case binding, no cross-customer access:

GATE CHECK (all required):
- [ ] First-Time Customer Gate
- [ ] Return-Later Gate
- [ ] Exceptional Follow-Up Gate
```

## Current auto-claim defaults (reference)

| task_id | task_source | Completes via |
|---------|-------------|----------------|
| `accident_story` | system_default | `known_facts.accident_description` |
| `accident_photos` | system_default | claim photo evidence slots |
| `insurance_card` | system_default (or broker_requested when open) | `policy_or_insurance_card` evidence / Slice1 satisfy |
