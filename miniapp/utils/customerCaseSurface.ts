/**
 * D-014 Commit 1 — Customer case surface routing (Action Needed vs Waiting Broker).
 *
 * Pure helpers: Entry / Continue / post-submit navigation share one decision.
 * No new API; reuses Constitution + Slice1 waiting signals already on the task.
 */

import type { CustomerTask } from "../types/task";
import { isSubmitted } from "./taskMapping";
import { mapSlice1CustomerView } from "./slice1Customer";
import {
  resolveCustomerTaskCardsFromTask,
  resolveTaskHomePrimaryRoute,
} from "./resolveCustomerTaskCards";

export const TASK_HOME_ROUTE = "/pages/task-home/task-home";
export const CASE_STATUS_ROUTE = "/pages/case-status/case-status";
export const RECEIPT_ROUTE = "/pages/receipt/receipt";

/** Retired as primary Waiting copy — Case Status never surfaces this as the title. */
export const LEGACY_WAIT_TODAY = "先不用操作";

/** Waiting Broker Case Status title — office voice, not underwriting. */
export const CASE_STATUS_TITLE = "已收到，陈总正在看";

/** In-page Request More submit receipt when customer is truly waiting (not toast-only). */
export const SUBMIT_RECEIPT_COPY = "补充已收到，陈总会继续看。";

/**
 * Soften institutional waiting vocabulary for customer display only.
 * Does not change routing or Constitution authority — presentation polish.
 */
export function softenOfficeWaitingVoice(text: string): string {
  let t = String(text || "").trim();
  if (!t) return t;
  t = t.replace(/资料已提交，等待陈总审核/g, "已提交，陈总正在看");
  t = t.replace(/资料已收到，等待陈总审核/g, "已收到，陈总正在看");
  t = t.replace(/等待陈总审核/g, "陈总正在看");
  t = t.replace(/陈总会继续审核/g, "陈总会继续看");
  t = t.replace(/陈总正在审核中/g, "陈总正在看");
  t = t.replace(/陈总正在审核/g, "陈总正在看");
  t = t.replace(/陈总开始审核/g, "陈总会尽快联系您");
  t = t.replace(/下一步由陈总审核/g, "下一步由陈总联系您");
  t = t.replace(/完成后由陈总审核/g, "完成后陈总会联系您");
  t = t.replace(/提交给陈总审核/g, "交给陈总");
  t = t.replace(/审核中/g, "陈总正在看");
  return t;
}

/** Pause mid-task — must not read as “case closed.” */
export const DEFER_LATER_LABEL = "先离开，稍后再继续";

/** Shared hub name — Task Home / return paths. */
export const HUB_NAME = "我的报案";
export const HUB_RETURN_LABEL = "返回我的报案";
export const HUB_VIEW_LABEL = "查看我的报案";

/** Secondary Waiting action — append-only; never reopens satisfied Request More items. */
export const VOLUNTARY_SUPPLEMENT_LABEL = "继续补充资料";

/**
 * Post-submit receipt: never say “审核中 / 等待” when the customer still owes Today work.
 */
export function buildSubmitReceiptCopy(task?: CustomerTask | null): string {
  if (!customerOwesWork(task)) {
    return SUBMIT_RECEIPT_COPY;
  }
  const view = mapSlice1CustomerView(task);
  const today = String(view.constitutionToday || "").trim();
  if (today && today !== LEGACY_WAIT_TODAY) {
    return `已收到。下一步：${today}`;
  }
  const nextTitle = String(view.nextAction?.title || view.primaryCtaLabel || "").trim();
  if (nextTitle) {
    return `已收到。下一步：${nextTitle}`;
  }
  return "已收到。请继续完成下一步。";
}

export const CASE_STATUS_BODY_LINES = [
  "已收到，陈总正在看。",
  "您这边先不用操作。",
  "如需补充照片或说明，也可以继续添加。",
] as const;

export type CustomerCaseSurface = "receipt" | "task_home" | "case_status";

export type CaseStatusViewModel = {
  title: string;
  bodyLines: string[];
  why: string;
  after: string;
  statusLabel: string;
  lastSubmittedLines: string[];
  completedLines: string[];
  careLine: string;
  careNote: string;
};

/**
 * True when the customer still owes actionable work (Today / open Request More).
 * Waiting Broker is explicitly not “owes work.”
 *
 * Actionable cards and a concrete non-wait Today win over stale waiting stage
 * signals — never celebrate Waiting while the next default task remains open.
 */
export function customerOwesWork(task?: CustomerTask | null): boolean {
  if (!task) return false;
  const view = mapSlice1CustomerView(task);
  const cards = resolveCustomerTaskCardsFromTask(task);
  if (cards.some((row) => row.actionable)) return true;
  const today = String(view.constitutionToday || "").trim();
  if (today && today !== LEGACY_WAIT_TODAY) {
    if (view.primaryActionable) return true;
    if (view.currentStage === "customer_action_needed") return true;
    if (view.enabled && view.nextAction) {
      const actionType = String(view.nextAction.action_type || "").trim();
      if (actionType === "provide_fact" || actionType === "provide_evidence") {
        return true;
      }
    }
    // Concrete Today (e.g. 补充照片) means work remains even if stage drifted.
    if (view.currentStage !== "waiting_broker") return true;
  }
  if (view.waitingForBroker) return false;
  if (
    view.currentStage === "waiting_broker" ||
    view.currentStage === "waiting"
  ) {
    return false;
  }
  if (view.primaryActionable) return true;
  // Legacy non-Slice1 in-progress claim: keep Task Home until submitted.
  if (!view.enabled && !isSubmitted(task)) {
    return true;
  }
  return false;
}

