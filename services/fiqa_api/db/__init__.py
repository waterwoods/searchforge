"""
Stage 1 Service Record — Postgres foundation (schema + optional dual-write).

In-progress intake sessions are stored in Postgres (or in-process when no DB URL is set).
JSON case files remain part of the pilot path unless DB-primary case writes are enabled.
"""

from __future__ import annotations
