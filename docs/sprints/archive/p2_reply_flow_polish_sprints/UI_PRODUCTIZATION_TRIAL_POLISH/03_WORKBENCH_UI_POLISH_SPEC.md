# Workbench UI Polish Spec

**Purpose:** Define how the Broker Workbench should feel for trial and daily use.

---

## 1. Above the Fold

- **Title:** "Broker Workbench" or "办公室工作台" — clear, not technical.
- **Subtitle:** One-line value: "粘贴客户消息 → 整理成 case → 下一步动作、已收集/还缺什么、草稿回复。确认后再发。"
- **Primary action:** "Load founder demo queue" or equivalent — for demo path; otherwise "Paste the message to start" is primary.

---

## 2. Information Hierarchy

- **Most prominent:** Current case — next move, collected, still needed.
- **Second:** Case handoff block — "Your next move" in large, readable text.
- **Third:** Draft to review, client prep, follow-up.
- **Fourth:** Recent messages, tracking status.

---

## 3. Case Cards (Queue)

- **Case focus:** Clear tag (e.g. Add car quote, Cancellation risk).
- **Attention state:** "Action now", "Your move", "Due today" — visible.
- **Preview:** One-line source text preview.
- **Action:** "Reopen case" — prominent.

---

## 4. Next Move Visibility

- "Your next move" should be a distinct block:
  - Label: "Your next move" (or 您的下一步)
  - Body: Large, bold, actionable sentence.
- Not buried in tags or long paragraphs.

---

## 5. Collected / Still Needed

- Green chips for collected.
- Orange chips for still needed.
- Grouped under clear section headers.
- Compact but readable.

---

## 6. Recent Messages

- Grouped in a "Recent customer messages" block.
- Bordered, distinct from action block.
- Max 3 messages; truncate if needed.

---

## 7. Reduce Debug-Screen Feeling

- **Remove or hide:** "Founder demo snapshot" — rename to "Demo queue" or "演示队列" and make it collapsible.
- **Remove or hide:** "Local/demo-safe workbench" — internal; not for broker.
- **Avoid:** Raw technical labels (e.g. "Case ID", "lifecycle_status").
- **Prefer:** Product-like labels ("Where this case stands", "Keep this case moving").

---

## 8. Section Naming

- "Paste the message to start" → "粘贴消息开始"
- "Case handoff" → Keep or use "Case 整理"
- "Draft to review before sending" → "草稿回复（确认后再发）"
- "Where this case stands now" → Keep.

---

## 9. Empty State

- When no case is open: Clear "Paste the message to start" with helpful placeholder.
- When queue is empty: "暂无 case。粘贴或加载演示队列开始。"

---

*End of Workbench UI Polish Spec*
