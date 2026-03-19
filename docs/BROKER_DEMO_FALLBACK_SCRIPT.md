# Broker Demo Fallback Script

Use when **Live retrieval fails** (backend down, Qdrant unavailable, network error).

## When to Use

- Status bar shows **Offline** (orange)
- Backend error banner: "Backend unreachable"
- Any question returns an error

## Steps (30 seconds)

1. **Say:** "Let me switch to our offline demo mode. We keep pre-saved answers for the most common questions so the demo can run even when the live system is unavailable."

2. **Do:** Refresh the page (F5 or Ctrl+R).

3. **Wait** for the orange banner: "演示模式（预设答案）— 即时检索暂不可用。请点击上方 5 个推荐问题加载预设答案，演示可正常进行。"

4. **Click** the recommended questions (in order; 5 available offline):
   - 我刚买了辆新车（加州），最低需要买哪些保险？大概怎么配比较合理？
   - 我的车注册被暂停了（可能是保险问题），我该怎么恢复？需要交多少钱/提交什么材料？
   - 客户问我：怎么查保险公司/经纪人是不是合规？加州官方在哪里能查到？
   - 客户想省钱：哪些因素会影响保费？有哪些常见折扣/优惠？
   - 出险后理赔流程是怎样的？

5. **Continue** the demo script from Question 1. The answers and citations will load from the pre-saved pack. Do **not** type custom questions — they will fail in Offline mode.

6. **Say (optional):** "In offline mode we use pre-saved answers for these five questions. When the live system is available, you can ask any question and get real-time retrieval."

## What Works in Offline Mode

- ✅ The 5 recommended questions (click only)
- ✅ 建议结论, 下一步怎么做, 权威依据
- ✅ 复制给客户 button
- ✅ Same UI, same broker-focused flow

## What Does Not Work

- ❌ Typing custom questions
- ❌ Real-time retrieval from Qdrant

## After the Demo

- Run `bash scripts/demo_pre_checklist.sh` to confirm state
- If Qdrant becomes active later, run the Qdrant recovery flow (see `docs/QDRANT_RECOVERY_CHECKLIST.md`)
