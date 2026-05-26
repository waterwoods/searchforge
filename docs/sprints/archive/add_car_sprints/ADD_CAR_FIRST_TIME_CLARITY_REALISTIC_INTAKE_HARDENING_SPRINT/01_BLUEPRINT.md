# ADD-CAR FIRST-TIME CLARITY + REALISTIC INTAKE HARDENING — Blueprint

## Sprint goal

Improve the Add-Car flagship flow so that (1) first-time users understand what to do, what happens after submit, and how the office takes over, and (2) realistic North American Chinese-style phrasing is interpreted more reliably for quote-critical fields (dates, drivers, materials).

## Why now

The product is portal- and case-oriented; Add-Car is the strongest monetizable template. Weak first-use clarity and fragile colloquial intake raise office follow-up cost and erode broker trust in pilot.

## Scope

**In scope:** Add-Car UI microcopy and empty-state clarity; optional visual emphasis of Add-Car as the default path; targeted rule-based extraction hardening in inbox triage for delivery/driver/material signals; a small realistic scenario battery script for regression-style checks.

**Out of scope:** Triage engine rewrite, CRM/auth, broad homepage redesign, large persistence changes, heavy documentation.

## Current practical problems (pre-sprint)

- Empty-state copy did not spell out the three entry modes (button / free text / structured card) or post-submit office ownership in one place.
- Rule-based `has_delivery` missed common English/Chinese phrasing (e.g. Friday / pickup one word / calendar dates without repeating every keyword).
- Driver phrasing like “主要我本人开” and multi-driver “我跟老婆都可能开” was under-covered vs existing markers.
- Material-state (先发行吗 / 还没拿到 VIN) was handled in reply logic but not always surfaced as structured `collected_fields` for broker visibility.

## Target outcome

- First-time users see a clearer primary path and a single readable explanation of entry modes and office handoff.
- Add-Car extraction flags better match realistic Chinglish and office-style messages; scenario battery can be re-run under `LLM_GENERATION_ENABLED=0`.
