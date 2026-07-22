import { CustomerTaskApi } from "../services/taskApi";
import type { CustomerTask, TaskErrorState, TaskViewModel } from "../types/task";
import { resetApiHealthCache } from "../utils/apiHealth";
import { qaPathLog } from "../utils/qaPathLog";
import { ApiRequestError } from "../utils/request";
import { clearResumeToken } from "../utils/storage";
import { mapErrorMessage } from "../utils/taskMapping";
import {
  resolveTaskViewModel,
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
  taskViewModelDataPatch,
} from "../utils/resolveTaskViewModel";

const MAX_RETRY_ATTEMPTS = 3;
const RETRY_COOLDOWN_MS = 2000;
const LOAD_TIMEOUT_MS = 12_000;
const RETRYABLE_CODES = new Set([
  "network_error",
  "backend_unreachable",
  "save_failed",
  "submit_failed",
  "timeout",
]);

type InternalState = {
  latestRequestSeq: number;
  activeLoadPromise: Promise<CustomerTask | null> | null;
  activeLoadSeq: number | null;
  pageAlive: boolean;
  firstShowConsumed: boolean;
};

type TaskBehaviorData = {
  task: CustomerTask | null;
  taskViewModel: TaskViewModel;
  shellSafetyCopy: string;
  ctaDisabledReason: string;
  errorState: TaskErrorState;
  busy: {
    loading: boolean;
    saving: boolean;
    uploading: boolean;
    submitting: boolean;
    navigating: boolean;
    retrying: boolean;
  };
  retryMeta: {
    attempts: number;
    cooldownUntil: number;
  };
};

function normalizeError(code: string, blockingOverride?: boolean): TaskErrorState {
  const retryable = RETRYABLE_CODES.has(code);
  return {
    code,
    message: mapErrorMessage(code),
    retryable,
    blocking: typeof blockingOverride === "boolean" ? blockingOverride : !retryable,
  };
}

function ensureInternalState(target: WechatMiniprogram.Behavior.Instance): InternalState {
  const page = target as WechatMiniprogram.Behavior.Instance & { __taskPageState?: InternalState };
  if (!page.__taskPageState) {
    page.__taskPageState = {
      latestRequestSeq: 0,
      activeLoadPromise: null,
      activeLoadSeq: null,
      pageAlive: true,
      firstShowConsumed: false,
    };
  }
  return page.__taskPageState;
}

function navigateBackAsync(): Promise<void> {
  return new Promise((resolve, reject) => {
    wx.navigateBack({
      success: () => resolve(),
      fail: (err) => reject(err),
    });
  });
}

function withTimeout<T>(promise: Promise<T>, ms: number): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const timer = setTimeout(() => reject(new ApiRequestError("timeout")), ms);
    promise
      .then((value) => {
        clearTimeout(timer);
        resolve(value);
      })
      .catch((err) => {
        clearTimeout(timer);
        reject(err);
      });
  });
}

