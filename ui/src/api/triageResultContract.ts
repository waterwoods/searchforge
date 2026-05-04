/**
 * Frontend-only contract grouping for POST /api/inbox/triage (TriageResult).
 * Does not change runtime behavior; use for typing and to prefer CORE fields in new UI.
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
