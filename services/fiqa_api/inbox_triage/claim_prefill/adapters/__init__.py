"""C02 Adapters — own classification policy. Workflow must never import these."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.claim_prefill.adapters.mock_adapter import (
    MockPrefillClassifierAdapter,
    get_default_classifier_adapter,
)
from services.fiqa_api.inbox_triage.claim_prefill.adapters.protocol import (
    PrefillClassifierAdapter,
)

__all__ = [
    "MockPrefillClassifierAdapter",
    "PrefillClassifierAdapter",
    "get_default_classifier_adapter",
]
