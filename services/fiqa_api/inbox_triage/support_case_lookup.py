"""Identifier → case resolution for the support head (Pilot Reliability Fix 3 completion).

Support knows a phone, a CLM-#### reference, or a WeChat person link — not a case_id.
This module turns one of those into the case_id that
``support_case_diagnosis.build_support_case_diagnosis`` already understands.

Rules of this module:
- Read-only. It resolves and projects; it never writes, binds, or issues tokens.
- Reuses the existing identity sources (phone index, case_ref unique index, One
  Active Case binding). It never stores a second copy of identity.
- The identifier the operator typed is never echoed back, and no contact detail,
  customer prose, token, or OpenID is projected into a match row.
- Diagnosis stays in ``support_case_diagnosis``; this module only calls it.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

LOOKUP_CONTRACT_VERSION = "support_case_lookup_v1"

IDENTIFIER_PHONE = "phone"
IDENTIFIER_CASE_REF = "case_ref"
IDENTIFIER_PERSON_LINK = "person_link"

# Bounded so an operator gets a choosable list, never a customer data dump.
MAX_MATCHES = 5
_MAX_HYDRATE = 12

# Opaque person-link prefixes we accept. A bare WeChat OpenID is deliberately not
# one of them: hashing it here would put a raw customer identifier in a support
# URL and its access logs. Callers must pass the wx_* key the client already uses.
_PERSON_LINK_PREFIXES = ("wx_", "anon-", "p26h-", "p35-")
_MIN_PERSON_LINK_LEN = 8

ERROR_IDENTIFIER_REQUIRED = "support_lookup_identifier_required"
ERROR_MULTIPLE_IDENTIFIERS = "support_lookup_one_identifier_at_a_time"
ERROR_INVALID_PHONE = "support_lookup_invalid_phone"
ERROR_INVALID_CASE_REF = "support_lookup_invalid_case_ref"
ERROR_INVALID_PERSON_LINK = "support_lookup_invalid_person_link"


class SupportLookupError(ValueError):
    """Rejected identifier. ``code`` is a stable, non-sensitive error code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _text(value: Any) -> str:
    return str(value or "").strip()


def resolve_identifier(
    *,
    phone: str | None = None,
    case_ref: str | None = None,
    person_link: str | None = None,
) -> tuple[str, str]:
    """Validate exactly one identifier and return ``(kind, normalized_value)``."""

    from services.fiqa_api.inbox_triage.case_ref import normalize_case_ref
    from services.fiqa_api.inbox_triage.phone_normalization import normalize_phone_digits

    supplied = [
        (IDENTIFIER_PHONE, _text(phone)),
        (IDENTIFIER_CASE_REF, _text(case_ref)),
        (IDENTIFIER_PERSON_LINK, _text(person_link)),
    ]
    present = [(kind, raw) for kind, raw in supplied if raw]
    if not present:
        raise SupportLookupError(ERROR_IDENTIFIER_REQUIRED)
    if len(present) > 1:
        # Never guess which customer the operator meant.
        raise SupportLookupError(ERROR_MULTIPLE_IDENTIFIERS)

    kind, raw = present[0]
    if kind == IDENTIFIER_PHONE:
        digits = normalize_phone_digits(raw)
        if len(digits) != 10:
            raise SupportLookupError(ERROR_INVALID_PHONE)
        return kind, digits
    if kind == IDENTIFIER_CASE_REF:
        ref = normalize_case_ref(raw)
        if not ref:
            raise SupportLookupError(ERROR_INVALID_CASE_REF)
        return kind, ref
    key = raw[:80]
    if len(key) < _MIN_PERSON_LINK_LEN or not key.startswith(_PERSON_LINK_PREFIXES):
        raise SupportLookupError(ERROR_INVALID_PERSON_LINK)
    return kind, key


