/**
 * Slice 1 customer projection helpers — pure, testable, server-authoritative.
 */
import type {
  CustomerTask,
  Slice1CustomerNextAction,
  Slice1Projection,
  Slice1RequestItem,
  Slice1RequestItemType,
  Slice1RequestProgress,
} from "../types/task";
import { resolveCustomerConstitutionFromTask } from "./resolveCustomerConstitution";

export const REQUEST_ITEM_ROUTE = "/pages/request-item/request-item";

export type Slice1CustomerView = {
  enabled: boolean;
  legacyFallback: boolean;
  workflowState: string;
  aggregateVersion: number;
  nextAction: Slice1CustomerNextAction | null;
  primaryActionable: boolean;
  primaryCtaLabel: string;
  primaryRoute: string;
  queuedItems: Slice1RequestItem[];
  satisfiedItems: Slice1RequestItem[];
  progress: Slice1RequestProgress;
  brokerStatus: string;
  lastServerUpdate: string;
  waitingForBroker: boolean;
  openRequestId: string;
  /** P24D2.1 — resolved Constitution Focus fields (server-first). */
  constitutionToday: string;
  constitutionWhy: string;
  constitutionAfter: string;
  careLine: string;
  careNote: string;
  currentStage: string;
};

export const EMPTY_SLICE1_PROGRESS: Slice1RequestProgress = {
  satisfied: 0,
  total: 0,
  remaining: 0,
};

export const EMPTY_SLICE1_VIEW: Slice1CustomerView = {
  enabled: false,
  legacyFallback: true,
  workflowState: "",
  aggregateVersion: 0,
  nextAction: null,
  primaryActionable: false,
  primaryCtaLabel: "",
  primaryRoute: "",
  queuedItems: [],
  satisfiedItems: [],
  progress: { ...EMPTY_SLICE1_PROGRESS },
  brokerStatus: "",
  lastServerUpdate: "",
  waitingForBroker: false,
  openRequestId: "",
  constitutionToday: "",
  constitutionWhy: "",
  constitutionAfter: "",
  careLine: "",
  careNote: "",
  currentStage: "",
};

const EVIDENCE_TYPES = new Set(["photo_evidence", "policy_or_insurance_card"]);
const TEXT_TYPES = new Set(["vin", "free_text"]);

export function extractSlice1Projection(task?: CustomerTask | null): Slice1Projection | null {
  if (!task) return null;
  if (task.slice1_projection && typeof task.slice1_projection === "object") {
    return task.slice1_projection;
  }
  const v1 = task.task_contract_v1;
  if (v1 && v1.contract_version === "1") {
    return {
      case_id: task.case_id,
      workflow_state: String(v1.workflow_state || ""),
      aggregate_version: Number(v1.aggregate_version || 0),
      customer_next_action: v1.next_action || null,
      queued_request_items: v1.queued_request_items || [],
      request_progress: v1.request_progress,
      server_timestamp: v1.server_timestamp,
      open_request: null,
      broker_next_action: null,
    };
  }
  return null;
}

export function isSlice1CustomerFlow(task?: CustomerTask | null): boolean {
  return extractSlice1Projection(task) != null;
}

export function isEvidenceItemType(itemType?: string | null): boolean {
  return EVIDENCE_TYPES.has(String(itemType || "").trim().toLowerCase());
}

export function isTextItemType(itemType?: string | null): boolean {
  return TEXT_TYPES.has(String(itemType || "").trim().toLowerCase());
}

export function normalizeVin(value: string): string {
  return String(value || "")
    .trim()
    .toUpperCase()
    .replace(/[^A-HJ-NPR-Z0-9]/g, "");
}

export function validateVin(value: string): { ok: boolean; message: string; normalized: string } {
  const normalized = normalizeVin(value);
  if (!normalized) {
    return { ok: false, message: "请填写车辆 VIN", normalized };
  }
  if (normalized.length !== 17) {
    return { ok: false, message: "VIN 应为 17 位（不含 I/O/Q）", normalized };
  }
  if (/[IOQ]/.test(normalized)) {
    return { ok: false, message: "VIN 不能包含字母 I、O、Q", normalized };
  }
  return { ok: true, message: "", normalized };
}

export function validateFreeText(value: string): { ok: boolean; message: string; normalized: string } {
  const normalized = String(value || "").trim();
  if (!normalized) {
    return { ok: false, message: "请填写陈总需要的说明", normalized };
  }
  if (normalized.length > 2000) {
    return { ok: false, message: "内容过长，请控制在 2000 字以内", normalized };
  }
  return { ok: true, message: "", normalized };
}

export function factFieldForItemType(itemType: Slice1RequestItemType): string {
  const key = String(itemType || "").trim().toLowerCase();
  if (key === "vin") return "vin";
  return "free_text";
}

function normalizeItem(raw: unknown): Slice1RequestItem | null {
  if (!raw || typeof raw !== "object") return null;
  const item = raw as Partial<Slice1RequestItem>;
  const requestItemId = String(item.request_item_id || "").trim();
  if (!requestItemId) return null;
  return {
    request_item_id: requestItemId,
    request_id: String(item.request_id || "").trim(),
    item_type: String(item.item_type || "").trim() || "free_text",
    label: String(item.label || "待补充资料").trim() || "待补充资料",
    instructions: String(item.instructions || "").trim(),
    required: item.required !== false,
    position: Number(item.position || 0),
    status: String(item.status || "").trim() || "queued",
    actionable: Boolean(item.actionable) && String(item.status || "") === "active",
    created_at: item.created_at,
    satisfied_at: item.satisfied_at ?? null,
    satisfied_by_event_id: item.satisfied_by_event_id ?? null,
  };
}

