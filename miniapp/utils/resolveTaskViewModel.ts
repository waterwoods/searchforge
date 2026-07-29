import {
  basicsComplete,
  buildSupplementRows,
  isSubmitted,
  mapErrorMessage,
  photosSatisfiedForPrototype,
  progressPercent,
  mapServerMissingItem,
  resolveNextAction,
  resolveSupplementAction,
  storyComplete,
} from "./taskMapping";
import { isSlice1CustomerFlow, mapSlice1CustomerView, REQUEST_ITEM_ROUTE } from "./slice1Customer";
import { resolveCustomerConstitutionFromTask } from "./resolveCustomerConstitution";
import { HUB_NAME } from "./customerCaseSurface";
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
  "这是给办公室整理用的记录，不等于向保险公司正式报案。";

/** Legacy hub titles from older contracts — remap to Pilot SSOT. */
const LEGACY_HUB_TITLES = new Set(["我的事故资料", "事故资料"]);

function normalizeHubTitle(raw: unknown, fallback: string = HUB_NAME): string {
  const title = normalizeUiString(raw, fallback);
  if (LEGACY_HUB_TITLES.has(title)) return HUB_NAME;
  return title || HUB_NAME;
}

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
  title: HUB_NAME,
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
  "police_involved",
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
    title: normalizeHubTitle(contract.title),
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
    loading: busy.submitting,
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
    loading: busy.submitting,
    disabledReason: disabledByError ? "请先处理当前错误" : "",
  });
}

/** Customer-facing reason when submit CTA must stay disabled. */
export function resolveSubmitDisabledReason(
  task: CustomerTask,
  submitReady: boolean,
  busy?: Partial<BusyState>,
  error?: TaskErrorState | null,
): string {
  const nextBusy = normalizeBusyState(busy);
  if (error?.blocking) return "请先处理当前错误";
  if (nextBusy.submitting) return "正在提交…";
  if (nextBusy.loading) return "正在加载…";
  if (isSubmitted(task)) return "资料已提交，无需重复提交。";
  if (submitReady) return "";
  if (!storyComplete(task)) return "请先填写事故经过";
  if (!basicsComplete(task)) return "请先补全基本资料";
  if (!photosSatisfiedForPrototype(task)) return "请先上传必需照片";
  return "请先补全必填资料";
}

function applyRouteSpecificCta(
  vm: TaskViewModel,
  task: CustomerTask,
  busy: BusyState,
  error: TaskErrorState | null,
  pageContext?: TaskPageContext,
): TaskViewModel {
  const route = normalizeUiString(pageContext?.route).toLowerCase();
  if (route.includes("review")) {
    const submitReady = Boolean(vm.submitReady) && !isSubmitted(task);
    const disabledByState = busy.loading || busy.submitting || busy.navigating;
    const disabledByError = Boolean(error?.blocking);
    const disabledReason = resolveSubmitDisabledReason(task, submitReady, busy, error);
    return {
      ...vm,
      cta: normalizeTaskCta({
        label: "确认并交给陈总",
        actionType: "submit",
        target: "receipt",
        disabled: !submitReady || disabledByState || disabledByError,
        loading: busy.submitting,
        disabledReason,
      }),
    };
  }
  if (route.includes("receipt")) {
    return {
      ...vm,
      statusTone: isSubmitted(task) ? "done" : vm.statusTone,
      statusLabel: isSubmitted(task)
        ? normalizeUiString(vm.statusLabel, "已提交")
        : vm.statusLabel,
      cta: normalizeTaskCta({
        label: "返回我的报案",
        actionType: "view_status",
        target: "task-home",
        disabled: busy.loading || busy.navigating,
        loading: false,
        disabledReason: "",
      }),
    };
  }

  // Task Home (and non-Review hubs): never route post-submit「继续补充资料」to inert Review.
  if (isSubmitted(task)) {
    const supplement = resolveSupplementAction(vm.missingItems);
    const disabledByState = busy.loading || busy.submitting || busy.saving || busy.navigating;
    const disabledByError = Boolean(error?.blocking);
    if (supplement) {
      return {
        ...vm,
        cta: normalizeTaskCta({
          label: "继续补充资料",
          actionType: "go_to_section",
          target: supplement.route,
          disabled: disabledByState || disabledByError,
          loading: busy.submitting,
          disabledReason: disabledByError ? "请先处理当前错误" : "",
        }),
      };
    }
    return {
      ...vm,
      cta: normalizeTaskCta({
        label: "查看提交结果",
        actionType: "go_to_section",
        target: "/pages/receipt/receipt",
        disabled: disabledByState || disabledByError,
        loading: false,
        disabledReason: disabledByError ? "请先处理当前错误" : "",
      }),
    };
  }

  return vm;
}

