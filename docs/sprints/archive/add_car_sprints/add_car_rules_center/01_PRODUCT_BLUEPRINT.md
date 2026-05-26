# Minimal Business Rules Center for Add-Car Quote — Product Blueprint

**Sprint:** Minimal Business Rules Center for Add-Car Quote  
**Purpose:** Define why a minimal Rules Center matters now and what the smallest useful version is.

---

## 1. Why a Minimal Rules Center Matters Now

The founder Chen Kui wants:
- **More business flexibility** — adjust wording and flow without touching code
- **More participation** — assistants and Chen Kui can safely tune customer-facing behavior
- **Less dependency on engineering** — every wording/flow change should not require a deploy
- **Safe experimentation** — try changes without breaking production

The product insight: **A good rules center helps business users improve the Add-Car Quote flow, not burden them with technical complexity.**

---

## 2. Why Add-Car Quote Is the Correct First Scenario

- **High value:** Add-car is a common, high-volume customer flow
- **Mature flow:** Already 80% completion (handoff logic, collection order, extraction)
- **Config-driven surface exists:** `reply_templates.json` and `handoff_phrases.json` already support add_car
- **Clear boundaries:** One well-defined flow; no multi-scenario sprawl yet

---

## 3. Why Flexibility Should Come After a Strong Default Flow

The Add-Car Quote flow already has a strong default:
- Vehicle → Zip → Delivery/Driver → Handoff
- Handoff threshold: vehicle + zip + (delivery or driver)
- First reply and next-step prompts are defined

The Rules Center should **expose** and **adjust** these, not replace them. Flexibility comes from editing existing rules, not from building a new flow from scratch.

---

## 4. What the Smallest Useful Version Is

**In scope:**
1. **View** — current Add-Car flow structure (steps, collection order, handoff condition)
2. **Edit** — selected business-facing rules:
   - 这类客户第一句怎么回 (first reply)
   - 下一步要问什么 (next-step prompts: vehicle, zip, delivery/driver)
   - 什么时候转给办公室 (handoff message)
3. **Preview** — type sample customer message, see system reply
4. **Draft vs Publish** — save draft, preview draft, publish only when ready
5. **Revert** — restore last published version

**Out of scope:**
- Full visual workflow builder
- Full enterprise rule engine
- Free editing of low-level system behavior (extraction, storage, security)
- Multi-scenario editing

---

## 5. Success Criteria

- Chen Kui or an assistant can: view rules → edit → preview → publish → see result in live flow
- No engineering required for wording/flow changes
- Safe: draft/preview before publish; revert available

---

*See also: 02_RULES_CENTER_UX_SPEC.md, 03_ADD_CAR_RULES_DATA_MODEL.md*
