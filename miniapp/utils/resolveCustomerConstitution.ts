/**
 * P24D2 / P24D2.1 — Server-first Customer Constitution resolver.
 *
 * Authority (field-by-field):
 *   1. Valid fields from constitution_projection.customer (H5 intake)
 *   2. Existing task contract / Slice1-derived fallback
 *   3. Existing local/prototype derivation
 *   4. Safe empty
 *
 * Selection stays here — pages must not scatter server ?? local checks.
 */

import type { CustomerTask, Slice1CustomerNextAction } from "../types/task";

export type CustomerConstitutionTrust = {
  care_line?: string | null;
  care_note?: string | null;
};

/** P26A — Constitution Task Card (server projection; client must not invent lists). */
export type CustomerConstitutionTaskCard = {
  task_id?: string | null;
  title?: string | null;
  state?: string | null;
  progress?: { completed?: number | null; total?: number | null } | null;
  is_today?: boolean | null;
  route?: string | null;
  actionable?: boolean | null;
  primary_action?: string | null;
};

export type CustomerConstitutionProjection = {
  today?: string | null;
  why?: string | null;
  after?: string | null;
  trust?: CustomerConstitutionTrust | null;
  current_stage?: string | null;
  /** P26A — visible Task Cards for Customer Task Home. */
  tasks?: CustomerConstitutionTaskCard[] | null;
};

/** Additive H5/customer API shape (customer slice only). */
export type ConstitutionProjection = {
  projection_version?: number;
  case_id?: string | null;
  current_stage?: string | null;
  customer?: CustomerConstitutionProjection | null;
};

export type LocalCustomerConstitution = {
  today: string;
  why: string;
  after: string;
  careLine: string;
  careNote: string;
  currentStage: string;
};

export type FieldAuthority = "server" | "task_contract" | "local";

export type ResolvedCustomerConstitution = {
  today: string;
  why: string;
  after: string;
  careLine: string;
  careNote: string;
  currentStage: string;
  /** Per-field source for tests / debugging — not shown in UI. */
  fieldAuthority: {
    today: FieldAuthority;
    why: FieldAuthority;
    after: FieldAuthority;
    careLine: FieldAuthority;
    careNote: FieldAuthority;
    currentStage: FieldAuthority;
  };
};

function nonEmpty(value: unknown): string | null {
  if (value == null) return null;
  const text = String(value).trim();
  return text ? text : null;
}

function pickField(
  server: string | null,
  taskContract: string | null,
  local: string,
): { value: string; authority: FieldAuthority } {
  if (server) return { value: server, authority: "server" };
  if (taskContract) return { value: taskContract, authority: "task_contract" };
  return { value: String(local || "").trim(), authority: "local" };
}

export function extractServerCustomerProjection(
  serverProjection: ConstitutionProjection | null | undefined,
): CustomerConstitutionProjection | null {
  if (!serverProjection || typeof serverProjection !== "object") return null;
  const customer = serverProjection.customer;
  if (!customer || typeof customer !== "object") return null;
  return customer;
}

/**
 * Prefer valid server Constitution fields; then task-contract; then local.
 * Blank strings are treated as missing.
 */
export function resolveCustomerConstitution(args: {
  serverProjection?: ConstitutionProjection | null;
  /** Middle tier: task_contract / Slice1-shaped fallback (optional). */
  taskContract?: Partial<LocalCustomerConstitution> | null;
  local: LocalCustomerConstitution;
}): ResolvedCustomerConstitution {
  const local = args.local;
  const mid = args.taskContract || null;
  const serverCustomer = extractServerCustomerProjection(args.serverProjection);
  const serverTrust =
    serverCustomer && serverCustomer.trust && typeof serverCustomer.trust === "object"
      ? serverCustomer.trust
      : null;

  const today = pickField(
    nonEmpty(serverCustomer?.today),
    nonEmpty(mid?.today),
    local.today,
  );
  const why = pickField(nonEmpty(serverCustomer?.why), nonEmpty(mid?.why), local.why);
  const after = pickField(nonEmpty(serverCustomer?.after), nonEmpty(mid?.after), local.after);
  const careLine = pickField(
    nonEmpty(serverTrust?.care_line),
    nonEmpty(mid?.careLine),
    local.careLine,
  );
  const careNote = pickField(
    nonEmpty(serverTrust?.care_note),
    nonEmpty(mid?.careNote),
    local.careNote,
  );
  const currentStage = pickField(
    nonEmpty(serverCustomer?.current_stage) || nonEmpty(args.serverProjection?.current_stage),
    nonEmpty(mid?.currentStage),
    local.currentStage,
  );

  return {
    today: today.value,
    why: why.value,
    after: after.value,
    careLine: careLine.value,
    careNote: careNote.value,
    currentStage: currentStage.value,
    fieldAuthority: {
      today: today.authority,
      why: why.authority,
      after: after.authority,
      careLine: careLine.authority,
      careNote: careNote.authority,
      currentStage: currentStage.authority,
    },
  };
}

