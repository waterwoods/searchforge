/**
 * Customer Start Claim entry / Home navigation helpers (pure + thin wx wrappers).
 *
 * P26D Home routing contract:
 * - Active case/token → Home lands on Task Home (via Entry bootstrap)
 * - No active case → Home lands on Start Claim
 * - Explicit「开始新报案」→ clear draft resume, then Start Claim
 * - pages[0] remains Start Claim (Build Gate / WeChat capsule Home entry)
 */

import { loadResumeToken, clearResumeToken, clearSubmitIntentId } from "./storage";

export const START_CLAIM_ROUTE = "/pages/start-claim/start-claim";
export const START_CLAIM_SUCCESS_ROUTE = "/pages/start-claim-success/start-claim-success";
export const ENTRY_ROUTE = "/pages/entry/entry";
export const TASK_HOME_ROUTE = "/pages/task-home/task-home";

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
 * the customer on Receipt after Start New Claim.
 * Does not clear anonymous session identity or API config.
 */
export function resetStartClaimDraftState(): void {
  clearResumeToken();
  clearSubmitIntentId();
}

/** True when a resumable active case/token is present in local storage. */
export function hasActiveCustomerCase(): boolean {
  return Boolean(loadResumeToken());
}

/** Start Claim route — used when no active case, or after explicit Start New Claim. */
export function resolveHomeStartClaimUrl(): string {
  return START_CLAIM_ROUTE;
}

/**
 * Home destination for capsule Home / success return with an active case.
 * Entry bootstrap rehydrates Task Home (or Receipt if already submitted).
 */
export function resolveCustomerHomeUrl(): string {
  return hasActiveCustomerCase() ? ENTRY_ROUTE : START_CLAIM_ROUTE;
}

type WxNavigate = {
  reLaunch: (opts: { url: string; fail?: () => void }) => void;
  redirectTo?: (opts: { url: string; fail?: () => void }) => void;
};

function launchUrl(wxLike: WxNavigate, url: string): void {
  wxLike.reLaunch({
    url,
    fail: () => {
      wxLike.redirectTo?.({ url });
    },
  });
}

/**
 * Deterministic Home navigation: active token → Entry/Task Home; else Start Claim.
 * Does not clear resume — preserves One Active Case.
 */
export function reLaunchCustomerHome(wxLike: WxNavigate): void {
  launchUrl(wxLike, resolveCustomerHomeUrl());
}

/**
 * Explicit「开始新报案」: clear draft resume, then open Start Claim form.
 * Prefer reLaunch so restored stacks cannot return to a stale Receipt.
 */
export function reLaunchStartClaimHome(wxLike: WxNavigate): void {
  resetStartClaimDraftState();
  launchUrl(wxLike, resolveHomeStartClaimUrl());
}

/**
 * Capsule Home opens pages[0] (Start Claim). If an active case exists, redirect
 * to Entry before the form clears resume — Task Home becomes operational home.
 * Returns true when a redirect was started (caller must not reset draft).
 */
export function redirectStartClaimIfActiveCase(wxLike: WxNavigate): boolean {
  if (!hasActiveCustomerCase()) return false;
  launchUrl(wxLike, ENTRY_ROUTE);
  return true;
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
