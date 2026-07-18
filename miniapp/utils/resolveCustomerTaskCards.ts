/**
 * P26A — Constitution-first Customer Task Cards.
 *
 * Authority: constitution_projection.customer.tasks only.
 * Pages must not invent a hard-coded task list.
 */

import type { CustomerTask } from "../types/task";
import {
  REQUEST_ITEM_ROUTE,
  mapSlice1CustomerView,
} from "./slice1Customer";
import {
  resolveCustomerConstitutionFromTask,
  type CustomerConstitutionProjection,
} from "./resolveCustomerConstitution";

export type CustomerTaskCardState =
  | "pending"
  | "in_progress"
  | "completed"
  | "waiting_broker"
  | "blocked";

export type CustomerTaskCardRoute = "request_item" | "photos" | "story" | "";

export type ConstitutionTaskCard = {
  task_id?: string | null;
  title?: string | null;
  state?: string | null;
  progress?: { completed?: number | null; total?: number | null } | null;
  is_today?: boolean | null;
  route?: string | null;
  actionable?: boolean | null;
  primary_action?: string | null;
};

export type CustomerTaskCardView = {
  taskId: string;
  title: string;
  state: CustomerTaskCardState;
  stateLabel: string;
  progressCompleted: number;
  progressTotal: number;
  progressText: string;
  isToday: boolean;
  actionable: boolean;
  primaryAction: string;
  route: string;
  completionMark: string;
};

const STATE_LABELS: Record<CustomerTaskCardState, string> = {
  pending: "待处理",
  in_progress: "进行中",
  completed: "已完成",
  waiting_broker: "等待审核",
  blocked: "稍后处理",
};

const ROUTE_MAP: Record<string, string> = {
  request_item: REQUEST_ITEM_ROUTE,
  photos: "/pages/photos/photos",
  story: "/pages/story/story",
};

function nonEmpty(value: unknown): string {
  return String(value || "").trim();
}

function normalizeState(raw: unknown): CustomerTaskCardState {
  const state = nonEmpty(raw).toLowerCase();
  if (
    state === "pending" ||
    state === "in_progress" ||
    state === "completed" ||
    state === "waiting_broker" ||
    state === "blocked"
  ) {
    return state;
  }
  return "pending";
}

function extractTasks(
  customer: CustomerConstitutionProjection | null | undefined,
): ConstitutionTaskCard[] {
  if (!customer || typeof customer !== "object") return [];
  const tasks = (customer as CustomerConstitutionProjection & {
    tasks?: ConstitutionTaskCard[] | null;
  }).tasks;
  if (!Array.isArray(tasks)) return [];
  return tasks.filter((row) => row && typeof row === "object");
}

export function mapConstitutionTaskCard(raw: ConstitutionTaskCard): CustomerTaskCardView | null {
  const taskId = nonEmpty(raw.task_id);
  const title = nonEmpty(raw.title);
  if (!taskId || !title) return null;

  const state = normalizeState(raw.state);
  const completed = Math.max(0, Number(raw.progress?.completed || 0));
  const total = Math.max(1, Number(raw.progress?.total || 1));
  const routeKey = nonEmpty(raw.route).toLowerCase();
  const actionable = Boolean(raw.actionable) && Boolean(ROUTE_MAP[routeKey]);
  const progressText =
    state === "completed" || state === "waiting_broker"
      ? "已完成"
      : `${Math.min(completed, total)}/${total}`;

  return {
    taskId,
    title,
    state,
    stateLabel: STATE_LABELS[state],
    progressCompleted: completed,
    progressTotal: total,
    progressText,
    isToday: Boolean(raw.is_today),
    actionable,
    primaryAction: nonEmpty(raw.primary_action),
    route: actionable ? ROUTE_MAP[routeKey] || "" : "",
    completionMark:
      state === "completed" || state === "waiting_broker" ? "✓" : state === "blocked" ? "·" : "○",
  };
}

/**
 * Resolve visible Task Cards from server Constitution only.
 * Empty list when projection has no tasks — never invent a client checklist.
 */
export function resolveCustomerTaskCardsFromTask(
  task: CustomerTask | null | undefined,
): CustomerTaskCardView[] {
  if (!task) return [];
  const resolved = resolveCustomerConstitutionFromTask(task);
  const serverCustomer = task.constitution_projection?.customer || null;
  const tasks = extractTasks(serverCustomer);
  // Server tasks are authoritative. If absent, do not hard-code a fallback list.
  void resolved;
  return tasks.map(mapConstitutionTaskCard).filter(Boolean) as CustomerTaskCardView[];
}

export function primaryTaskRouteFromCards(cards: CustomerTaskCardView[]): string {
  const today = cards.find((card) => card.isToday && card.actionable && card.route);
  if (today) return today.route;
  const first = cards.find((card) => card.actionable && card.route);
  return first?.route || "";
}

/** Prefer Constitution card route; fall back to Slice1 request-item for insurance. */
export function resolveTaskHomePrimaryRoute(task: CustomerTask | null | undefined): string {
  const cards = resolveCustomerTaskCardsFromTask(task);
  const fromCards = primaryTaskRouteFromCards(cards);
  if (fromCards) return fromCards;
  const slice1 = mapSlice1CustomerView(task);
  if (slice1.primaryActionable && slice1.primaryRoute) {
    return slice1.primaryRoute;
  }
  return "";
}