/** Map mock profile → local Constitution stage vocabulary (fallback only). */
export function localStageFromMockProfile(profile: {
  customerActionNeeded?: boolean;
  statusLabel?: string;
}): string {
  if (profile.customerActionNeeded) return "customer_action_needed";
  const status = String(profile.statusLabel || "").trim();
  if (status === "已完成") return "waiting";
  if (status === "等待保险公司") return "waiting";
  if (!profile.customerActionNeeded) return "waiting_broker";
  return "waiting";
}

/**
 * Primary CTA from resolved Constitution stage + local profile.
 * While customer owes work: CTA matches Today Focus.
 * Waiting/done: keep acknowledgment CTAs (知道了 / 返回首页).
 */
export function primaryLabelForResolvedConstitution(
  resolved: Pick<ResolvedCustomerConstitution, "today" | "currentStage">,
  profile: { customerActionNeeded?: boolean; statusLabel?: string; nextAction?: string },
  localPrimary: string,
): string {
  const stage = String(resolved.currentStage || "").trim();
  if (stage === "customer_action_needed") {
    return String(resolved.today || "").trim() || localPrimary;
  }
  if (stage === "waiting_broker" || stage === "waiting") {
    if (String(profile.statusLabel || "").trim() === "已完成") {
      return "返回首页";
    }
    if (stage === "waiting_broker") return "知道了";
    return localPrimary || "知道了";
  }
  return localPrimary;
}

function stageFromSlice1Action(actionType: string): string {
  const type = String(actionType || "").trim();
  if (type === "provide_fact" || type === "provide_evidence") {
    return "customer_action_needed";
  }
  if (type === "wait_for_broker_review") {
    return "waiting_broker";
  }
  return "";
}

/** Local Slice1 peek — avoids importing slice1Customer (circular). */
function peekSlice1NextAction(task: CustomerTask): Slice1CustomerNextAction | null {
  const projection = task.slice1_projection;
  if (projection && typeof projection === "object" && projection.customer_next_action) {
    return projection.customer_next_action;
  }
  const v1 = task.task_contract_v1;
  if (v1 && v1.contract_version === "1" && v1.next_action) {
    return v1.next_action;
  }
  return null;
}

/**
 * Build task-contract + local fallbacks from a production CustomerTask,
 * then resolve through the single Constitution authority selector.
 */
export function resolveCustomerConstitutionFromTask(
  task: CustomerTask | null | undefined,
): ResolvedCustomerConstitution {
  const emptyLocal: LocalCustomerConstitution = {
    today: "",
    why: "",
    after: "",
    careLine: "",
    careNote: "",
    currentStage: "",
  };
  if (!task || typeof task !== "object") {
    return resolveCustomerConstitution({ local: emptyLocal });
  }

  const slice1Action = peekSlice1NextAction(task);
  const v1Action = task.task_contract_v1?.next_action;
  const dash = task.dashboard_summary;

  // Task-contract Focus = Slice1 / v1 titles only — never CTA labels (view_status, primary_cta).
  const taskContract: Partial<LocalCustomerConstitution> = {
    today: nonEmpty(v1Action?.title) || "",
    why: nonEmpty(v1Action?.instructions) || "",
    after: "",
    careLine: "",
    careNote: "",
    currentStage:
      stageFromSlice1Action(String(v1Action?.action_type || "")) ||
      stageFromSlice1Action(String(slice1Action?.action_type || "")) ||
      "",
  };

  const local: LocalCustomerConstitution = {
    today: nonEmpty(slice1Action?.title) || nonEmpty(dash?.next_action) || "",
    why: nonEmpty(slice1Action?.instructions) || "",
    after: "",
    careLine: "",
    careNote: "",
    currentStage:
      stageFromSlice1Action(String(slice1Action?.action_type || "")) ||
      (task.submitted ? "waiting_broker" : "customer_action_needed"),
  };

  return resolveCustomerConstitution({
    serverProjection: task.constitution_projection,
    taskContract,
    local,
  });
}
