/**
 * Frontend-only contract grouping for POST /api/inbox/triage (TriageResult).
 *
 * Lifecycle authority: `case_lifecycle` is set on the server by
 * `routes/inbox_triage._attach_case_lifecycle` + `case_lifecycle._derive_case_lifecycle`
 * (may overlay `formal_submitted_at` from the persisted case). Prefer that field when
 * present; `caseLifecycleDisplay.resolveCaseLifecycle` mirrors `_derive_case_lifecycle` for old payloads only.
 *
 * Vehicle fields on the wire: when Postgres has an active vehicle entity for the session, the
 * route applies it after triage (`_apply_pg_active_vehicle_identity_last`). Treat
 * `primary_vehicle_summary` / `vehicle_key` in **Core** as that post-overlay truth for UX.
 *
 * Layering:
 * - **Core** — identity, lane, lifecycle/progress, broker-visible summary lines:
 *   safe to drive primary customer + office UX (excluding explicit debug telemetry below).
 * - **Optional signals** — assist payload, perf metrics, routing path: additive / diagnostic only.
 *
 * These types do **not** narrow the wire format; they are views over the full `TriageResult`.
 * Never delete fields from `TriageResult` in `inboxTriage.ts` to “match” this file.
 */

import type { TriageResult } from './inboxTriage';

/** Stable fields the product UI should treat as authoritative for headings, strips, and vehicle identity. */
export type TriageResultCore = Pick<
    TriageResult,
    | 'primary_vehicle_summary'
    | 'vehicle_key'
    | 'broker_next_step'
    | 'issue_category'
    | 'add_car_turn_intent'
    | 'case_lifecycle'
    | 'formal_submitted_at'
    | 'triage_mode'
    | 'handoff_ready'
    | 'quote_ready_status'
    | 'lifecycle_status'
    | 'case_status'
    | 'source_text'
>;

/** Suggestive / debug / perf — must not gate primary broker workflow. */
export type TriageResultOptionalSignals = Pick<TriageResult, 'assist' | 'route_perf' | 'triage_turn_metrics' | 'triage_path'>;

export function pickTriageResultCore(t: TriageResult): TriageResultCore {
    return {
        primary_vehicle_summary: t.primary_vehicle_summary ?? null,
        vehicle_key: t.vehicle_key ?? null,
        broker_next_step: t.broker_next_step,
        issue_category: t.issue_category,
        add_car_turn_intent: t.add_car_turn_intent ?? null,
        case_lifecycle: t.case_lifecycle,
        formal_submitted_at: t.formal_submitted_at,
        triage_mode: t.triage_mode,
        handoff_ready: t.handoff_ready,
        quote_ready_status: t.quote_ready_status,
        lifecycle_status: t.lifecycle_status,
        case_status: t.case_status,
        source_text: t.source_text,
    };
}

/** Non-mutating slice of optional / debug fields (may be empty objects or null). */
export function pickTriageResultOptionalSignals(t: TriageResult): TriageResultOptionalSignals {
    return {
        assist: t.assist ?? null,
        route_perf: t.route_perf ?? null,
        triage_turn_metrics: t.triage_turn_metrics ?? null,
        triage_path: t.triage_path,
    };
}

/**
 * True when the payload carries routing or latency/debug material worth surfacing in office tooling
 * (e.g. a subtle tag). Does not imply correctness — only presence of optional telemetry.
 */
export function hasDebugSignals(t: TriageResult): boolean {
    const o = pickTriageResultOptionalSignals(t);
    if ((o.triage_path ?? '').trim().length > 0) return true;
    if (o.assist != null && typeof o.assist === 'object' && Object.keys(o.assist).length > 0) return true;
    if (o.route_perf != null && typeof o.route_perf === 'object' && Object.keys(o.route_perf).length > 0) return true;
    if (o.triage_turn_metrics != null && typeof o.triage_turn_metrics === 'object' && Object.keys(o.triage_turn_metrics).length > 0) {
        return true;
    }
    return false;
}
