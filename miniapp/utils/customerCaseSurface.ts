/**
 * D-014 Commit 1 — Customer case surface routing (Action Needed vs Waiting Broker).
 *
 * Pure helpers: Entry / Continue / post-submit navigation share one decision.
 * No new API; reuses Constitution + Slice1 waiting signals already on the task.
 */

import type { CustomerTask } from "../types/task";
import { isSubmitted } from "./taskMapping";
import { mapSlice1CustomerView } from "./slice1Customer";
import { resolveCustomerTaskCardsFromTask } from "./resolveCustomerTaskCards";

export const TASK_HOME_ROUTE = "/pages/task-home/task-home";
export const CASE_STATUS_ROUTE = "/pages/case-status/case-status";
export const RECEIPT_ROUTE = "/pages/receipt/receipt";

/** Retired as primary Waiting copy — Case Status never surfaces this as the title. */
export const LEGACY_WAIT_TODAY = "先不用操作";

/** Demo Polish Sprint 2 — Waiting Broker Case Status title (durable confirmation). */
export const CASE_STATUS_TITLE = "资料已收到，等待陈总审核";

/** In-page Request More submit receipt (not toast-only). */
export const SUBMIT_RECEIPT_COPY = "补充资料已收到，陈总会继续审核。";

/** Secondary Waiting action — append-only; never reopens satisfied Request More items. */
export const VOLUNTARY_SUPPLEMENT_LABEL = "继续补充资料";

export const CASE_STATUS_BODY_LINES = [
  "资料已收到，等待陈总审核。",
  "您这边暂时没有需要完成的事项。",
  "如需继续补充，可添加照片或说明（不会覆盖已提交的必填资料）。",
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
 */
export function customerOwesWork(task?: CustomerTask | null): boolean {
  if (!task) return false;
  const view = mapSlice1CustomerView(task);
  if (view.waitingForBroker) return false;
  if (
    view.currentStage === "waiting_broker" ||
    view.currentStage === "waiting"
  ) {
    return false;
  }
  if (view.primaryActionable) return true;
  const cards = resolveCustomerTaskCardsFromTask(task);
  if (cards.some((row) => row.actionable)) return true;
  const today = String(view.constitutionToday || "").trim();
  if (today && today !== LEGACY_WAIT_TODAY) {
    if (view.currentStage === "customer_action_needed") return true;
    if (view.enabled && view.nextAction) {
      const actionType = String(view.nextAction.action_type || "").trim();
      if (actionType === "provide_fact" || actionType === "provide_evidence") {
        return true;
      }
    }
  }
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
    "您这边暂时没有需要完成的事项";
  const after =
    String(view.constitutionAfter || "").trim() ||
    "如需补充，陈总会再联系您";

  return {
    title: CASE_STATUS_TITLE,
    bodyLines: [...CASE_STATUS_BODY_LINES],
    why: why === LEGACY_WAIT_TODAY ? "您这边暂时没有需要完成的事项" : why,
    after: after === "请等待确认。" ? "如需补充，陈总会再联系您" : after,
    statusLabel: "审核中",
    lastSubmittedLines,
    completedLines,
    careLine: String(view.careLine || "").trim() || "下一步由陈总审核",
    careNote: String(view.careNote || "").trim() || "有进展时我们会联系您",
  };
}
