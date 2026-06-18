"""
P16 OCR Kill Test — field schema and output data structures.

Kill-test only. Not wired into production flows.
"""
from dataclasses import dataclass, field
from typing import Any, Optional

# The 8 core add-car fields
CORE_FIELDS = [
    "customer_name",
    "phone",
    "vin",
    "year",
    "make_model",
    "garaging_zip",
    "primary_driver",
    "delivery_or_effective_date",
]

# Minimum required fields for packet_ready (primary_driver is "surfaced" not hard-blocked)
REQUIRED_FOR_PACKET_READY = [
    "customer_name",
    "phone",
    "vin",
    "year",
    "make_model",
    "garaging_zip",
    "delivery_or_effective_date",
]


@dataclass
class ExtractedField:
    value: str = ""
    confidence: float = 0.0
    source_file: str = ""
    source_quote: str = ""
    needs_confirmation: bool = True
    notes: str = ""

    def is_present(self) -> bool:
        return bool(self.value and self.value.strip())

    def to_dict(self) -> dict:
        return {
            "value": self.value,
            "confidence": self.confidence,
            "source_file": self.source_file,
            "source_quote": self.source_quote,
            "needs_confirmation": self.needs_confirmation,
            "notes": self.notes,
        }


@dataclass
class ConflictRecord:
    field: str
    values: list
    sources: list
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "field": self.field,
            "values": self.values,
            "sources": self.sources,
            "notes": self.notes,
        }


@dataclass
class KillTestResult:
    case_id: str
    input_files: list = field(default_factory=list)
    document_types_detected: list = field(default_factory=list)
    extracted_fields: dict = field(default_factory=dict)
    missing_fields: list = field(default_factory=list)
    conflicts: list = field(default_factory=list)
    unrelated_documents: list = field(default_factory=list)
    second_vehicle_detected: bool = False
    packet_ready: bool = False
    packet_readiness_reason: str = ""
    quote_ready_packet_draft: str = ""
    model_used: str = ""
    runtime_seconds: float = 0.0
    cost_estimate_usd: Optional[float] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "input_files": self.input_files,
            "document_types_detected": self.document_types_detected,
            "extracted_fields": {
                k: v.to_dict() if isinstance(v, ExtractedField) else v
                for k, v in self.extracted_fields.items()
            },
            "missing_fields": self.missing_fields,
            "conflicts": [
                c.to_dict() if isinstance(c, ConflictRecord) else c
                for c in self.conflicts
            ],
            "unrelated_documents": self.unrelated_documents,
            "second_vehicle_detected": self.second_vehicle_detected,
            "packet_ready": self.packet_ready,
            "packet_readiness_reason": self.packet_readiness_reason,
            "quote_ready_packet_draft": self.quote_ready_packet_draft,
            "model_used": self.model_used,
            "runtime_seconds": round(self.runtime_seconds, 2),
            "cost_estimate_usd": self.cost_estimate_usd,
            "error": self.error,
        }
