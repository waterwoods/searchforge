# ADD-CAR PILOT SIMULATION + DEPLOY + FINAL TEST CASE PACKAGE — Final report

## Summary

- **Alignment:** Master outline + truth switch reviewed; Add-Car flagship and Stage 1 handoff boundary respected.
- **Simulation:** NA-Chinese battery run (rule path); focused IDs S01, S03, S05, S07, S08 inspected; full `guardrail_inbox_triage.sh` **PASS**.
- **Code changes:** None in this sprint (no new release-blocking defect identified).
- **Frontend deploy:** `vercel --prod --yes` from `ui/` **completed**; alias `https://ui-smoky-beta.vercel.app` updated to new production deployment (`ui-lnlmcbyir-andys-projects-1f411b73.vercel.app`). Build warning: `fatal: not a git repository` on Vercel builder (non-fatal); large chunk size warning from Vite.
- **Backend deploy:** **Not verified end-to-end in this session** after the frontend deploy step (subsequent local shell log capture failed; separate agent deploy attempt hit timeout). **Production** `https://fiqa-api-g7zatxrycq-uw.a.run.app` was **probed successfully** (readiness, client-config, CORS, sample triage POST) — confirms **currently live** backend health, not a new revision ID.
- **Known weak spots (inherited):** S07 re-shop and S08 thin “还缺什么” turns remain **need_more** / generic checklist behavior in rule-only single-turn; S05 can show overlapping slot tension (e.g. `make_model` collected yet still listed in `still_needed_fields` for other slots). Documented in prior dual-write / high-risk sprint reports.

## Founder decision (short)

1. **适合朋友/broker  bounded 试点吗？** Yes **with cautions** — handoff and happy path are strong; re-shop / context-free follow-ups need human expectation-setting.  
2. **前后端都发成功了吗？** **Frontend: yes (this session). Backend: not proven redeployed this session; live API smoke passed.**  
3. **最该测的 cases：** Happy path; 微信发过了; 太贵/换公司; 还缺什么; 配偶/第二驾驶人（见主对话 Report §7）。  
4. **最大 caution：** 无 CRM 记忆的单句跟进、reshop 抽取偏薄、试点级持久化/PII — 办公室仍需最终核实。

## Timing (approximate)

- Start: 2026-03-28 ~18:53 Pacific (repo `date` snapshot).  
- End: 2026-03-28 ~19:15 Pacific.  
- Elapsed: ~25–45 minutes (excludes aborted parallel deploy agent).
