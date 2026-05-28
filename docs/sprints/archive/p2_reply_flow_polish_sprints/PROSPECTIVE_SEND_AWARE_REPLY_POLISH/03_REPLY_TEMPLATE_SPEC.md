# Reply Template Spec — Prospective Send Lead

## When it applies

Last customer message matches `_is_prospective_send_offer_message()` (extended in this sprint for 我先发给你看看行吗 / 行不行-style permission asks).

## Chinese leads (one sentence, then existing Add-Car text)

| Signal in message | Lead |
|-------------------|------|
| 微信 | 可以，微信发我就行。 |
| 截图 | 可以，截图先发我，我这边一起看。 |
| 行驶证 / 照片 / 材料, or dec/declaration | 可以，先发我就行，我这边一起整理给办公室。 |
| Default | 可以，先发我就行，我这边一起整理给办公室。 |

## English leads

- WeChat: `Yes—WeChat works. `
- Screenshot: `Yes—send the screenshot and I will review it with your file. `
- Default: `Yes—send it over and I will bundle it for the office. `

## Placement

- **Before** acknowledgement + next ask when collecting.  
- **Before** standard Add-Car handoff line when `handoff_ready` and `is_add_car`.  
- Do **not** replace `already_sent` warmer copy (`您说材料发过了…`).

## Regex extensions (detection only)

- `(我先)?发给你看看行吗?` / `先发给你看看行吗` / `发给你.{0,6}行吗`
- `行不行` + `发` without completed-send markers (发过了 / 已经发 / 发了 / 发你了 / 发您了)
