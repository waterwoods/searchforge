# Founder Inspection Notes — Post-Handoff Add-Car

## Quick demo path

1. **客户入口** → 获取报价 / 加车 → complete until handoff toast.  
2. Confirm **green closure card**: status chip “已提交 · 办公室处理中”, 提交新问题 as ghost primary.  
3. Expand **还要继续补充本次加车** → send a correction (e.g. VIN) → expect success toast + new bubbles.  
4. Send a **账单** line in that lane → expect **warning** toast (new_issue) and draft mentioning **提交新问题**.  
5. **办公室工作台** → open the case → confirm **追加 · 疑似新事项** or **同一条服务记录** tag on list card.

## API note

Append uses existing `POST /api/inbox/cases/{id}/append-message` (no new endpoint).

## Deploy

Backend and frontend both changed → **redeploy API + static UI** for production parity with this branch.
