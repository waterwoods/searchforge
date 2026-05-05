/**
 * Frontend-only contract grouping for POST /api/inbox/triage (TriageResult).
 *
 * Layering:
 * - **Core** — vehicle identity, lane, next step: safe to drive primary broker/office UI.
 * - **Optional signals** — assist payload, perf metrics, routing path: additive / diagnostic only.
 *
 * These types do **not** narrow the wire format; they are views over the full `TriageResult`.
 * Never delete fields from `TriageResult` in `inboxTriage.ts` to “match” this file.
 */

import type { TriageResult } from './inboxTriage';

/** Stable vehicle identity + progress signals the broker UI should trust first. */
export type TriageResultCore = Pick<TriageResult, 'primary_vehicle_summary' | 'vehicle_key' | 'broker_next_step'> & {
    /** Lane / category (generic intent axis). */
    issue_category: TriageResult['issue_category'];
    /** Add-car resolved intent when present; optional on non-add-car turns. */
    add_car_turn_intent: TriageResult['add_car_turn_intent'];
};

/** Suggestive / debug / perf — must not gate primary broker workflow. */
export type TriageResultOptionalSignals = Pick<TriageResult, 'assist' | 'route_perf' | 'triage_turn_metrics' | 'triage_path'>;

export function pickTriageResultCore(t: TriageResult): TriageResultCore {
    return {
        primary_vehicle_summary: t.primary_vehicle_summary ?? null,
        vehicle_key: t.vehicle_key ?? null,
        broker_next_step: t.broker_next_step,
        issue_category: t.issue_category,
        add_car_turn_intent: t.add_car_turn_intent ?? null,
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
