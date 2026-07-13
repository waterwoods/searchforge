import {
  buildSupplementRows,
  mapErrorMessage,
  progressPercent,
  resolveNextAction,
} from "./taskMapping";
import type {
  BusyState,
  CustomerTask,
  CustomerTaskSafeContract,
  TaskContractError,
  TaskContractStatus,
  TaskCtaViewModel,
  TaskErrorState,
  TaskPageContext,
  TaskViewModel,
} from "../types/task";

const DEFAULT_SAFETY_COPY = "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。";
const DEFAULT_BUSY_STATE: BusyState = {
  loading: false,
  saving: false,
  uploading: false,
  submitting: false,
  navigating: false,
  retrying: false,
};

const ALLOWED_FIELD_KEYS = new Set([
  "anyone_injured",
  "injury_status",
  "accident_datetime",
  "accident_location",
  "accident_description",
  "own_vehicle_info",
  "other_party_plate",
  "other_party_info",
]);

function normalizeBusyState(partial?: Partial<BusyState>): BusyState {
  return {
    ...DEFAULT_BUSY_STATE,
    ...(partial || {}),
  };
}

function clampProgress(completed: number, total: number): { completed: number; total: number; percent: number } {
  const safeTotal = Math.max(Number(total) || 0, 1);
  const safeCompleted = Math.max(0, Math.min(Number(completed) || 0, safeTotal));
  return {
    completed: safeCompleted,
    total: safeTotal,
    percent: Math.round((safeCompleted / safeTotal) * 100),
  };
}

function normalizeStatus(status: TaskContractStatus): { label: string; tone: "active" | "done" } {
  if (status === "submitted") return { label: "已提交", tone: "done" };
  if (status === "review_ready") return { label: "待提交", tone: "active" };
  return { label: "进行中", tone: "active" };
}

function normalizeError(error?: TaskErrorState | TaskContractError | null): TaskErrorState | null {
  if (!error) return null;
  const code = String(error.code || "task_unavailable");
  const message = String(error.message || mapErrorMessage(code));
  const retryable = typeof error.retryable === "boolean" ? error.retryable : false;
  return {
    code,
    message,
    retryable,
    blocking: !retryable,
  };
}

function normalizeContract(contract: CustomerTaskSafeContract): CustomerTaskSafeContract {
  const safeFields: Record<string, string> = {};
  for (const [key, value] of Object.entries(contract.fields || {})) {
    if (!ALLOWED_FIELD_KEYS.has(key)) continue;
    const safeValue = String(value || "").trim();
    if (!safeValue) continue;
    safeFields[key] = safeValue;
  }

  return {
    ...contract,
    fields: safeFields,
    missing_items: (contract.missing_items || []).map((item) => ({
      key: String(item.key || ""),
      label: String(item.label || ""),
    })),
    evidence_requirements: (contract.evidence_requirements || []).map((item) => ({
      slot: String(item.slot || ""),
      label: String(item.label || ""),
      min: Math.max(Number(item.min) || 0, 0),
      received: Math.max(Number(item.received) || 0, 0),
    })),
  };
}

function contractCta(
  contract: CustomerTaskSafeContract,
  busy: BusyState,
  error: TaskErrorState | null,
): TaskCtaViewModel {
  const disabledByState = busy.loading || busy.submitting || busy.saving || busy.navigating;
  const disabledByError = Boolean(error?.blocking);
  const label = String(contract.next_action?.label || "继续");
  return {
    label,
    actionType: contract.next_action?.type || "go_to_section",
    target: contract.next_action?.target || undefined,
    disabled: disabledByState || disabledByError,
    loading: busy.loading || busy.submitting || busy.saving,
    disabledReason: disabledByError ? "请先处理当前错误" : undefined,
  };
}

function legacyCta(task: CustomerTask, busy: BusyState, error: TaskErrorState | null): TaskCtaViewModel {
  const next = resolveNextAction(task);
  const disabledByState = busy.loading || busy.submitting || busy.saving || busy.navigating;
  const disabledByError = Boolean(error?.blocking);
  return {
    label: next.primaryCta || "继续",
    actionType: "go_to_section",
    target: next.route,
    disabled: disabledByState || disabledByError,
    loading: busy.loading || busy.submitting || busy.saving,
    disabledReason: disabledByError ? "请先处理当前错误" : undefined,
  };
}

export function resolveTaskViewModel(
  task: CustomerTask,
  taskContract?: CustomerTaskSafeContract | null,
  pageContext?: TaskPageContext,
  safeErrorState?: TaskErrorState | null,
): TaskViewModel {
  const busy = normalizeBusyState(pageContext?.busy);
  const normalizedError = normalizeError(safeErrorState || taskContract?.error);

  if (taskContract) {
    const safeContract = normalizeContract(taskContract);
    const status = normalizeStatus(safeContract.task_status);
    const progress = clampProgress(
      safeContract.progress?.completed || 0,
      safeContract.progress?.total || 0,
    );
    return {
      source: "contract",
      shellMode: busy.loading ? "loading" : normalizedError?.blocking ? "blocking_error" : "content",
      title: safeContract.title || task.title || "我的事故资料",
      instruction: safeContract.instruction || "",
      statusLabel: status.label,
      statusTone: status.tone,
      progress,
      cta: contractCta(safeContract, busy, normalizedError),
      missingItems: safeContract.missing_items.map((item) => ({
        key: item.key,
        label: item.label || "待补充资料",
        statusText: "待补充",
        actionable: Boolean(safeContract.next_action?.target),
      })),
      evidenceRequirements: safeContract.evidence_requirements,
      reviewReady: Boolean(safeContract.review_ready),
      submitReady: Boolean(safeContract.submit_ready),
      safetyCopy: safeContract.branding?.safety_copy || task.safety_copy || DEFAULT_SAFETY_COPY,
      error: normalizedError,
    };
  }

  const progress = clampProgress(
    Math.round((progressPercent(task) * Math.max(task.step_total || 1, 1)) / 100),
    task.step_total || 1,
  );
  return {
    source: "legacy",
    shellMode: busy.loading ? "loading" : normalizedError?.blocking ? "blocking_error" : "content",
    title: task.title || "我的事故资料",
    instruction: task.dashboard_summary?.next_action || "",
    statusLabel: task.dashboard_summary?.status || "进行中",
    statusTone: task.submitted ? "done" : "active",
    progress,
    cta: legacyCta(task, busy, normalizedError),
    missingItems: buildSupplementRows(task),
    evidenceRequirements: [],
    reviewReady: task.current_step === "review",
    submitReady: task.current_step === "review" && !task.submitted,
    safetyCopy: task.safety_copy || DEFAULT_SAFETY_COPY,
    error: normalizedError,
  };
}

/**
 * Migration note:
 * Client fallback inference remains temporary. Once contract parity passes,
 * client inference ceases to be authoritative and can be retired.
 */
