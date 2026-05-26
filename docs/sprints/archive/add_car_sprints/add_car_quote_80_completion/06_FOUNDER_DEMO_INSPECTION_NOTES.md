# Add-Car Quote 80% Completion — Founder Demo / Inspection Notes

**Sprint:** Add-Car Quote 80% Completion  
**Purpose:** What the founder should inspect after implementation.

---

## 1. What to Inspect

| Area | What to Check |
|------|---------------|
| **First turn** | "想加一台X5" → system asks year+zip (or similar), NOT 6 items at once |
| **Second turn** | "2024年的" → system asks zip, NOT hand off |
| **Third turn** | "90210" → system asks delivery/driver OR hand off if delivery in T1 |
| **Fourth turn** | "下周拿车" → hand off with "报价资料已收集" |
| **Full info T1** | "2025 CR-V, 92705, 下周提车" → hand off immediately |
| **Collected chips** | Case shows year, model, zip, delivery in Collected |
| **Still needed** | When partial, shows delivery_date or primary_driver in Still needed |

---

## 2. Example Inputs That Best Show the Stronger Flow

| # | User Says (T1) | Expected System Ask |
|---|----------------|---------------------|
| 1 | 想加一台2021 Tesla Model Y | 先把地址邮编发我 / Send zip |
| 2 | 我买了台宝马X5，想问下保费多少钱 | 先把年份和地址邮编发我 |
| 3 | 新车保险多少 | 先把年份和车型发我 |
| 4 | 2025 Honda CR-V, 92705, 下周提车 | Hand off (full info) |
| 5 | 加一台X5 | 先把年份和地址邮编发我 |

---

## 3. What Should Feel Improved vs Before

| Before | After |
|--------|-------|
| Often 2 turns then hand off | 4–5 turns when user gives partial info |
| Zip alone enough for handoff | Zip + delivery or driver required |
| First turn lists 6 items | First turn asks 1–2 next things |
| No "additional drivers?" | Asks when natural |
| Case summary thin | Collected / Still needed richer |

---

## 4. Where to Inspect

- **Broker Workbench:** Load founder demo queue → Add-car case
- **Simulation Assistant:** Run SIM3 (Add-car Chinese), SIM15 (Add-car 3-turn)
- **Manual:** Type add-car messages in Unified Intake, observe replies

---

*See also: ADD_CAR_QUOTE_80_COMPLETION_REPORT.md (final report)*