export function isWaitingBrokerSurface(task?: CustomerTask | null): boolean {
  if (!task || isSubmitted(task)) return false;
  return !customerOwesWork(task);
}

/** Closed / History cases stay read-only — no voluntary append. */
export function isCustomerCaseClosedReadOnly(task?: CustomerTask | null): boolean {
  if (!task) return false;
  if (Boolean((task as { case_closed_read_only?: unknown }).case_closed_read_only)) {
    return true;
  }
  const status = String(
    (task as { case_status?: unknown }).case_status || "",
  )
    .trim()
    .toLowerCase();
  if (status === "closed") return true;
  return isSubmitted(task);
}

/**
 * Active Waiting Broker cases always expose voluntary append.
 * Request More (Action Needed) is handled by Task Home routing, not this CTA.
 */
export function canVoluntarySupplement(task?: CustomerTask | null): boolean {
  if (!task) return false;
  if (isCustomerCaseClosedReadOnly(task)) return false;
  return isWaitingBrokerSurface(task);
}

/**
 * Single routing decision for Entry / Continue / safe redirects.
 * Closed/submitted → Receipt (unchanged). Else Action Needed → Task Home; else Case Status.
 */
export function resolveCustomerCaseSurface(task?: CustomerTask | null): CustomerCaseSurface {
  if (!task) return "case_status";
  if (isSubmitted(task)) return "receipt";
  if (customerOwesWork(task)) return "task_home";
  return "case_status";
}

export function resolveCustomerCaseSurfaceRoute(task?: CustomerTask | null): string {
  const surface = resolveCustomerCaseSurface(task);
  if (surface === "receipt") return RECEIPT_ROUTE;
  if (surface === "task_home") return TASK_HOME_ROUTE;
  return CASE_STATUS_ROUTE;
}

/**
 * Post-submit / Continue continuity route.
 * When work remains, go directly to the next unfinished task page.
 * Only when nothing remains → Case Status (Waiting). Never celebrate early.
 */
export function resolveWorkflowContinueRoute(task?: CustomerTask | null): string {
  if (!task) return CASE_STATUS_ROUTE;
  if (isSubmitted(task)) return RECEIPT_ROUTE;
  if (!customerOwesWork(task)) return CASE_STATUS_ROUTE;
  const nextTaskRoute = resolveTaskHomePrimaryRoute(task);
  return nextTaskRoute || TASK_HOME_ROUTE;
}

function formatSubmittedLabel(label: string, when?: string): string {
  const title = String(label || "").trim();
  if (!title) return "";
  const stamp = String(when || "").trim();
  return stamp ? `${title} · ${stamp}` : title;
}

/** Build Case Status presentation from existing task fields only (no invented progress). */
export function buildCaseStatusViewModel(task?: CustomerTask | null): CaseStatusViewModel {
  const view = mapSlice1CustomerView(task);
  const cards = resolveCustomerTaskCardsFromTask(task);
  const completedFromCards = cards
    .filter((row) => row.state === "completed" || row.state === "waiting_broker")
    .map((row) => row.title);
  const satisfied = (view.satisfiedItems || [])
    .map((row) => String(row.label || "").trim())
    .filter(Boolean);
  const received = (task?.dashboard_summary?.received || [])
    .map((row) => String(row || "").trim())
    .filter(Boolean);

  const completedLines = Array.from(
    new Set([...satisfied, ...completedFromCards, ...received].filter(Boolean)),
  );

  const lastSubmittedLines: string[] = [];
  const lastStamp = String(view.lastServerUpdate || "").trim();
  if (satisfied.length) {
    lastSubmittedLines.push(formatSubmittedLabel(satisfied[satisfied.length - 1], lastStamp));
  } else if (completedFromCards.length) {
    lastSubmittedLines.push(
      formatSubmittedLabel(completedFromCards[completedFromCards.length - 1], lastStamp),
    );
  } else if (received.length) {
    lastSubmittedLines.push(formatSubmittedLabel(received[received.length - 1], lastStamp));
  }

  const why =
    String(view.constitutionWhy || "").trim() ||
    "您这边先不用操作";
  const after =
    String(view.constitutionAfter || "").trim() ||
    "如需补充，陈总会再联系您";

  return {
    title: CASE_STATUS_TITLE,
    bodyLines: [...CASE_STATUS_BODY_LINES],
    why: softenOfficeWaitingVoice(
      why === LEGACY_WAIT_TODAY ? "您这边先不用操作" : why,
    ),
    after: softenOfficeWaitingVoice(
      after === "请等待确认。" ? "如需补充，陈总会再联系您" : after,
    ),
    statusLabel: "陈总正在看",
    lastSubmittedLines,
    completedLines,
    careLine: softenOfficeWaitingVoice(
      String(view.careLine || "").trim() || "下一步由陈总联系您",
    ),
    careNote: String(view.careNote || "").trim() || "有进展时我们会联系您",
  };
}
