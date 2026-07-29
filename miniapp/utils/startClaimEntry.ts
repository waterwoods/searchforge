/**
 * Customer Start Claim entry / Home navigation helpers (pure + thin wx wrappers).
 *
 * Home routing contract (P29 Service Home):
 * - Operational Home → Service Home (product entrance; Home ≠ Task Home)
 * - Server Customer Context → Continue on Service Home → Entry → Task Home
 * - No active case → Start Claim from Service Home (?entry=form)
 * - Explicit「开始新的报案」with active case → One Active Case policy (never wipe resume)
 * - pages[0] remains Start Claim (Build Gate / WeChat capsule Home entry)
 */

import { clearResumeToken, clearSubmitIntentId } from "./storage";
import { SERVICE_HOME_ROUTE } from "./serviceHome";
import { isIntentionalStartClaimEntry } from "./demoInviteLaunch";

export const START_CLAIM_ROUTE = "/pages/start-claim/start-claim";
export const START_CLAIM_SUCCESS_ROUTE = "/pages/start-claim-success/start-claim-success";
export const ENTRY_ROUTE = "/pages/entry/entry";
export const TASK_HOME_ROUTE = "/pages/task-home/task-home";
export { SERVICE_HOME_ROUTE };

/** Keep Start Claim free of heavy task-view imports (injection / Home path). */
export const START_CLAIM_SAFETY_COPY =
  "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。";

export const START_CLAIM_MISSING_HINT =
  "请先填写：事故经过、事故时间、事故地点、是否受伤";

/** P30 One Active Case — never silently create a second case. */
export const ONE_ACTIVE_CASE_POLICY_TITLE = "您已有一个正在处理的报案";
export const ONE_ACTIVE_CASE_POLICY_CONTINUE = "继续当前报案";
export const ONE_ACTIVE_CASE_POLICY_CONTACT = "联系陈总";
export const ONE_ACTIVE_CASE_POLICY_CONTENT =
  "请先继续当前报案。\n\n如确需新的报案，请联系陈总。";

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
 * the customer on Receipt after an empty-state Start New Claim.
 * Does not clear anonymous session identity or API config.
 * Must not be called while an Active Case token should be preserved.
 */
export function resetStartClaimDraftState(): void {
  clearResumeToken();
  clearSubmitIntentId();
}

/** Intentional Start Claim form entry from Service Home (empty state). */
export function resolveHomeStartClaimUrl(): string {
  return `${START_CLAIM_ROUTE}?entry=form`;
}

/**
 * Operational Home destination — always Service Home.
 * Continue on Service Home routes into Entry → Task Home when a token exists.
 */
export function resolveCustomerHomeUrl(): string {
  return SERVICE_HOME_ROUTE;
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
 * Deterministic Home navigation: always Service Home.
 * Does not clear resume — preserves One Active Case / Golden one-scan.
 */
export function reLaunchCustomerHome(wxLike: WxNavigate): void {
  launchUrl(wxLike, resolveCustomerHomeUrl());
}

/**
 * Empty-state Start Claim form only (no active case).
 * Clears draft markers, then opens the form with entry=form.
 */
export function reLaunchEmptyStartClaimForm(wxLike: WxNavigate): void {
  resetStartClaimDraftState();
  launchUrl(wxLike, resolveHomeStartClaimUrl());
}

/**
 * 「返回首页」from Receipt / success always returns to Service Home. That page
 * performs the server Customer Context read before offering a form or Continue.
 */
export function reLaunchStartClaimHome(wxLike: WxNavigate): void {
  launchUrl(wxLike, SERVICE_HOME_ROUTE);
}

/**
 * Capsule Home opens pages[0] (Start Claim). Operational home is Service Home.
 * - Cold Home without ?entry=form / dit= → Service Home
 * - Explicit ?entry=form or Demo Invite ?dit= must resolve Customer Context;
 *   form renders only when next_action is START_NEW_CLAIM (start-claim page gate).
 */
export function redirectStartClaimIfActiveCase(
  wxLike: WxNavigate,
  options?: Record<string, string | undefined>,
): boolean {
  if (!isIntentionalStartClaimEntry(options)) {
    launchUrl(wxLike, SERVICE_HOME_ROUTE);
    return true;
  }
  return false;
}

/**
 * WXML must keep a visible shell: checking / error / authorized form.
 * Form fields may sit behind formAuthorized only when checking + error paths exist.
 */
export function assertStartClaimWxmlNotBlankable(wxml: string): string[] {
  const failures: string[] = [];
  if (
    !wxml.includes("告诉陈总发生了什么") &&
    !wxml.includes("formTitle") &&
    !wxml.includes("事故经过")
  ) {
    failures.push("missing visible form title/fields");
  }
  if (!wxml.includes("formAuthorized")) {
    failures.push("missing Customer Context formAuthorized gate");
  }
  if (!wxml.includes("contextPhase") && !wxml.includes("正在确认")) {
    failures.push("missing context checking shell");
  }
  if (!wxml.includes("initErrorMessage") && !wxml.includes("errorMessage")) {
    failures.push("missing visible error fallback bindings");
  }
  // Legacy blank-screen footgun: entire form behind pageReady alone.
  if (
    /wx:if\s*=\s*"\{\{\s*pageReady\s*\}\}"[\s\S]{0,80}事故经过/.test(wxml) &&
    !wxml.includes("formAuthorized")
  ) {
    failures.push("required form fields are behind a pageReady-only guard");
  }
  return failures;
}
