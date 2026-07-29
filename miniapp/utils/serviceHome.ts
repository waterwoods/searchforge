/**
 * P29 lightweight Service Home — pure view-model (no wx).
 *
 * Product entrance (Home ≠ Task Home). One Active Case:
 * Continue is the only primary CTA when a resume token exists;
 * Start New Claim is demoted and never silently opens a second case.
 */

export const SERVICE_HOME_ROUTE = "/pages/service-home/service-home";

export const CONTINUE_CLAIM_TITLE = "继续办理当前报案";
export const VIEW_PROGRESS_LABEL = "查看我的报案";
export const CONTACT_BROKER_LABEL = "联系陈总";
export const START_NEW_CLAIM_LABEL = "开始新的报案";
export const START_CLAIM_PRIMARY_TITLE = "开始报案";
export const START_CLAIM_PRIMARY_HINT = "告诉陈总发生了什么，我们帮您记下";

export type ServiceHomeViewModel = {
  brandTitle: string;
  greetingLead: string;
  question: string;
  hasActiveSession: boolean;
  continueTitle: string;
  viewProgressLabel: string;
  contactLabel: string;
  startNewClaimLabel: string;
  startClaimTitle: string;
  startClaimHint: string;
};

export function buildServiceHomeViewModel(
  hasActiveSession: boolean,
  options?: { brandTitle?: string; brokerName?: string },
): ServiceHomeViewModel {
  const brandTitle =
    String(options?.brandTitle || "陈总保险办公室").trim() || "陈总保险办公室";
  void options?.brokerName;

  return {
    brandTitle,
    greetingLead: "您好，",
    question: "今天怎么了？我们在。",
    hasActiveSession: Boolean(hasActiveSession),
    continueTitle: CONTINUE_CLAIM_TITLE,
    viewProgressLabel: VIEW_PROGRESS_LABEL,
    contactLabel: CONTACT_BROKER_LABEL,
    startNewClaimLabel: START_NEW_CLAIM_LABEL,
    startClaimTitle: START_CLAIM_PRIMARY_TITLE,
    startClaimHint: START_CLAIM_PRIMARY_HINT,
  };
}
