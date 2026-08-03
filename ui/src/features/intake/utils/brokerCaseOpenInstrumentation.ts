/**
 * Broker first-open timing is recorded server-side on successful
 * GET /api/inbox/cases/{case_id} (first-wins). The workbench open path must
 * call that detail fetch for Claim / Add-Car lanes.
 *
 * This helper documents the client contract for tests — no client-side
 * PII or page-view spam; the server owns the timestamp.
 */

import { shouldFetchFormalCaseDetail } from './workbenchCaseOpen';

export const BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE = 'broker_workbench' as const;

export type BrokerOpenInstrumentationPlan = {
  /** When true, client must GET formal case detail (triggers server first-open stamp). */
  fetchesFormalCaseDetail: boolean;
  instrumentationSurface: typeof BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE;
  notes: string;
};

export function planBrokerCaseOpenInstrumentation(
  stub: { service_lane?: string | null } | null | undefined,
): BrokerOpenInstrumentationPlan {
  const fetches = shouldFetchFormalCaseDetail(stub);
  return {
    fetchesFormalCaseDetail: fetches,
    instrumentationSurface: BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE,
    notes: fetches
      ? 'Server records broker_first_opened on successful GET /api/inbox/cases/{id} once.'
      : 'Holding/WeCom list row skips formal detail fetch; broker_first_opened is not stamped.',
  };
}
