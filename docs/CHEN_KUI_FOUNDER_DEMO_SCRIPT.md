# Chen Kui Founder Demo Script

**Purpose:** One tight founder-demo story for the Unified Intake mainline.

## 1. Core promise

Show only this:

1. A messy customer or carrier message comes in
2. Unified Intake turns it into one usable broker case
3. The broker keeps follow-up continuity without starting over

## 2. Two surfaces: Customer Entry + Broker Workbench

The page has two tabs:

- **客户入口 (Customer Entry)** — default. Simple front door for customers. One input box, one CTA. Customer gets a useful first-pass response; the case is saved to the broker workbench.
- **Broker Workbench** — internal triage, case cards, recent cases, follow-up.

**Best demo order:** Show Customer Entry first (customer submits a messy message), then switch to Broker Workbench to show the case and broker continuity.

## 3. Strongest route (exact order)

### Step 1: Customer Entry (optional but recommended)

On the **客户入口** tab, paste a messy customer message, e.g.:

```text
客户问：这个英文 notice 说 payment failed，我现在怎么办？
```

Or for an English add-car example:

```text
I bought a new BMW X5, how much is insurance?
```

Click **提交**. The customer sees an intent-specific response (payment risk: urgency + ask for notice; add-car: ask for year, model, VIN, delivery date, zip, driver) — not generic "provide more context." Then "Chen Kui's office will review this and follow up." Click **查看工作台** to switch to the broker tab with this case.

### Step 2: Load founder demo queue (Broker tab)

Click **Load founder demo queue** in the Founder demo snapshot card. This seeds 10 demo-safe cases that look like one day of Chen Kui office traffic.

**What opens first:** The cancellation-risk case auto-opens. This is intentional — it shows urgency and same-day broker action immediately.

### Step 3: Show cancellation risk (already open)

The first case is:

```text
Carrier notice: Your policy will be cancelled due to non-payment. 客户说这个是不是今天一定要处理？
```

What to say:

- "This is the one entry point. I paste the raw message without cleaning it up."
- "The system turns it into one case with urgency, the broker's next move, client prep, and a sendable draft."
- "This is useful because the risky cases stop getting buried in message noise."

### Step 4: Reopen saved follow-up

Scroll to **Recent broker cases**. Find the **Missing document follow-up** case (UW follow up - need dec page + garaging proof). Click **Reopen case**.

```text
UW follow up - need dec page + garaging proof. 客户说上周发过了
```

What to say:

- "The case does not disappear after triage."
- "I can reopen it, see who we are waiting on, when to check again, and the latest broker note."
- "This is the closed loop: triage once, then continue the work instead of re-reading the whole message chain."

### Step 5: One everyday revenue case

Reopen either **Add car quote** or **Premium review** from Recent cases.

What to say:

- "This is not only for urgent notices; it also handles the repetitive office work that takes time every day."
- "It gives the broker a practical next move and a client-ready starting reply."

## 4. Founder demo queue

The **Load founder demo queue** action seeds 10 demo-safe cases:

- Cancellation risk (opens first)
- Missing document follow-up (saved, waiting on client)
- Add-car quote request
- Premium review
- DMV / SR-22 help
- Payment failed / lapse risk
- Remove car
- English notice + Chinese confusion
- Declaration page missing
- Chinese cancellation summary

This queue is demo-safe input data running through the real local triage and saved-case flow.

For a clean repeatable queue before a meeting, run:

```bash
PYTHONPATH=. python3 scripts/prepare_unified_intake_founder_demo.py
```

## 5. What is real now

- **Customer Entry tab:** customer-facing input, first-pass response, case saved to broker workbench
- pasted-text triage
- structured case card
- urgency / broker next move / client prep / client draft
- local saved cases
- reopen / status / waiting-on / next-contact memory
- broker note and activity trail
- business snapshot counts derived from the local queue

## 6. What is mock or demo-safe

- founder demo starter queue inputs
- the exact recent-case mix shown right after loading the starter queue

## 7. What is deferred

- inbox sync
- OCR upload inside the product
- CRM history
- customer identity linking
- auto-send
- analytics or ROI certainty beyond the visible local queue

## 8. What not to say

Do not claim:

- "It connects to WeChat or email already."
- "It reads screenshots directly in the product."
- "It automatically sends replies."
- "It already has full customer memory."
- "These queue metrics are production analytics."

## 9. One-sentence sell

**Customer side:** "Customers can paste their problem here and get a useful first response; the case goes straight to the broker workbench."

**Broker side:** "You can paste the messy message you already received, get a broker-usable case immediately, and keep lightweight follow-up continuity so urgent work is less likely to get missed."
