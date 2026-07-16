/**
 * Customer Start Claim entry / Home navigation helpers (pure + thin wx wrappers).
 *
 * Keeps Home → Start Claim deterministic after Receipt / success / restored sessions.
 */

import { clearResumeToken, clearSubmitIntentId } from "./storage";

export const START_CLAIM_ROUTE = "/pages/start-claim/start-claim";
export const START_CLAIM_SUCCESS_ROUTE = "/pages/start-claim-success/start-claim-success";

/** Keep Start Claim free of heavy task-view imports (injection / Home path). */
export const START_CLAIM_SAFETY_COPY =
  "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。";

export const START_CLAIM_MISSING_HINT =
  "请先填写：事故经过、事故时间、事故地点、是否受伤";

/** Empty form shell — always safe to bind; never depends on network. */
export type StartClaimShellState = {
  description: string;
  charCount: number;
  accidentDatetime: string;
  accidentLocation: string;
  injuryStatus: string;
  canSubmit: boolean;
  missingHint: string;
  fieldErrors: Record<string, string>;
  errorMessage: string;
  errorRetryable: boolean;
  pageReady: boolean;
  initErrorMessage: string;
};

export function createEmptyStartClaimShell(missingHint: string): StartClaimShellState {
  return {
    description: "",
    charCount: 0,
    accidentDatetime: "",
    accidentLocation: "",
    injuryStatus: "",
    canSubmit: false,
    missingHint,
    fieldErrors: {},
    errorMessage: "",
    errorRetryable: false,
    pageReady: true,
    initErrorMessage: "",
  };
}

/**
 * Reset only claim-draft resume markers so a prior submitted task cannot strand
 * the customer on Receipt after Home / Start New Claim.
 * Does not clear anonymous session identity or API config.
 */
export function resetStartClaimDraftState(): void {
  clearResumeToken();
  clearSubmitIntentId();
}

/** Home / Start New Claim must always target the customer entry form. */
export function resolveHomeStartClaimUrl(): string {
  return START_CLAIM_ROUTE;
}

/**
 * Deterministic Home navigation used by success/result pages.
 * Prefer reLaunch so restored stacks cannot return to a stale Receipt.
 */
export function reLaunchStartClaimHome(wxLike: {
  reLaunch: (opts: { url: string; fail?: () => void }) => void;
  redirectTo?: (opts: { url: string }) => void;
}): void {
  resetStartClaimDraftState();
  const url = resolveHomeStartClaimUrl();
  wxLike.reLaunch({
    url,
    fail: () => {
      wxLike.redirectTo?.({ url });
    },
  });
}

/** WXML must never be able to hide the entire form shell. */
export function assertStartClaimWxmlNotBlankable(wxml: string): string[] {
  const failures: string[] = [];
  if (!wxml.includes("告诉陈总发生了什么") && !wxml.includes("事故经过")) {
    failures.push("missing visible form title/fields");
  }
  // Entire-page readiness gates that default false are a blank-screen footgun.
  if (/wx:if\s*=\s*"\{\{\s*pageReady\s*\}\}"/.test(wxml) && !wxml.includes("initErrorMessage")) {
    // pageReady may wrap extras, but the form card itself must not be solely behind it.
  }
  const formCardGuarded =
    /wx:if\s*=\s*"\{\{\s*(ready|pageReady|initialized|showForm)\s*\}\}"[\s\S]{0,80}事故经过/.test(
      wxml,
    ) ||
    /事故经过[\s\S]{0,40}wx:if\s*=\s*"\{\{\s*(ready|pageReady|initialized|showForm)\s*\}\}"/.test(
      wxml,
    );
  if (formCardGuarded) {
    failures.push("required form fields are behind a readiness wx:if guard");
  }
  if (!wxml.includes("initErrorMessage") && !wxml.includes("errorMessage")) {
    failures.push("missing visible error fallback bindings");
  }
  return failures;
}
