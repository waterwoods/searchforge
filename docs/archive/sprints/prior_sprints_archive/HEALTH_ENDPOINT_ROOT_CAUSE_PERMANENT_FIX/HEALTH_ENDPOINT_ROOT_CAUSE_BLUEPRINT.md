# Health Endpoint Root-Cause Blueprint

**Sprint:** Health Endpoint Root-Cause + Permanent Fix  
**Product context:** SearchForge → Chen Kui Insurance Unified Entry (fiqa-api on Cloud Run)  
**Date:** 2026-03-22  

## Problem statement

Post-deploy and monitoring checks against `GET /healthz` repeatedly report failure (often **404**), while `GET /readyz` and `GET /health/live` appear healthy. This creates false alarms, erodes trust in deploy output, and wastes time on “phantom” backend bugs.

## Goal

1. Establish **production truth**: why `/healthz` fails when it fails.  
2. Choose a **single canonical contract** for liveness vs readiness on Cloud Run.  
3. Align **app routes (where needed), deploy scripts, Docker healthcheck, and runbooks** so checks stop failing for the wrong reason.

## Non-goals

Add-Car logic, frontend, OCR, carrier APIs, unrelated refactors.

## Success shape

- Root cause is **explicit** and evidenced (not “maybe cold start”).  
- Operators know **which URL to curl** after deploy.  
- No lingering story of “healthz is flaky” without an explanation.

## Hypothesis lane (pre-audit)

Candidates to eliminate with evidence:

- FastAPI route missing / wrong prefix  
- Duplicate routers  
- Deploy script wrong URL  
- **Platform / edge behavior before the container**  
- Environment mismatch (different app entrypoint)

The audit and reproduction steps in companion docs narrow this to one judgment.