export const taskPage = Behavior({
  data: {
    task: null,
    taskViewModel: EMPTY_TASK_VIEW_MODEL,
    ...taskShellBindingsFromViewModel(EMPTY_TASK_VIEW_MODEL),
    errorState: EMPTY_TASK_ERROR,
    busy: {
      loading: false,
      saving: false,
      uploading: false,
      submitting: false,
      navigating: false,
      retrying: false,
    },
    retryMeta: {
      attempts: 0,
      cooldownUntil: 0,
    },
  } as TaskBehaviorData,

  lifetimes: {
    attached() {
      const state = ensureInternalState(this);
      state.pageAlive = true;
      const bindings = taskShellBindingsFromViewModel(this.data.taskViewModel);
      if (
        this.data.shellSafetyCopy !== bindings.shellSafetyCopy ||
        this.data.ctaDisabledReason !== bindings.ctaDisabledReason
      ) {
        this.setData(bindings);
      }
    },
    detached() {
      const state = ensureInternalState(this);
      state.pageAlive = false;
      state.latestRequestSeq += 1;
      state.activeLoadPromise = null;
      state.activeLoadSeq = null;
    },
  },

  pageLifetimes: {
    show() {
      ensureInternalState(this).pageAlive = true;
    },
    hide() {
      // Keep pageAlive true while hidden so in-flight loads can still complete
      // unless the page is destroyed (detached/onUnload).
    },
  },

  methods: {
    safeSetData(patch: Record<string, unknown>): void {
      if (!ensureInternalState(this).pageAlive) return;
      this.setData(patch);
    },

    commitTaskViewModel(vm: TaskViewModel): void {
      this.safeSetData(taskViewModelDataPatch(vm));
    },

    requireToken(): string | null {
      const app = getApp<IAppOption>();
      const token = String(app.taskToken || "").trim();
      if (!token) {
        qaPathLog("EARLY_EXIT", {
          page: String((this as { route?: string }).route || "taskPage"),
          reason: "requireToken_missing_redirect_entry",
          why: "app.taskToken_empty_page_opened_without_entry_bootstrap",
          next: "/pages/entry/entry",
        });
        wx.redirectTo({ url: "/pages/entry/entry" });
        return null;
      }
      return token;
    },

    setBusy(key: keyof TaskBehaviorData["busy"], value: boolean): void {
      if (!ensureInternalState(this).pageAlive) return;
      const next = {
        ...this.data.busy,
        [key]: value,
      };
      this.setData({ busy: next });
    },

    isBusy(key?: keyof TaskBehaviorData["busy"]): boolean {
      if (!key) return Object.values(this.data.busy).some(Boolean);
      return Boolean(this.data.busy[key]);
    },

    track(_event: string, _meta?: Record<string, unknown>): void {
      // A1 intentionally no-ops analytics wiring.
    },

    markTaskPageDestroyed(): void {
      const state = ensureInternalState(this);
      state.pageAlive = false;
      state.latestRequestSeq += 1;
      state.activeLoadPromise = null;
      state.activeLoadSeq = null;
    },

    /**
     * Single-flight authoritative task load.
     * Newer calls supersede older responses via request generation.
     * Concurrent callers join the in-flight promise when not forcing a refresh.
     */
    async loadTask(options?: {
      silent?: boolean;
      force?: boolean;
      joinInFlight?: boolean;
    }): Promise<CustomerTask | null> {
      const token = this.requireToken();
      if (!token) return null;

      const state = ensureInternalState(this);
      const silent = Boolean(options?.silent);
      const force = Boolean(options?.force);
      // Default: newer load supersedes. Explicit joinInFlight is for first-show ↔ onLoad.
      const joinInFlight = Boolean(options?.joinInFlight);

      if (!force && joinInFlight && state.activeLoadPromise) {
        return state.activeLoadPromise;
      }

      state.latestRequestSeq += 1;
      const requestSeq = state.latestRequestSeq;
      state.activeLoadSeq = requestSeq;

      const run = (async (): Promise<CustomerTask | null> => {
        if (!silent) {
          this.setBusy("loading", true);
        }

        try {
          const task = await withTimeout(CustomerTaskApi.getTask(token), LOAD_TIMEOUT_MS);
          if (!state.pageAlive || requestSeq !== state.latestRequestSeq) {
            return null;
          }

          const app = getApp<IAppOption>();
          app.task = task;
          const nextVm = resolveTaskViewModel(task, task.task_contract, {
            route: (this as { route?: string }).route,
            busy: this.data.busy,
          });
          this.safeSetData({
            task,
            errorState: EMPTY_TASK_ERROR,
            ...taskViewModelDataPatch(nextVm),
          });
          return task;
        } catch (error) {
          if (!state.pageAlive || requestSeq !== state.latestRequestSeq) {
            return null;
          }
          const code = error instanceof ApiRequestError ? error.code : "network_error";
          const app = getApp<IAppOption>();

          // Expired/invalid session: clear local binding and show restart state.
          // Do not invent a new token or QR — Founder must Launch Golden QA again.
          if (code === "invalid_or_expired_task_link") {
            clearResumeToken();
            try {
              app.taskToken = "";
              app.task = undefined;
            } catch {
              // ignore
            }
            const expiredError = normalizeError(code, true);
            this.safeSetData({
              task: null,
              errorState: expiredError,
              ...taskViewModelDataPatch(
                resolveTaskViewModel({} as CustomerTask, undefined, {
                  route: (this as { route?: string }).route,
                  busy: this.data.busy,
                }, expiredError),
              ),
            });
            wx.redirectTo({
              url: "/pages/error/error?code=invalid_or_expired_task_link",
            });
            return null;
          }

          const safeError = normalizeError(code);
          const cachedTask = app.task;

          if (safeError.retryable && cachedTask) {
            const cachedError = { ...safeError, blocking: false };
            this.safeSetData({
              task: cachedTask,
              errorState: cachedError,
              ...taskViewModelDataPatch(
                resolveTaskViewModel(cachedTask, cachedTask.task_contract, {
                  route: (this as { route?: string }).route,
                  busy: this.data.busy,
                }, cachedError),
              ),
            });
            return cachedTask;
          }

          const blockingError = { ...safeError, blocking: true };
          this.safeSetData({
            errorState: blockingError,
            ...taskViewModelDataPatch(
              resolveTaskViewModel(app.task || ({} as CustomerTask), app.task?.task_contract, {
                route: (this as { route?: string }).route,
                busy: this.data.busy,
              }, blockingError),
            ),
          });
          return null;
        } finally {
          if (state.activeLoadSeq === requestSeq) {
            state.activeLoadPromise = null;
            state.activeLoadSeq = null;
          }
          if (state.pageAlive && requestSeq === state.latestRequestSeq && !silent) {
            this.setBusy("loading", false);
            const task = this.data.task as CustomerTask | null;
            if (task?.case_id) {
              const errState = this.data.errorState as TaskErrorState;
              const vm = resolveTaskViewModel(
                task,
                task.task_contract,
                {
                  route: (this as { route?: string }).route,
                  busy: { ...this.data.busy, loading: false },
                },
                errState?.message ? errState : undefined,
              );
              this.safeSetData(taskViewModelDataPatch(vm));
            }
          }
        }
      })();

      state.activeLoadPromise = run;
      return run;
    },

    /** Rehydrate authoritative server truth (resume / pull-to-refresh / foreground). */
    async rehydrateAuthoritativeTask(options?: { silent?: boolean }): Promise<CustomerTask | null> {
      return this.loadTask({ silent: Boolean(options?.silent), force: true, joinInFlight: false });
    },

    /**
     * Unified page show initialization:
     * - first show joins/awaits cold load owned by onLoad when present
     * - later shows force a safe rehydrate
     */
    async ensureTaskInitialized(options?: { ownerLoad?: boolean }): Promise<CustomerTask | null> {
      const state = ensureInternalState(this);
      if (options?.ownerLoad) {
        return this.loadTask({ force: true, joinInFlight: false });
      }
      if (!state.firstShowConsumed) {
        state.firstShowConsumed = true;
        if (state.activeLoadPromise) {
          return state.activeLoadPromise;
        }
        return this.loadTask({ force: false, joinInFlight: true });
      }
      return this.rehydrateAuthoritativeTask({ silent: false });
    },

    async retryLoadTask(): Promise<CustomerTask | null> {
      const now = Date.now();
      const { attempts, cooldownUntil } = this.data.retryMeta;
      if (now < cooldownUntil) {
        wx.showToast({ title: "请稍候再试", icon: "none" });
        return null;
      }
      if (attempts >= MAX_RETRY_ATTEMPTS) {
        const exhausted = normalizeError("network_error", true);
        exhausted.message = "网络暂时不可用，请稍后再试或联系陈总。";
        this.safeSetData({ errorState: exhausted });
        return null;
      }

      this.setBusy("retrying", true);
      this.safeSetData({
        retryMeta: {
          attempts: attempts + 1,
          cooldownUntil: now + RETRY_COOLDOWN_MS,
        },
      });
      resetApiHealthCache();
      try {
        return await this.rehydrateAuthoritativeTask();
      } finally {
        this.setBusy("retrying", false);
      }
    },

    async saveAndReturn(saveFn: () => Promise<unknown>): Promise<boolean> {
      if (this.isBusy("saving")) return false;
      this.setBusy("saving", true);
      try {
        await Promise.resolve(saveFn());
        await navigateBackAsync();
        return true;
      } catch (error) {
        const code = error instanceof ApiRequestError ? error.code : "save_failed";
        const safeError = normalizeError(code, false);
        this.safeSetData({ errorState: safeError });
        wx.showToast({ title: safeError.message, icon: "none" });
        return false;
      } finally {
        this.setBusy("saving", false);
      }
    },
  },
});
