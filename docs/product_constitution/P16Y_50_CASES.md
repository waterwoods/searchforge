# P16-Y Phase 3 — 50 Realistic Broker Messages

**Date:** 2026-06-01  
**Sprint:** P16-Y Case Intelligence Hardening  
**Machine-readable:** `configs/p16y_50_cases.json`  
**Runner:** `PYTHONPATH=. python3 scripts/run_p16y_case_battery.py`

---

## Distribution

| Theme | IDs | Count |
|-------|-----|-------|
| Cancellation | Y01–Y05 | 5 |
| Missing documents | Y06–Y10 | 5 |
| Address change | Y11–Y13 | 3 |
| Driver addition | Y14–Y16 | 3 |
| Vehicle addition / removal | Y17–Y20 | 4 |
| Billing / payment | Y21–Y25 | 5 |
| Coverage questions | Y26–Y28 | 3 |
| Underwriting notices | Y29–Y31 | 3 |
| Renewal | Y32–Y34 | 3 |
| Claims | Y35–Y37 | 3 |
| Screenshot / notice confusion | Y38–Y40 | 3 |
| Multi-turn (5 cases) | Y41–Y45 | 5 |
| Edge / control | Y46–Y50 | 5 |

---

## Cases

### Cancellation (Y01–Y05)

| ID | Message |
|----|---------|
| Y01 | Notice: Policy will be cancelled in 7 days due to non-payment. Last notice. |
| Y02 | ⚠️ 重要：您的保单即将因未缴款而被取消 |
| Y03 | 保险公司说我的保单7天后要cancel，我已经付了呀 |
| Y04 | Carrier notice: Your policy will be cancelled due to non-payment. 这个是不是今天一定要处理？ |
| Y05 | 急死了 保单要停了 怎么办 |

### Missing documents (Y06–Y10)

| ID | Message |
|----|---------|
| Y06 | Underwriting requested driver's license copy. Client says "I already sent it last week." |
| Y07 | 需要驾照 copy 客户说上周寄了 |
| Y08 | UW follow up - need dec page + garaging proof. 客户说上周发过了 |
| Y09 | carrier 说 declaration page missing，这个什么意思 |
| Y10 | Escrow department requests updated declaration page for loan refinance. Due in 14 days. |

### Address change (Y11–Y13)

| ID | Message |
|----|---------|
| Y11 | 我搬家了，新地址是94588 Pleasanton，保单地址要改吗？ |
| Y12 | Moved to 90210 last month — need to update garaging address on both cars |
| Y13 | 客户说从San Jose搬到Fremont了，garaging proof要重新发吗 |

### Driver addition (Y14–Y16)

| ID | Message |
|----|---------|
| Y14 | 我儿子刚拿驾照，想加到我的保单上，需要准备什么？ |
| Y15 | Add my wife as a driver on the 2020 Camry policy |
| Y16 | teen driver just got license — how do I add them? VIN 1HGCM82633A004352 |

### Vehicle addition / removal (Y17–Y20)

| ID | Message |
|----|---------|
| Y17 | 想加一台2021 Tesla Model Y，下周提车，今天能不能先出报价 |
| Y18 | I bought a new BMW X5, how much is insurance? |
| Y19 | 2024 Honda CR-V VIN 5J6RT6H50RL012345 zip 92618 delivery Friday — quote please |
| Y20 | 客户卖掉旧车了，想把2014 Honda Accord从保单拿掉 |

### Billing / payment (Y21–Y25)

| ID | Message |
|----|---------|
| Y21 | Payment failed. Your card on file was declined. Please update payment method. |
| Y22 | 这个是不是保单要停了？我昨天收到账单 overdue |
| Y23 | AutoPay failed again, please update card to avoid interruption in coverage |
| Y24 | 这个月保费太高了，能不能看看怎么降一点 |
| Y25 | Client says renewal premium is too high, can we review options? |

### Coverage questions (Y26–Y28)

| ID | Message |
|----|---------|
| Y26 | Need SR-22 filing proof for DMV suspension clearance, what should client bring? |
| Y27 | 客户问 liability 100/300 够不够，要不要加 umbrella |
| Y28 | Does comprehensive cover windshield replacement? 2022 Tesla |

### Underwriting (Y29–Y31)

| ID | Message |
|----|---------|
| Y29 | Underwriting needs clarification on prior claims. Please respond within 10 days. |
| Y30 | UW questionnaire incomplete — need signed form by 3/15/2026 |
| Y31 | 核保说之前事故记录对不上，要我补说明，deadline Friday |

### Renewal (Y32–Y34)

| ID | Message |
|----|---------|
| Y32 | Renewal reminder: Your policy renews in 45 days. No action needed at this time. |
| Y33 | 续保通知到了，保费涨了30%，客户很生气 |
| Y34 | Policy #CA-8829101 renews March 15 — client wants to shop around first |

### Claims (Y35–Y37)

| ID | Message |
|----|---------|
| Y35 | 刚出事故了，对方追尾我，现在要报claim吗？保单号8829101 |
| Y36 | Rear-ended yesterday on 101, other driver has no insurance. What do I do? |
| Y37 | 玻璃裂了，走保险还是自己修？deductible 500 |

### Screenshot / notice (Y38–Y40)

| ID | Message |
|----|---------|
| Y38 | 客户发来一张截图 上面是dmv的信 看不懂 |
| Y39 | 这个英文 notice 看不懂 |
| Y40 | 客户发来截图：保单申请需要签名，但客户说「我签了呀，怎么还说要签？」 |

### Multi-turn (Y41–Y45)

| ID | Thread |
|----|--------|
| Y41 | T1: Payment failed notice → T2: Paid + screenshot → T3: When will coverage be restored? |
| Y42 | T1: 想加2021 Camry → T2: VIN + zip |
| Y43 | T1: UW need DL → T2: 驾照正反面都发你微信了 |
| Y44 | T1: 保单要cancel了 → T2: 不是payment问题，是地址不对被UW退回了 |
| Y45 | T1: 续保费太高 → T2: 我发你账单了，你看能不能换便宜点的coverage |

### Edge / control (Y46–Y50)

| ID | Message |
|----|---------|
| Y46 | [Forwarded email — generic marketing footer only] |
| Y47 | Your policy is pending issuance. We will notify you within 5-7 business days. |
| Y48 | Lienholder requests certificate of insurance. Policy number and effective dates needed. |
| Y49 | 联系人工 |
| Y50 | Your proof of insurance has been emailed to the DMV. No further action required. |

---

*End of P16-Y Phase 3 — 50 Cases*
