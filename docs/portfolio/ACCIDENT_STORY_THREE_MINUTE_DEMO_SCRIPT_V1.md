# Accident Story — Three-Minute Demo Script V1

**Audience:** interview / Founder demo · **Not** Production · **Not** real-customer accuracy claim

## Live path (≈3 minutes)

1. Customer enters incomplete Chinese story: `昨天开车的时候被追尾，没有受伤。`
2. AI shows organized draft (`AI已帮您整理`) with known injury = no
3. AI asks only the two missing items (time clock + location)
4. Customer confirms → facts become `customer_confirmed`
5. Broker Brief shows three layers: 客户原始描述 / AI整理草稿 / 客户已确认事实
6. Show one timeout/fallback case → **AI回退** tag; manual path still works
7. Flash metrics + kill switch (`ACCIDENT_STORY_ASSISTANT_ENABLED=0`)

## Interview narrative (concise)

Customer discovery showed free-form accident stories stalling on Must Have forms. We kept Claim lifecycle deterministic and used a bounded LangGraph assist (propose → ≤3 questions → confirm). Golden evals + LangSmith redaction + live synthetic canary proved safety gates; Postgres durable metrics and kill switches make a five-case office pilot operable without claiming Production deployment or real-customer accuracy.