function primaryCtaForAction(action: Slice1CustomerNextAction | null): {
  actionable: boolean;
  label: string;
  route: string;
} {
  if (!action) {
    return { actionable: false, label: "", route: "" };
  }
  const type = String(action.action_type || "").trim();
  if (type === "provide_fact" || type === "provide_evidence") {
    return {
      actionable: true,
      label: String(action.title || "补充陈总需要的资料").trim() || "补充陈总需要的资料",
      route: REQUEST_ITEM_ROUTE,
    };
  }
  if (type === "wait_for_broker_review") {
    return {
      actionable: false,
      label: "资料已提交，等待经纪人审核",
      route: "",
    };
  }
  return {
    actionable: false,
    label: String(action.title || "请联系陈总").trim() || "请联系陈总",
    route: "",
  };
}

function constitutionFieldsFromTask(task?: CustomerTask | null) {
  const resolved = resolveCustomerConstitutionFromTask(task);
  return {
    constitutionToday: resolved.today,
    constitutionWhy: resolved.why,
    constitutionAfter: resolved.after,
    careLine: resolved.careLine,
    careNote: resolved.careNote,
    currentStage: resolved.currentStage,
  };
}

export function mapSlice1CustomerView(task?: CustomerTask | null): Slice1CustomerView {
  const projection = extractSlice1Projection(task);
  if (!projection) {
    return {
      ...EMPTY_SLICE1_VIEW,
      ...constitutionFieldsFromTask(task),
    };
  }

  const nextAction = projection.customer_next_action || null;
  const open = projection.open_request;
  const allItems = (open?.items || [])
    .map(normalizeItem)
    .filter(Boolean) as Slice1RequestItem[];
  const queuedFromOpen = (open?.queued_items || projection.queued_request_items || [])
    .map(normalizeItem)
    .filter(Boolean) as Slice1RequestItem[];
  const queuedItems = queuedFromOpen.length
    ? queuedFromOpen.map((item) => ({ ...item, actionable: false }))
    : allItems
        .filter((item) => item.status === "queued")
        .map((item) => ({ ...item, actionable: false }));
  const satisfiedItems = allItems.filter((item) => item.status === "satisfied");
  const progress = projection.request_progress || open?.progress || {
    satisfied: satisfiedItems.length,
    total: Math.max(allItems.length, queuedItems.length + satisfiedItems.length + (nextAction?.request_item_id ? 1 : 0)),
    remaining: queuedItems.length + (nextAction?.request_item_id ? 1 : 0),
  };
  const cta = primaryCtaForAction(nextAction);
  const constitution = constitutionFieldsFromTask(task);
  const waitingFromStage = constitution.currentStage === "waiting_broker";
  const waitingFromAction = String(nextAction?.action_type || "") === "wait_for_broker_review";
  const waitingForBroker = waitingFromStage || waitingFromAction;

  // Overlay Constitution Today/Why onto display next-action (Slice1 SSOT on task unchanged).
  let displayNextAction = nextAction;
  if (nextAction && (constitution.constitutionToday || constitution.constitutionWhy)) {
    displayNextAction = {
      ...nextAction,
      title: constitution.constitutionToday || nextAction.title,
      instructions: constitution.constitutionWhy || nextAction.instructions,
    };
  }

  // Actionable CTA prefers Constitution Today; waiting keeps Cap3B wait label.
  const primaryCtaLabel =
    !waitingForBroker && constitution.constitutionToday
      ? constitution.constitutionToday
      : cta.label;

  return {
    enabled: true,
    legacyFallback: false,
    workflowState: String(projection.workflow_state || ""),
    aggregateVersion: Number(projection.aggregate_version || 0),
    nextAction: displayNextAction,
    primaryActionable: waitingForBroker ? false : cta.actionable,
    primaryCtaLabel,
    primaryRoute: waitingForBroker ? "" : cta.route,
    queuedItems,
    satisfiedItems,
    progress: {
      satisfied: Number(progress.satisfied || 0),
      total: Math.max(Number(progress.total || 0), 0),
      remaining: Number(progress.remaining || 0),
    },
    brokerStatus: String(projection.broker_next_action?.status || projection.broker_next_action?.action_type || ""),
    lastServerUpdate: String(projection.server_timestamp || nextAction?.last_updated_at || ""),
    waitingForBroker,
    openRequestId: String(open?.request_id || nextAction?.request_id || ""),
    ...constitution,
  };
}

export function applySlice1ProjectionToTask(
  task: CustomerTask,
  projection?: Slice1Projection | null,
): CustomerTask {
  if (!projection) return task;
  return {
    ...task,
    slice1_projection: projection,
    task_contract_v1: {
      contract_version: "1",
      task_id: task.task_contract_v1?.task_id || task.task_contract?.task_id || task.case_id,
      task_type: "claim_request_more",
      workflow_state: projection.workflow_state,
      aggregate_version: projection.aggregate_version,
      next_action: projection.customer_next_action || null,
      queued_request_items: projection.queued_request_items || [],
      request_progress: projection.request_progress,
      server_timestamp: projection.server_timestamp,
    },
  };
}

export const slice1Customer = {
  extractSlice1Projection,
  isSlice1CustomerFlow,
  isEvidenceItemType,
  isTextItemType,
  normalizeVin,
  validateVin,
  validateFreeText,
  factFieldForItemType,
  mapSlice1CustomerView,
  applySlice1ProjectionToTask,
  REQUEST_ITEM_ROUTE,
};
