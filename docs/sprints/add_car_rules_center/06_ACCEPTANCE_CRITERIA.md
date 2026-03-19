# Acceptance / SLA Criteria

**Sprint:** Minimal Business Rules Center for Add-Car Quote  
**Purpose:** Practical criteria for usability, safety, and usefulness.

---

## 1. Usability

- [ ] Business user can open Rules Center without engineering context
- [ ] Labels are in business language (no intent_key, soft_route, etc.)
- [ ] Edit flow is intuitive: edit → save draft → preview → publish

---

## 2. Clarity

- [ ] Current flow structure is visible (collection order, handoff condition)
- [ ] Editable fields have clear labels (第一句怎么回, 下一步问什么, etc.)

---

## 3. Safe Editing

- [ ] Draft state exists; edit does not affect live flow
- [ ] Publish requires explicit action
- [ ] Restore available to revert last publish

---

## 4. Preview Usefulness

- [ ] User can type sample customer message
- [ ] Preview shows system reply (as would be sent)
- [ ] Preview uses draft rules when draft exists

---

## 5. Publish Safety

- [ ] Publish copies draft → published
- [ ] Live triage uses published rules
- [ ] Empty/invalid values fall back to defaults

---

## 6. Would This Help Chen Kui / Assistants?

- [ ] Can change first reply wording
- [ ] Can change next-step prompts
- [ ] Can preview before publish
- [ ] No code deploy required for wording changes

---

*See also: 07_FOUNDER_DEMO_INSPECTION_NOTES.md*
