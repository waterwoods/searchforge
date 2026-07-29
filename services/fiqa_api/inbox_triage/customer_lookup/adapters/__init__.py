"""C01 Adapters — own datasource protocols. Workflow must never import these."""

from __future__ import annotations

from services.fiqa_api.inbox_triage.customer_lookup.adapters.mock_adapter import (
    MockCustomerDirectoryAdapter,
    get_default_directory_adapter,
)
from services.fiqa_api.inbox_triage.customer_lookup.adapters.protocol import (
    CustomerDirectoryAdapter,
)

__all__ = [
    "CustomerDirectoryAdapter",
    "MockCustomerDirectoryAdapter",
    "get_default_directory_adapter",
]
