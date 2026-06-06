# Important vs Less Important — Quick Reference

**Purpose:** Reduce thrash. Focus migration and demos on what actually moves the needle.

---

## Most important (understand first)

1. **`CLIENT_ID` + `configs/clients/<id>/`** — which broker you are running.  
2. **`config_loader.py` load order** — who wins when files disagree.  
3. **`guardrail_inbox_triage.sh`** — your release gate for triage.  
4. **`handoff_phrases.json` + `ui_copy.json`** — what customers and founders *see*.  
5. **Cross-client A/B scripts** — proof that packs don’t bleed.

---

## Important but don’t “casually” rewrite

- **`triage.py`** — large, interconnected; small edits can break many scenarios.  
- **`routes/inbox_triage.py`** — API contract; UI depends on it.  
- **`case_store.py`** — schema drift breaks workbench/history.  
- **`markers.json`** — tuning affects classification globally for all brokers.

---

## Safe customization areas (usual first moves)

- Client **`ui_copy.json`** (branding, buttons, handoff card).  
- Client **`handoff_phrases.json`** / **`stitched`**.  
- Client **`reply_overrides.json`** (targeted keys only).  
- Industry **`reply_templates.json`** / **`category_templates.json`** when all brokers should share tone updates.

---

## Advanced / later (not first migration priority)

- New workflow keys or lifecycle changes in **`triage.py`**.  
- New API fields — requires UI + tests + doc.  
- **`notice_retrieval`** / RAG augmentation behavior.  
- Docker/Cloud Run topology — only after pack + guardrail are stable.

---

## Looks big but not first priority for “second broker”

- Full **`UnifiedIntakePage.tsx` refactor** — only if UX blocks sale; otherwise JSON + small UI tweaks.  
- Add-car **stress batteries** — run when editing add-car flows, not for every copy tweak.

---

*Pair with [SAFE_VS_RISKY_CHANGES.md](./SAFE_VS_RISKY_CHANGES.md).*
