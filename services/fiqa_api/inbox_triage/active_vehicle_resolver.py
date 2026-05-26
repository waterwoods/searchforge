"""Resolve which customer turn defines the active vehicle in add-car threads.

Contract (priority):
1. Explicit VIN in the latest customer message
2. Explicit model / make in the latest message → match thread segment(s)
3. Explicit \"first car\" / re-anchor phrases → first vehicle segment (after ignore filters)
4. Ignore / exclude phrases remove candidate segments before 2–3
5. Fallback: defer to persisted active entity (caller; no segment index)

If multiple segments remain plausible and the message does not disambiguate: AMBIGUOUS
(do not switch active vehicle; caller surfaces clarify).

Runtime wiring (authority): ``triage.py`` does **not** import this module on the current
mainline — behavior is covered by ``tests/test_active_vehicle_resolver.py`` only.
Production vehicle lines are produced by triage heuristics + entity payload merge, then the
HTTP route overwrites from Postgres when ``_finalize_response_with_pg_truth`` applies.
See ``docs/DEPRECATED_PATHS.md`` (explicit ``active_vehicle_resolver`` section).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_VIN = re.compile(r"\b([a-hj-npr-z0-9]{17})\b", re.IGNORECASE)

# (aliases…) → slug used for matching / exclusion
_MODEL_ALIASES: list[tuple[frozenset[str], str]] = [
    (frozenset({"camry", "凯美瑞", "凱美瑞"}), "camry"),
    (frozenset({"civic", "思域"}), "civic"),
    (frozenset({"accord", "雅阁"}), "accord"),
    (frozenset({"corolla", "卡罗拉"}), "corolla"),
    (frozenset({"model y", "modely", "model-y", "model  y"}), "model_y"),
    (frozenset({"model 3", "model3"}), "model_3"),
    (frozenset({"crv", "cr-v", "本田crv"}), "crv"),
    (frozenset({"rav4", "rav 4"}), "rav4"),
    (frozenset({"highlander", "汉兰达"}), "highlander"),
    (frozenset({"outback"}), "outback"),
    (frozenset({"tesla", "特斯拉"}), "tesla"),
    (frozenset({"bmw", "宝马"}), "bmw"),
    (frozenset({"4runner", "4-runner"}), "4runner"),
    (frozenset({"cx-5", "cx5"}), "cx5"),
    (frozenset({"f-150", "f150"}), "f150"),
    (frozenset({"altima"}), "altima"),
]

_FIRST_CAR_RE = re.compile(
    r"(?i)(?:^|[\n。！？\s,.，])"
    r"(?:"
    r"go\s+back\s+to\s+(?:the\s+)?first|return\s+to\s+(?:the\s+)?first|"
    r"back\s+to\s+(?:the\s+)?first\s+(?:car|vehicle|line|one|thing)|"
    r"same\s+as\s+(?:the\s+)?(?:very\s+)?first|"
    r"\bfirst\s+car\b|"
    r"first\s+car\s+i\s+mentioned|car\s+i\s+said\s+earlier|first\s+bubble\s+wins|"
    r"\bfirst\s+one\b|"
    r"the\s+one\s+before|previous\s+car|earlier\s+car|"
    r"最开始那台|最开始那辆|第一个车|最开始的车|"
    r"第一台|最上面(?:那条)?|我一开始说|上面第一条|"
    r"为准.*(?:车|car)|最开始的(?:那个|那台)?车"
    r")",
)


def _norm_lower(s: str) -> str:
    return (s or "").strip().lower()


def segment_has_vehicle_signal(seg: str) -> bool:
    if not (seg or "").strip():
        return False
    if re.search(r"(?<![0-9])20[12][0-9]", seg):
        return True
    lo = seg.lower()
    return bool(
        re.search(
            r"(?i)(toyota|honda|tesla|bmw|nissan|lexus|subaru|ford|mazda|kia|"
            r"camry|civic|accord|corolla|model\s*[y3]|outback|rav4|cr-v|crv|"
            r"特斯拉|丰田|本田|宝马|凯美瑞|雅阁|思域)",
            lo,
        )
    )


def _bubble_matches_slug(seg: str, slug: str) -> bool:
    lo = _norm_lower(seg)
    for aliases, cand in _MODEL_ALIASES:
        if cand != slug:
            continue
        return any(a.lower() in lo for a in aliases)
    return slug in lo


def _slugs_present_in_segment(seg: str) -> frozenset[str]:
    out: set[str] = set()
    lo = _norm_lower(seg)
    for aliases, slug in _MODEL_ALIASES:
        if any(a.lower() in lo for a in aliases):
            out.add(slug)
    return frozenset(out)


def _explicit_model_slugs_from_message(msg: str) -> list[str]:
    lo = _norm_lower(msg)
    found: list[str] = []
    seen: set[str] = set()
    for aliases, slug in _MODEL_ALIASES:
        if not any(a.lower() in lo for a in aliases):
            continue
        if slug not in seen:
            seen.add(slug)
            found.append(slug)
    return found


def _parse_ignore_slugs(msg: str) -> frozenset[str]:
    lo = _norm_lower(msg)
    out: set[str] = set()
    if re.search(r"(?i)ignore\s+tesla|no\s+tesla|not\s+tesla|drop\s+tesla|\bignore\s+.*\btesla\b", lo):
        out.add("tesla")
    if "不要特斯拉" in msg or "别要特斯拉" in msg or "排除特斯拉" in msg:
        out.add("tesla")
    if re.search(r"(?i)ignore.*(?:cr-?v|crv)|drop.*(?:cr-?v|crv)|不要.*(?:cr-?v|crv)", lo):
        out.add("crv")
    m = re.search(
        r"(?i)ignore\s+(?:the\s+)?(camry|civic|model\s*y|tesla|crv|cr-v|toyota|honda|accord|corolla)",
        lo,
    )
    if m:
        tok = re.sub(r"\s+", "", m.group(1).lower())
        if "camry" in tok:
            out.add("camry")
        elif "civic" in tok:
            out.add("civic")
        elif "accord" in tok:
            out.add("accord")
        elif "corolla" in tok:
            out.add("corolla")
        elif "y" in tok or "modely" in tok:
            out.add("model_y")
            out.add("tesla")
        elif "tesla" in tok:
            out.add("tesla")
        elif "crv" in tok or "cr-v" in tok:
            out.add("crv")
        elif "toyota" in tok:
            out.add("toyota")
        elif "honda" in tok:
            out.add("honda")
    return frozenset(out)


def _segment_excluded_by_ignore(seg: str, ignore_slugs: frozenset[str]) -> bool:
    if not ignore_slugs:
        return False
    present = _slugs_present_in_segment(seg)
    for ign in ignore_slugs:
        if ign == "toyota":
            if "toyota" in _norm_lower(seg) or any(
                s in present for s in ("camry", "corolla", "rav4", "highlander", "4runner")
            ):
                return True
        elif ign == "honda":
            if "honda" in _norm_lower(seg) or any(s in present for s in ("civic", "accord", "crv")):
                return True
        elif ign in ("model_y", "model_3"):
            if "tesla" in present or _bubble_matches_slug(seg, "tesla"):
                return True
        elif ign in present or _bubble_matches_slug(seg, ign):
            return True
    return False


def _filtered_segment_indices(bubbles: list[str], ignore_slugs: frozenset[str]) -> list[int]:
    if not ignore_slugs:
        return list(range(len(bubbles)))
    return [i for i, seg in enumerate(bubbles) if not _segment_excluded_by_ignore(seg, ignore_slugs)]


def _vin_in_message(msg: str) -> bool:
    return bool(msg and _VIN.search(msg))


def _first_car_anchor(msg: str) -> bool:
    return bool(msg and _FIRST_CAR_RE.search(msg))


def _slug_position_in_text(msg: str, slug: str) -> int:
    lo = _norm_lower(msg)
    best = -1
    for aliases, cand in _MODEL_ALIASES:
        if cand != slug:
            continue
        for a in aliases:
            p = lo.rfind(a.lower())
            best = max(best, p)
    return best


@dataclass(frozen=True)
class ActiveVehicleResolveResult:
    """Resolver output for one add-car turn."""

    segment_index: int | None
    """Index into ``customer_bubbles`` for identity, or ``None`` to use PG / default merge."""

    ignore_entity: bool
    """When True, do not let Postgres active row override heuristic/segment identity."""

    is_ambiguous: bool
    """When True, do not switch vehicle; caller should clarify."""

    kind: str
    """Debug label: explicit_vin | explicit_model | first_created | ignore_remainder | use_entity | ambiguous."""


def resolve_add_car_active_vehicle(
    *,
    last_customer_message: str,
    customer_bubbles: list[str],
) -> ActiveVehicleResolveResult:
    bubbles = [(b or "").strip() for b in customer_bubbles]
    bubbles = [b for b in bubbles if b]
    if not bubbles:
        return ActiveVehicleResolveResult(
            segment_index=None, ignore_entity=False, is_ambiguous=False, kind="use_entity"
        )

    last = (last_customer_message or "").strip()
    last_idx = len(bubbles) - 1

    # 1) Explicit VIN — latest message
    if last and _vin_in_message(last):
        return ActiveVehicleResolveResult(
            segment_index=last_idx, ignore_entity=True, is_ambiguous=False, kind="explicit_vin"
        )

    ignore_slugs = _parse_ignore_slugs(last) if last else frozenset()
    filtered = _filtered_segment_indices(bubbles, ignore_slugs)
    if ignore_slugs and not filtered:
        return ActiveVehicleResolveResult(
            segment_index=None, ignore_entity=True, is_ambiguous=True, kind="ambiguous"
        )

    # 2) Explicit model in latest message
    if last:
        want = _explicit_model_slugs_from_message(last)
        if ignore_slugs:
            drop = set(ignore_slugs)
            if "tesla" in drop:
                drop.update({"tesla", "model_y", "model_3"})
            want = [w for w in want if w not in drop]
        if want:
            want_sorted = sorted(want, key=lambda s: _slug_position_in_text(last, s), reverse=True)
            primary = want_sorted[0]
            candidates = [i for i in filtered if _bubble_matches_slug(bubbles[i], primary)]
            uniq = sorted(frozenset(candidates))
            if len(uniq) == 1:
                return ActiveVehicleResolveResult(
                    segment_index=uniq[0],
                    ignore_entity=True,
                    is_ambiguous=False,
                    kind="explicit_model",
                )
            if len(uniq) > 1:
                # Same model repeated across refinement bubbles (e.g. Camry → "Actually 2020 Camry"):
                # latest matching segment wins; different models under one slug are rare for this MVP.
                if all(_bubble_matches_slug(bubbles[i], primary) for i in uniq):
                    return ActiveVehicleResolveResult(
                        segment_index=max(uniq),
                        ignore_entity=True,
                        is_ambiguous=False,
                        kind="explicit_model",
                    )
                return ActiveVehicleResolveResult(
                    segment_index=None, ignore_entity=True, is_ambiguous=True, kind="ambiguous"
                )
            # Mentioned model not found in remaining bubbles — fall through (do not force ambiguous)

    # 3) First-car re-anchor
    if last and _first_car_anchor(last):
        with_id = sorted(i for i in filtered if segment_has_vehicle_signal(bubbles[i]))
        if not with_id:
            return ActiveVehicleResolveResult(
                segment_index=None, ignore_entity=True, is_ambiguous=True, kind="ambiguous"
            )
        return ActiveVehicleResolveResult(
            segment_index=with_id[0],
            ignore_entity=True,
            is_ambiguous=False,
            kind="first_created",
        )

    # 4) Ignore-only → single surviving vehicle
    if ignore_slugs and len(filtered) == 1:
        return ActiveVehicleResolveResult(
            segment_index=filtered[0],
            ignore_entity=True,
            is_ambiguous=False,
            kind="ignore_remainder",
        )
    if ignore_slugs and len(filtered) > 1:
        return ActiveVehicleResolveResult(
            segment_index=None, ignore_entity=True, is_ambiguous=True, kind="ambiguous"
        )

    return ActiveVehicleResolveResult(
        segment_index=None, ignore_entity=False, is_ambiguous=False, kind="use_entity"
    )