function finalizeViewModel(vm: TaskViewModel): TaskViewModel {
  return {
    ...vm,
    title: normalizeHubTitle(vm.title),
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

function legacySubmitReady(task: CustomerTask): boolean {
  return (
    !isSubmitted(task) &&
    storyComplete(task) &&
    basicsComplete(task) &&
    photosSatisfiedForPrototype(task)
  );
}

export function resolveTaskViewModel(
  task: CustomerTask,
  taskContract?: CustomerTaskSafeContract | null,
  pageContext?: TaskPageContext,
  safeErrorState?: TaskErrorState | null,
): TaskViewModel {
  const busy = normalizeBusyState(pageContext?.busy);
  const normalizedError = normalizeError(safeErrorState || taskContract?.error);

  // Slice 1 server Next Action wins when projection is present.
  if (isSlice1CustomerFlow(task)) {
    const slice1 = mapSlice1CustomerView(task);
    const progress = clampProgress(slice1.progress.satisfied, Math.max(slice1.progress.total, 1));
    const disabledByState = busy.loading || busy.submitting || busy.saving || busy.navigating;
    const disabledByError = Boolean(normalizedError?.blocking);
    // Focus line: Constitution Today → Why → Slice1 display → dashboard.
    const focusInstruction = normalizeUiString(
      slice1.constitutionToday ||
        slice1.nextAction?.title ||
        slice1.constitutionWhy ||
        slice1.nextAction?.instructions ||
        task.dashboard_summary?.next_action,
    );
    const baseVm = finalizeViewModel({
      source: "contract",
      shellMode: busy.loading ? "loading" : normalizedError?.blocking ? "blocking_error" : "content",
      title: normalizeHubTitle(task.title),
      instruction: focusInstruction,
      statusLabel: slice1.waitingForBroker ? "等待陈总" : "需补充材料",
      statusTone: slice1.waitingForBroker ? "done" : "active",
      progress,
      cta: normalizeTaskCta({
        label: slice1.waitingForBroker
          ? "已提交，陈总正在看"
          : normalizeUiString(slice1.primaryCtaLabel, "补充陈总需要的资料"),
        actionType: slice1.waitingForBroker ? "view_status" : "go_to_section",
        target: slice1.waitingForBroker ? "/pages/receipt/receipt" : REQUEST_ITEM_ROUTE,
        disabled: slice1.waitingForBroker || disabledByState || disabledByError || !slice1.primaryActionable,
        loading: busy.submitting,
        disabledReason: slice1.waitingForBroker
          ? "已提交，陈总正在看"
          : disabledByError
            ? "请先处理当前错误"
            : "",
      }),
      missingItems: slice1.queuedItems.map((item) => ({
        key: item.request_item_id,
        label: item.label,
        statusText: "稍后",
        actionable: false,
        route: "",
        hint: "按顺序补充，当前只需完成上方一项",
      })),
      evidenceRequirements: [],
      reviewReady: false,
      submitReady: false,
      safetyCopy: normalizeUiString(task.safety_copy, DEFAULT_SAFETY_COPY),
      error: normalizedError,
    });
    return baseVm;
  }

  if (taskContract) {
    const constitution = resolveCustomerConstitutionFromTask(task);
    const safeContract = normalizeContract(taskContract);
    const status = normalizeStatus(safeContract.task_status);
    const progress = clampProgress(
      safeContract.progress?.completed || 0,
      safeContract.progress?.total || 0,
    );
    // Server Constitution Focus → existing contract instruction → local resolver fallback.
    const serverFocus =
      constitution.fieldAuthority.today === "server"
        ? constitution.today
        : constitution.fieldAuthority.why === "server"
          ? constitution.why
          : "";
    const baseVm = finalizeViewModel({
      source: "contract",
      shellMode: busy.loading ? "loading" : normalizedError?.blocking ? "blocking_error" : "content",
      title: normalizeHubTitle(safeContract.title || task.title),
      instruction: normalizeUiString(serverFocus || safeContract.instruction),
      statusLabel: status.label,
      statusTone: status.tone,
      progress,
      cta: contractCta(safeContract, busy, normalizedError),
      missingItems: safeContract.missing_items
        .map((item) => {
          const row = mapServerMissingItem(item, task);
          if (!row) return null;
          return {
            key: row.key,
            label: row.label,
            statusText: normalizeUiString(row.statusText, "待补充"),
            actionable: Boolean(row.actionable),
            route: normalizeUiString(row.route),
            hint: normalizeUiString(row.hint),
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
    return applyRouteSpecificCta(baseVm, task, busy, normalizedError, pageContext);
  }

  const constitution = resolveCustomerConstitutionFromTask(task);
  const serverFocus =
    constitution.fieldAuthority.today === "server"
      ? constitution.today
      : constitution.fieldAuthority.why === "server"
        ? constitution.why
        : "";
  const progress = clampProgress(
    Math.round((progressPercent(task) * Math.max(task.step_total || 1, 1)) / 100),
    task.step_total || 1,
  );
  const ready = legacySubmitReady(task);
  const baseVm = finalizeViewModel({
    source: "legacy",
    shellMode: busy.loading ? "loading" : normalizedError?.blocking ? "blocking_error" : "content",
    title: normalizeHubTitle(task.title),
    instruction: normalizeUiString(
      serverFocus || task.dashboard_summary?.next_action,
    ),
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
    reviewReady: ready || task.current_step === "review",
    submitReady: ready,
    safetyCopy: normalizeUiString(task.safety_copy, DEFAULT_SAFETY_COPY),
    error: normalizedError,
  });
  return applyRouteSpecificCta(baseVm, task, busy, normalizedError, pageContext);
}

/**
 * Migration note:
 * Client fallback inference remains temporary. Once contract parity passes,
 * client inference ceases to be authoritative and can be retired.
 */
