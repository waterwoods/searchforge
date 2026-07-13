import { CustomerTaskApi } from "../services/taskApi";
import type { CustomerTask, TaskErrorState, TaskViewModel } from "../types/task";
import { resetApiHealthCache } from "../utils/apiHealth";
import { ApiRequestError } from "../utils/request";
import { mapErrorMessage } from "../utils/taskMapping";
import { resolveTaskViewModel } from "../utils/resolveTaskViewModel";

const MAX_RETRY_ATTEMPTS = 3;
const RETRY_COOLDOWN_MS = 2000;
const RETRYABLE_CODES = new Set(["network_error", "backend_unreachable", "save_failed", "submit_failed"]);

type InternalState = {
  latestRequestSeq: number;
};

type TaskBehaviorData = {
  task: CustomerTask | null;
  taskViewModel: TaskViewModel | null;
  errorState: TaskErrorState | null;
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

export const taskPage = Behavior({
  data: {
    task: null,
    taskViewModel: null,
    errorState: null,
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

  methods: {
    requireToken(): string | null {
      const app = getApp<IAppOption>();
      const token = String(app.taskToken || "").trim();
      if (!token) {
        wx.redirectTo({ url: "/pages/entry/entry" });
        return null;
      }
      return token;
    },

    setBusy(key: keyof TaskBehaviorData["busy"], value: boolean): void {
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

    async loadTask(options?: { silent?: boolean }): Promise<CustomerTask | null> {
      const token = this.requireToken();
      if (!token) return null;

      const state = ensureInternalState(this);
      state.latestRequestSeq += 1;
      const requestSeq = state.latestRequestSeq;
      const silent = Boolean(options?.silent);

      if (!silent) {
        this.setBusy("loading", true);
      }

      try {
        const task = await CustomerTaskApi.getTask(token);
        if (requestSeq !== state.latestRequestSeq) {
          return null;
        }

        const app = getApp<IAppOption>();
        app.task = task;
        const nextVm = resolveTaskViewModel(task, task.task_contract, {
          route: (this as { route?: string }).route,
          busy: this.data.busy,
        });
        this.setData({
          task,
          taskViewModel: nextVm,
          errorState: null,
        });
        return task;
      } catch (error) {
        if (requestSeq !== state.latestRequestSeq) {
          return null;
        }
        const code = error instanceof ApiRequestError ? error.code : "network_error";
        const app = getApp<IAppOption>();
        const safeError = normalizeError(code);
        const cachedTask = app.task;

        if (safeError.retryable && cachedTask) {
          const cachedError = { ...safeError, blocking: false };
          this.setData({
            task: cachedTask,
            errorState: cachedError,
            taskViewModel: resolveTaskViewModel(cachedTask, cachedTask.task_contract, {
              route: (this as { route?: string }).route,
              busy: this.data.busy,
            }, cachedError),
          });
          return cachedTask;
        }

        const blockingError = { ...safeError, blocking: true };
        this.setData({
          errorState: blockingError,
          taskViewModel: resolveTaskViewModel(app.task || ({} as CustomerTask), app.task?.task_contract, {
            route: (this as { route?: string }).route,
            busy: this.data.busy,
          }, blockingError),
        });
        return null;
      } finally {
        if (requestSeq === ensureInternalState(this).latestRequestSeq && !silent) {
          this.setBusy("loading", false);
        }
      }
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
        exhausted.message = "网络暂时不可用，请稍后重试或联系陈总。";
        this.setData({ errorState: exhausted });
        return null;
      }

      this.setBusy("retrying", true);
      this.setData({
        retryMeta: {
          attempts: attempts + 1,
          cooldownUntil: now + RETRY_COOLDOWN_MS,
        },
      });
      resetApiHealthCache();
      try {
        return await this.loadTask();
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
        this.setData({ errorState: safeError });
        wx.showToast({ title: safeError.message, icon: "none" });
        return false;
      } finally {
        this.setBusy("saving", false);
      }
    },
  },
});

