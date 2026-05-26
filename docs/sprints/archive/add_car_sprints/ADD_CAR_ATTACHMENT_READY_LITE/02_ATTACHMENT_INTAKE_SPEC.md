# Attachment Intake Spec

**Sprint:** Add-Car Attachment-Ready Lite  
**Purpose:** Define which attachments matter for add-car, how users are invited to upload, and when uploads remain optional.

---

## 1. Relevant Attachment Types for Add-Car

| Type | Label (EN) | Label (ZH) | Typical use |
|------|------------|------------|-------------|
| registration | Registration | 车辆登记 | DMV registration card |
| vin_photo | VIN photo | 车架号照片 | Photo of VIN on vehicle |
| dec_page | Current dec page | 保单首页 | Declaration page of current policy |
| screenshot | Screenshot / supporting image | 截图/辅助图片 | Generic supporting image |

---

## 2. Optional Accelerators (Not Mandatory)

All add-car attachments are **optional accelerators**:

- **Registration** — speeds up quote; not required to continue
- **VIN photo** — confirms VIN when provided; not required
- **Dec page** — helps broker verify current coverage; not required
- **Screenshot** — generic supporting material; not required

---

## 3. How Users Are Invited to Upload

- **Progressive invite:** After vehicle/zip/delivery collected, system can say: "如需加快，可上传车辆登记或车架号照片（可选）"
- **Non-blocking:** Never say "必须上传才能继续"
- **Placeholder in chat:** Upload area visible but not required to submit

---

## 4. When Uploads Are Helpful

- Customer has registration ready → upload speeds broker work
- Customer has VIN photo → reduces typo risk
- Customer has dec page → broker can verify current coverage
- Customer sends screenshot of notice → context for quote

---

## 5. When Uploads Remain Optional

- Customer has no documents handy → chat-only flow continues
- Customer prefers text-only → no pressure to upload
- Trial/demo without real documents → flow still works

---

## 6. Implementation Notes

- Accept: image/*, application/pdf
- Max size: 10 MB per file (configurable)
- Store: metadata (filename, type, size, created_at) + file on disk or object storage
- No extraction: store as-is; broker views manually

---

*See also: 03_ATTACHMENT_VISIBILITY_SPEC.md*