def find_case_ids(kind: str, value: str) -> list[str]:
    """Resolve one validated identifier to candidate case_ids (newest-first where known)."""

    if kind == IDENTIFIER_PHONE:
        from services.fiqa_api.inbox_triage.case_truth_repository import list_cases_for_phone_lookup

        rows = list_cases_for_phone_lookup(value)
        return _dedupe([_text(row.get("case_id")) for row in rows if isinstance(row, dict)])

    if kind == IDENTIFIER_CASE_REF:
        from services.fiqa_api.inbox_triage.case_truth_repository import find_case_id_for_case_ref

        found = find_case_id_for_case_ref(value)
        return [found] if found else []

    if kind == IDENTIFIER_PERSON_LINK:
        from services.fiqa_api.inbox_triage.mp_customer_identity import lookup_bound_case_id

        found = _text(lookup_bound_case_id(value))
        return [found] if found else []

    return []


def _dedupe(case_ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for cid in case_ids:
        if not cid or cid in seen:
            continue
        seen.add(cid)
        out.append(cid)
    return out


def _case_is_active(case: dict[str, Any]) -> bool:
    from services.fiqa_api.inbox_triage.case_binding import is_case_open_for_binding
    from services.fiqa_api.inbox_triage.case_close import case_is_closed_history

    return bool(is_case_open_for_binding(case)) and not case_is_closed_history(case)


def rank_candidates(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Active cases first, then most recently touched. Deterministic on ties."""

    ordered = sorted(
        cases,
        key=lambda case: (
            _text(case.get("updated_at")),
            _text(case.get("created_at")),
            _text(case.get("case_id")),
        ),
        reverse=True,
    )
    ordered.sort(key=lambda case: 0 if _case_is_active(case) else 1)
    return ordered


def build_match_row(case: dict[str, Any]) -> dict[str, Any]:
    """Bounded, identifier-free row: just enough for an operator to choose a case."""

    from services.fiqa_api.inbox_triage.support_case_diagnosis import (
        build_support_case_diagnosis,
    )

    diagnosis = build_support_case_diagnosis(case)
    return {
        "case_id": _text(case.get("case_id")) or None,
        "case_ref": _text(case.get("case_ref")) or None,
        "service_lane": _text(case.get("service_lane")) or None,
        "case_status": _text(case.get("case_status")) or None,
        "lifecycle_status": _text(case.get("lifecycle_status")) or None,
        "waiting_on": _text(case.get("waiting_on")) or None,
        "claim_phase": _text(case.get("claim_phase")) or None,
        "active": _case_is_active(case),
        "workbench_test": bool(case.get("workbench_test")),
        "office_id": _text(case.get("asserted_org_id")) or None,
        "created_at": _text(case.get("created_at")) or None,
        "updated_at": _text(case.get("updated_at")) or None,
        "status": diagnosis.get("status"),
        "next_support_action_zh": diagnosis.get("next_support_action_zh"),
    }


def lookup_support_cases(
    *,
    kind: str,
    value: str,
    load_case: Callable[[str], dict[str, Any] | None],
    office_visible: Callable[[dict[str, Any]], bool] | None = None,
) -> dict[str, Any]:
    """Resolve an identifier to a bounded, ranked, office-filtered match list.

    ``load_case`` is the same read the support head uses, so a returned ``case_id``
    always resolves there. ``office_visible`` applies the caller's office boundary
    before anything about a case is projected.
    """

    case_ids = find_case_ids(kind, value)
    hydrated: list[dict[str, Any]] = []
    for cid in case_ids[:_MAX_HYDRATE]:
        case = load_case(cid)
        if not isinstance(case, dict):
            continue
        if office_visible is not None and not office_visible(case):
            continue
        hydrated.append(case)

    hydrated = rank_candidates(hydrated)
    visible = hydrated[:MAX_MATCHES]
    matches = [build_match_row(case) for case in visible]
    match_count = len(hydrated)

    return {
        "lookup_contract_version": LOOKUP_CONTRACT_VERSION,
        "identifier_kind": kind,
        "found": bool(matches),
        "match_count": match_count,
        "truncated": match_count > len(matches),
        "ambiguous": match_count > 1,
        "resolved_case_id": matches[0]["case_id"] if match_count == 1 else None,
        "matches": matches,
    }
