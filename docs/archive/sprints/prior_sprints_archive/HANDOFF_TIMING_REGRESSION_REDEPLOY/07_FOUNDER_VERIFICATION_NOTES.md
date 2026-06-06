# Founder Verification Notes

**Sprint:** Handoff Timing Regression + Redeploy Sprint  
**Purpose:** What founder should test on Vercel after redeploy.

---

## What to Test on Vercel

1. **Premium 3-turn (HT3):** 续保涨了好多 → 账单发你了 → 其中一辆去掉会便宜吗  
   - Expect: T2 handoff or T3 handoff (if fix applied)  
   - Watch: broker_next_step; collected fields

2. **Payment 3-turn (HT9):** payment failed 怎么办 → 我昨天付了 → 截图发你微信了  
   - Expect: T2 handoff or T3 handoff (if fix applied)  
   - Watch: broker_next_step; screenshot_sent in collected

3. **Add-car + garaging (HT8):** 加车 2024 X5 → 90210 下周提车 对了 garaging proof 是什么  
   - Expect: Answer garaging question + handoff T2  
   - Watch: No driver ask; answer present

4. **Add-car + driver T3 (HT1):** 加车 2024 Tesla Model Y → 90210 下周提车 → 对了 是我老婆开  
   - Expect: Ask driver T2; handoff T3  
   - Watch: Driver in collected

5. **Missing doc + garaging T3 (HT2):** 要dec page和garaging proof → dec page发你了 → garaging proof 是什么意思  
   - Expect: Handoff T2; T3 would append  
   - Watch: broker sees both

---

## Good Enough for Trial

- HT8 fix working (answer + handoff)
- HT1, HT4, HT5, HT6, HT7 strong
- HT3, HT9, HT10: T2 handoff acceptable; T3 append
- No new regressions

---

*End of Notes*
