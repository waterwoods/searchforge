"""Lightweight production-safe analytics hooks (structured logging + funnel buffer)."""

from services.fiqa_api.analytics.minimal_events import track_event

__all__ = ["track_event"]
