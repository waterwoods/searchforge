import { isWeComMediaIntakeLane } from './attachmentDisplay';

export const FORMAL_CASE_OPEN_ERROR = 'Could not open case';
export const INTAKE_ITEM_OPEN_ERROR = 'Could not open intake item';

type CaseLaneStub = { service_lane?: string | null } | null | undefined;

/** Unassigned WeCom media rows render from list payload; skip formal case detail fetch. */
export function shouldFetchFormalCaseDetail(stub: CaseLaneStub): boolean {
  if (!stub) return true;
  return !isWeComMediaIntakeLane(stub.service_lane);
}

/** User-facing open failure copy — holding intake is not a formal case. */
export function resolveCaseOpenErrorMessage(stub: CaseLaneStub): string {
  if (stub && isWeComMediaIntakeLane(stub.service_lane)) {
    return INTAKE_ITEM_OPEN_ERROR;
  }
  return FORMAL_CASE_OPEN_ERROR;
}

/**
 * When list-row fallback is enough (WeCom holding lane), a failed detail fetch must not
 * show the formal case error toast.
 */
export function shouldShowCaseOpenFailureToast(
  stub: CaseLaneStub,
  detailFetchFailed: boolean,
): boolean {
  if (!detailFetchFailed) return false;
  if (stub && isWeComMediaIntakeLane(stub.service_lane)) return false;
  return true;
}

/** P19H-3f-1c — raw inbound lanes are excluded from broker business queue. */
export function isBrokerBusinessQueueLane(serviceLane?: string | null): boolean {
  return !isWeComMediaIntakeLane(serviceLane);
}
