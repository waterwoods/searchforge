# P19H-3i — Customer-side smoothness manual checklist

**Date:** 2026-07-10  
**Scope:** Claim WeCom + H5 customer polish (text/plate/insurance/photo ack + status commands)  
**Deploy:** Combined with `d9b3a9d` (legacy fallback fix) + photo ack H5 link patch

---

## Preconditions

- Backend deployed with both commits (`d9b3a9d` + photo ack patch)
- WeCom test customer bound to broker workspace
- H5 frontend reachable (`H5_TASK_FRONTEND_BASE_URL` / production UI)
- No frontend deploy required for this patch

---

## Manual test steps

| # | Customer action | Expected |
|---|-----------------|----------|
| 1 | `我要理赔` | Start Card / H5 intake entry — **no** legacy bilingual fallback paragraph |
| 2 | `我需要理赔，发给我 H5` | H5 Start or Status Card with direct link — **no** legacy fallback |
| 3 | `进度` | Status card + H5 continue link (`继续补充事故资料` when submitted) |
| 4 | `补资料` | Same as status — H5 link present |
| 5 | `补充一下，对方车牌是 ABC123` | Ack: recorded to current claim + H5 link |
| 6 | `对方保险是 State Farm` | Ack: recorded + H5 link |
| 7 | **Send photo** (active claim) | Ack: `照片已收到` + `继续补充事故资料` + **direct H5 URL** — **not** “请回复 进度/链接” as primary path |
| 8 | Open H5 dashboard from link | Dashboard loads; submitted state shows supplement allowed |
| 9 | Broker Workbench | Case visible; photo on timeline; supplements in known facts / timeline |

---

## Pass criteria

- All Claim/H5 commands return Start / Status / H5 link (no dead-end text-only ack)
- Photo ack on active claim includes inline H5 link
- No legacy English paragraph (`Chen Kui's team has received your request`)
- No Add Car Phase 2 prompt unless customer explicitly says `我要加车`
- No implication of `broker_done` or official carrier filing in customer copy

---

## Known remaining gaps (out of scope)

- Workbench provenance UI polish
- Demo/test case cleanup
- Access protection / auth
- Add Car dashboard (later)
