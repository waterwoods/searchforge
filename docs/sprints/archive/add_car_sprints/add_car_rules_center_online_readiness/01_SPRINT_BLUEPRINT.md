# Add-Car Rules Center Online Readiness Sprint — Blueprint

**Sprint name:** Add-Car Rules Center Online Readiness Sprint  
**Target budget:** 45–90 minutes  
**Execution mode:** Long-running structured execution for Cursor Composer / multi-agent workflow

---

## 1. Why Online Readiness Is Needed Now

The previous sprint successfully built a minimal Add-Car Rules Center:
- business-friendly fields
- preview capability
- publish API
- restore action
- dedicated page

**Two critical gaps:**
1. **Frontend redeploy** — The Add-Car Rules page may not yet be live on Vercel; founder cannot inspect it online.
2. **Publish safety** — Cloud Run filesystem is read-only. Publish will fail (503) in production. The UI currently shows "发布" without warning that it may not work online.

The feature is promising but **not yet safe enough to demo as-is online**.

---

## 2. What Is Unsafe or Incomplete Today

| Gap | Risk | Impact |
|-----|------|--------|
| Publish in production | 503 on click | User confusion; "发布失败" with no explanation of why |
| UI over-promises | "发布后，Unified Intake 将使用新规则" | False expectation when publish fails |
| No environment awareness | Same UI locally vs online | Business user cannot tell if publish will work |
| Page visibility | May need frontend redeploy | Founder cannot find or inspect the page on Vercel |

---

## 3. Target Outcome

At the end of this sprint, the Rules Center should be **online-ready** in a way that feels:
- **clear** — Business user understands what the page does
- **safe** — No misleading publish promise when persistence is unavailable
- **non-confusing** — Draft vs publish vs preview states are explicit
- **valuable** — Chen Kui / assistants can edit, preview, and understand limitations

**Business users should be able to:**
- open the page on Vercel
- understand what it is
- edit safe business-facing rule text
- preview how Add-Car Quote would behave
- understand whether a change is draft-only or actually published
- not accidentally break production expectations

---

## 4. What This Sprint Will Do

- Make the Rules Center **visible** on the live frontend (ensure route + sider + redeploy)
- Make the page **understandable** for business users (clear copy, sample previews)
- Make publish behavior **honest** (draft-only mode when production persistence is unavailable)
- Add **publish capability detection** (backend reports whether config is writable)
- Improve **preview UX** (sample buttons, clearer labels)

---

## 5. What This Sprint Will NOT Do

- Build a full production rule engine
- Expand to other scenarios (remove-car, claim, etc.)
- Add version history or audit log
- Add writable volume for Cloud Run (out of scope)
- Add first reply / handoff editing (future sprint)

---

*See also: 02_ONLINE_READINESS_UX_SPEC.md, 03_PUBLISH_SAFETY_MODE_SPEC.md*
