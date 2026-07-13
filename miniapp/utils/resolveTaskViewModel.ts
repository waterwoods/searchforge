import {
  buildSupplementRows,
  mapErrorMessage,
  progressPercent,
  resolveMissingItemNav,
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

export const DEFAULT_SAFETY_COPY =
  "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。";

/** Non-null sentinel — safe to bind into TaskShell / inline TaskError. */
export const EMPTY_TASK_ERROR: TaskErrorState = {
  code: "",
  message: "",
  retryable: false,
  blocking: false,
};

export const EMPTY_TASK_CTA: TaskCtaViewModel = {
  label: "继续",
  actionType: "go_to_section",
  target: "",
  disabled: false,
  loading: false,
  disabledReason: "",
};

/** Non-null placeholder until the first successful loadTask(). */
export const EMPTY_TASK_VIEW_MODEL: TaskViewModel = {
  source: "legacy",
  shellMode: "content",
  title: "我的事故资料",
  instruction: "",
  statusLabel: "进行中",
  statusTone: "active",
  progress: { completed: 0, total: 1, percent: 0 },
  cta: { ...EMPTY_TASK_CTA },
  missingItems: [],
  evidenceRequirements: [],
  reviewReady: false,
  submitReady: false,
  safetyCopy: DEFAULT_SAFETY_COPY,
  error: null,
};

export function normalizeUiString(value: unknown, fallback = ""): string {
  if (value == null) return fallback;
  return String(value).trim() || fallback;
}

export function normalizeTaskCta(cta: TaskCtaViewModel): TaskCtaViewModel {
  return {
    label: normalizeUiString(cta.label, "继续"),
    actionType: cta.actionType || "go_to_section",
    target: normalizeUiString(cta.target),
    disabled: Boolean(cta.disabled),
    loading: Boolean(cta.loading),
    disabledReason: normalizeUiString(cta.disabledReason),
  };
}

export type TaskShellBindings = {
  shellSafetyCopy: string;
  ctaDisabledReason: string;
};

/** Flat page fields for WXML → component bindings (avoids nested null on first paint). */
export function taskShellBindingsFromViewModel(
  vm?: TaskViewModel | null,
): TaskShellBindings {
  const safe = vm || EMPTY_TASK_VIEW_MODEL;
  return {
    shellSafetyCopy: normalizeUiString(safe.safetyCopy, DEFAULT_SAFETY_COPY),
    ctaDisabledReason: normalizeUiString(safe.cta?.disabledReason),
  };
}

export function taskViewModelDataPatch(
  vm: TaskViewModel,
): TaskShellBindings & { taskViewModel: TaskViewModel } {
  const normalized = {
    ...vm,
    cta: normalizeTaskCta(vm.cta),
    safetyCopy: normalizeUiString(vm.safetyCopy, DEFAULT_SAFETY_COPY),
  };
  return {
    taskViewModel: normalized,
    ...taskShellBindingsFromViewModel(normalized),
  };
}

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
  const code = normalizeUiString(error.code, "task_unavailable");
  const message = normalizeUiString(error.message, mapErrorMessage(code));
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
    const safeValue = normalizeUiString(value);
    if (!safeValue) continue;
    safeFields[key] = safeValue;
  }

  return {
    ...contract,
    title: normalizeUiString(contract.title, "我的事故资料"),
    instruction: normalizeUiString(contract.instruction),
    fields: safeFields,
    missing_items: (contract.missing_items || []).map((item) => ({
      key: normalizeUiString(item.key),
      label: normalizeUiString(item.label, "待补充资料"),
    })),
    evidence_requirements: (contract.evidence_requirements || []).map((item) => ({
      slot: normalizeUiString(item.slot),
      label: normalizeUiString(item.label, "照片"),
      min: Math.max(Number(item.min) || 0, 0),
      received: Math.max(Number(item.received) || 0, 0),
    })),
    branding: {
      office_name: normalizeUiString(contract.branding?.office_name, "陈总办公室"),
      safety_copy: normalizeUiString(contract.branding?.safety_copy),
    },
  };
}

function contractCta(
  contract: CustomerTaskSafeContract,
  busy: BusyState,
  error: TaskErrorState | null,
): TaskCtaViewModel {
  const disabledByState = busy.loading || busy.submitting || busy.saving || busy.navigating;
  const disabledByError = Boolean(error?.blocking);
  return normalizeTaskCta({
    label: normalizeUiString(contract.next_action?.label, "继续"),
    actionType: contract.next_action?.type || "go_to_section",
    target: normalizeUiString(contract.next_action?.target),
    disabled: disabledByState || disabledByError,
    loading: busy.loading || busy.submitting || busy.saving,
    disabledReason: disabledByError ? "请先处理当前错误" : "",
  });
}

