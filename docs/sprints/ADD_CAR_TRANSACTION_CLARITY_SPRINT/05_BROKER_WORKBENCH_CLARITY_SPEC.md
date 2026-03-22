# Broker Workbench Transaction Clarity Spec

## Goal

Brokers see the same **transaction identity** the customer is in, without new workflow engines.

## Current behavior (baseline)

- Case card shows category tag + inferred focus tag (e.g. **加车报价**) + collection stage + lifecycle.  
- One-liner: `可交办公室：加车报价 — …` / `信息收集中：…`.

## Sprint addition

When inferred focus is **Add car quote**, show a single **transaction context line** under the tag row in Case 整理:

> 加车报价事务：与客户入口「获取报价 / 加车」一致，请按可交办公室状态推进出价与核实。

## Non-goals

New status machine, new case types, or mandatory fields.

## File

- `ui/src/pages/UnifiedIntakePage.tsx` — `BrokerWorkbenchTab` Case 整理 block.
