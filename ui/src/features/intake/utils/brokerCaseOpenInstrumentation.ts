/**
 * Broker first-open timing is recorded by a dedicated idempotent POST after a
 * successful Workbench case-detail/Brief render — never by generic GET.
 */

import { shouldFetchFormalCaseDetail } from './workbenchCaseOpen';

export const BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE = 'broker_workbench' as const;
export const BROKER_FIRST_OPEN_ACTIVITY_PATH =
  '/api/inbox/cases/{case_id}/activity/broker-first-opened' as const;

export type BrokerOpenInstrumentationPlan = {
  /** When true, client must GET formal case detail then POST activity stamp. */
  fetchesFormalCaseDetail: boolean;
  postsBrokerFirstOpenedActivity: boolean;
  instrumentationSurface: typeof BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE;
  notes: string;
};

export function planBrokerCaseOpenInstrumentation(
  stub: { service_lane?: string | null } | null | undefined,
): BrokerOpenInstrumentationPlan {
  const fetches = shouldFetchFormalCaseDetail(stub);
  return {
    fetchesFormalCaseDetail: fetches,
    postsBrokerFirstOpenedActivity: fetches,
    instrumentationSurface: BROKER_FIRST_OPEN_INSTRUMENTATION_SURFACE,
    notes: fetches
      ? 'After successful Workbench detail render, POST activity/broker-first-opened once (server first-wins). Generic GET never stamps.'
      : 'Holding/WeCom list row skips formal detail fetch; broker_first_opened is not stamped.',
  };
}

/** Fire-and-forget helper used after successful detail load; never throws to UI. */
export async function notifyBrokerCaseDetailRendered(
  caseId: string,
  recordFn: (id: string) => Promise<unknown>,
): Promise<void> {
  const cid = (caseId || '').trim();
  if (!cid) return;
  try {
    await recordFn(cid);
  } catch {
    // Observational only — never block Workbench.
  }
}