function legacyCta(task: CustomerTask, busy: BusyState, error: TaskErrorState | null): TaskCtaViewModel {
  const next = resolveNextAction(task);
  const disabledByState = busy.loading || busy.submitting || busy.saving || busy.navigating;
  const disabledByError = Boolean(error?.blocking);
  return normalizeTaskCta({
    label: normalizeUiString(next.primaryCta, "继续"),
    actionType: "go_to_section",
    target: normalizeUiString(next.route),
    disabled: disabledByState || disabledByError,
    loading: busy.loading || busy.submitting || busy.saving,
    disabledReason: disabledByError ? "请先处理当前错误" : "",
  });
}

function finalizeViewModel(vm: TaskViewModel): TaskViewModel {
  return {
    ...vm,
    title: normalizeUiString(vm.title, "我的事故资料"),
    instruction: normalizeUiString(vm.instruction),
    statusLabel: normalizeUiString(vm.statusLabel, "进行中"),
    safetyCopy: normalizeUiString(vm.safetyCopy, DEFAULT_SAFETY_COPY),
    cta: normalizeTaskCta(vm.cta),
    missingItems: vm.missingItems.map((item) => ({
      key: normalizeUiString(item.key),
      label: normalizeUiString(item.label, "待补充资料"),
      statusText: normalizeUiString(item.statusText, "待补充"),
      actionable: Boolean(item.actionable),
      route: normalizeUiString(item.route),
      hint: normalizeUiString(item.hint),
    })),
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
    return finalizeViewModel({
      source: "contract",
      shellMode: busy.loading ? "loading" : normalizedError?.blocking ? "blocking_error" : "content",
      title: safeContract.title || normalizeUiString(task.title, "我的事故资料"),
      instruction: safeContract.instruction,
      statusLabel: status.label,
      statusTone: status.tone,
      progress,
      cta: contractCta(safeContract, busy, normalizedError),
      missingItems: safeContract.missing_items
        .map((item) => {
          const nav = resolveMissingItemNav(item.key, task);
          if (nav.action === "COMPLETED") {
            return null;
          }
          return {
            key: item.key,
            label: item.label,
            statusText: normalizeUiString(nav.statusText, "待补充"),
            actionable: nav.action === "ACTIONABLE_NOW",
            route: normalizeUiString(nav.route),
            hint: normalizeUiString(nav.hint),
          };
        })
        .filter(Boolean) as TaskViewModel["missingItems"],
      evidenceRequirements: safeContract.evidence_requirements,
      reviewReady: Boolean(safeContract.review_ready),
      submitReady: Boolean(safeContract.submit_ready),
      safetyCopy:
        safeContract.branding.safety_copy ||
        normalizeUiString(task.safety_copy, DEFAULT_SAFETY_COPY),
      error: normalizedError,
    });
  }

  const progress = clampProgress(
    Math.round((progressPercent(task) * Math.max(task.step_total || 1, 1)) / 100),
    task.step_total || 1,
  );
  return finalizeViewModel({
    source: "legacy",
    shellMode: busy.loading ? "loading" : normalizedError?.blocking ? "blocking_error" : "content",
    title: normalizeUiString(task.title, "我的事故资料"),
    instruction: normalizeUiString(task.dashboard_summary?.next_action),
    statusLabel: normalizeUiString(task.dashboard_summary?.status, "进行中"),
    statusTone: task.submitted ? "done" : "active",
    progress,
    cta: legacyCta(task, busy, normalizedError),
    missingItems: buildSupplementRows(task).map((item) => ({
      key: normalizeUiString(item.key),
      label: normalizeUiString(item.label, "待补充资料"),
      statusText: normalizeUiString(item.statusText, "待补充"),
      actionable: Boolean(item.actionable),
      route: normalizeUiString(item.route),
      hint: normalizeUiString(item.hint),
    })),
    evidenceRequirements: [],
    reviewReady: task.current_step === "review",
    submitReady: task.current_step === "review" && !task.submitted,
    safetyCopy: normalizeUiString(task.safety_copy, DEFAULT_SAFETY_COPY),
    error: normalizedError,
  });
}

/**
 * Migration note:
 * Client fallback inference remains temporary. Once contract parity passes,
 * client inference ceases to be authoritative and can be retired.
 */
