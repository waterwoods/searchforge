# P19H-3j — Channel UX Policy Manual Checklist

**Date:** 2026-07-10  
**Scope:** H5 vs WeCom role clarification (supplement acks, status commands)  
**Deploy:** Not yet — patch + tests only

---

## Preconditions

- Backend includes P19H-3j channel UX policy commit
- WeCom test customer bound to broker workspace
- H5 frontend reachable
- Active submitted Claim case for supplement tests

---

## Manual scenarios

| # | Customer action | Expected |
|---|-----------------|----------|
| A | `进度` | Status card + H5 link (`继续补充事故资料` or equivalent) |
| B | `对方保险是 State Farm` (submitted Claim) | Ack: 已记录；**no** long raw H5 URL flooding chat |
| C | `补充一下，对方车牌是 ABC123` (submitted Claim) | Same as B — recorded, short ack |
| D | Send photo (submitted Claim, otherwise complete) | 照片已收到；H5 CTA only if open Claim still missing key items |
| E | `补资料` | Status card + H5 link |
| F | Open H5 from status link | Dashboard shows structured state; Review + Submit in H5 |
| G | Broker Workbench | Text/photo supplements visible on timeline; provenance preserved |

---

## Pass criteria

- Status / link commands always return H5 entry
- Ordinary supplements on **submitted** Claims do not dump raw URL every time
- Open Claims with missing structured fields may show compact H5 CTA
- No legacy bilingual fallback on Claim/H5 commands
- No Add Car Phase 2 misroute on Claim supplements
- No implication of `broker_done` or carrier filing in supplement acks

---

## Out of scope (this round)

- Workbench provenance UI polish
- Demo case cleanup
- Access protection / auth
- Add Car dashboard
- Deploy
