"""
Tracing placeholder for the orchestrator.

Future work will integrate with an OTLP-compatible backend. The current
implementation only provides a no-op context manager to avoid coupling modules
to a specific tracing provider during milestone M0.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def span(name: str) -> Iterator[None]:
    _ = name
    yield

