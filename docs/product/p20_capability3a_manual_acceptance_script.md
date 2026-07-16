# P20 Capability 3A — Manual Browser Acceptance Script

**Date:** 2026-07-15  
**Scope:** Send Request + Customer QR/Link (founder validation with Chen Kui)  
**Do not:** complete customer submission (Capability 3B), deploy, or commit unless separately authorized

## Preconditions

- Workbench open on document intake
- TEST Claim create path available (Capability 2)
- Backend includes SendRequest route + customer access migration/schema
- Mini Program / H5 can open existing Slice 1 customer task via launch token

## Script

| # | Step | Expected |
|---|------|----------|
| 1 | Broker creates/opens a **TEST Claim** | Case opens; Missing Information checklist visible |
| 2 | Select **VIN** (and optional instruction); click **Save request draft** | Draft saved; primary button becomes **Send Request**; secondary **Edit** |
| 3 | Click **Send Request** once | UI shows **Sent to customer**, QR, **Copy Link**, progress **0 / 1**, status **Waiting for customer** |
| 4 | Confirm instruction copy | “让客户用微信扫码并补充资料。” |
| 5 | Refresh / reopen the case | Same QR/link access card (no second request / no new access) |
| 6 | Confirm default UI | No access ID, request group ID, token, aggregate version, or workflow engine names in the main card |
| 7 | Open Advanced/Developer (optional) | Channel / expiry / production QR note only |
| 8 | Copy Link | Clipboard has the same URL encoded in the QR |
| 9 | Scan QR / open link | Existing customer task opens for the VIN request item — **do not** require submitting in 3A |
| 10 | Invalid Send with a new command after success | Rejected / no duplicate open request |
| 11 | Invalid Send with same command identity after transport loss | Replayed original accepted result |
| 12 | Invalid invalid/expired token where feasible | Safe error; no case details leaked |

## Screenshots to capture

1. Saved draft before Send  
2. Access card after Send (QR + Copy Link)  
3. After refresh (same access)  
4. Mini Program / H5 opening the expected VIN task  

## Pass criteria

- Broker completes New Case → Choose Missing Information → Send Request without Cursor/SQL  
- One open Request More + one customer access  
- QR and Copy Link share the same access  
- Refresh does not mint a new access  
- No Capability 3B customer submission changes required for this gate  

## Known pilot limitation

Native WeChat unlimited Mini Program QR (`wxacode.getUnlimited`) is not wired. Pilot QR encodes the HTTPS claim-task deep link that carries the opaque signed token.
