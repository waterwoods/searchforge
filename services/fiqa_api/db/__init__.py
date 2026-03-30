"""
Stage 1 Service Record — Postgres foundation (schema + optional dual-write).

JSON case/session stores remain the pilot source of truth unless dual-write is enabled.
"""

from __future__ import annotations
