import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import * as taskLaunchContext from "../../services/taskLaunchContext";
import type { TaskLaunchContext } from "../../types/task";
import { appConfig, devLog } from "../../utils/config";
import {
  contactBrokerModalCopy,
  isSubmitted,
  mapErrorMessage,
} from "../../utils/taskMapping";
import { resetApiHealthCache } from "../../utils/apiHealth";
import { DEFAULT_SAFETY_COPY, EMPTY_TASK_ERROR } from "../../utils/resolveTaskViewModel";
import { ApiRequestError } from "../../utils/request";
import { buildQaRuntimeDiagnostic } from "../../utils/requestErrors";
import { qaPathLog, summarizeLaunchQuery } from "../../utils/qaPathLog";
import { markResumeRestoredHint } from "../../utils/resumeHint";
import { clearResumeToken } from "../../utils/storage";

const ENTRY_RETRY_COOLDOWN_MS = 2000;
const NON_RETRYABLE_CODES = new Set([
  "token_missing",
  "invalid_or_expired_task_link",
  "domain_not_allowed",
  "tls_error",
]);

type PageData = {
  loadingMessage: string;
  launchSource: string;
  errorState: typeof EMPTY_TASK_ERROR;
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
  shellSafetyCopy: string;
};

function loadingMessageForSource(source: TaskLaunchContext["source"] | ""): string {
  if (source === "resume_storage") {
    return "正在恢复您上次填写的资料…";
  }
  return "正在打开您的资料…";
}

function entryErrorState(code: string): typeof EMPTY_TASK_ERROR {
  const retryable = !NON_RETRYABLE_CODES.has(code);
  return {
    code,
    message: mapErrorMessage(code),
    retryable,
    blocking: true,
  };
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在打开您的资料…",
    launchSource: "",
    errorState: EMPTY_TASK_ERROR,
    busy: {
      loading: true,
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
    shellSafetyCopy: DEFAULT_SAFETY_COPY,
  } as PageData,

  onLoad(options: Record<string, string | undefined>) {
    const q = summarizeLaunchQuery(options || {});
    qaPathLog("ENTRY", {
      page: "pages/entry/entry",
      queryKeys: q.queryKeys,
      queryRawSafe: q.queryRawSafe,
      hasToken: q.hasToken,
      note: "first_js_page_onload",
    });
    void this.bootstrap(options);
  },

  resolveLaunchContext(options: Record<string, string | undefined>) {
    return taskLaunchContext.resolveTaskLaunchContext(options);
  },

  persistLaunch(ctx: TaskLaunchContext) {
    taskLaunchContext.persistLaunchToken(ctx);
  },

  async fetchTask(token: string) {
    return CustomerTaskApi.getTask(token);
  },

  async bootstrap(options: Record<string, string | undefined>) {
    qaPathLog("BOOTSTRAP", {
      page: "entry",
      busyLoading: this.isBusy("loading"),
      launchSource: String(this.data.launchSource || ""),
      hasErrorMessage: Boolean(this.data.errorState?.message),
    });

    if (this.isBusy("loading") && this.data.launchSource) {
      // Ignore overlapping bootstrap while already opening.
      qaPathLog("EARLY_EXIT", {
        page: "entry",
        reason: "overlapping_bootstrap",
        launchSource: String(this.data.launchSource || ""),
      });
      return;
    }

    const now = Date.now();
    if (now < this.data.retryMeta.cooldownUntil && this.data.errorState.message) {
      qaPathLog("EARLY_EXIT", {
        page: "entry",
        reason: "retry_cooldown",
        errorCode: String(this.data.errorState?.code || ""),
      });
      wx.showToast({ title: "请稍候再试", icon: "none" });
      return;
    }

    this.setBusy("loading", true);
    this.setData({
      errorState: EMPTY_TASK_ERROR,
      retryMeta: {
        attempts: this.data.retryMeta.attempts,
        cooldownUntil: now + ENTRY_RETRY_COOLDOWN_MS,
      },
    });

    const resolution = taskLaunchContext.inspectLaunchTokenSources(options);
    qaPathLog("BOOTSTRAP", {
      page: "pages/entry/entry",
      phase: "token_resolve",
      tokenSource: resolution.source,
      hasLaunchQueryToken: resolution.launchQuery,
      hasDevTaskToken: resolution.devTaskToken,
      hasResumeToken: resolution.resumeToken,
    });

    const ctx = this.resolveLaunchContext(options);
    if (!ctx) {
      // First abort on Entry Preview with empty compile query: no API involved.
      qaPathLog("EARLY_EXIT", {
        page: "pages/entry/entry",
        reason: "token_missing_redirect_start_claim",
        why: "no_launch_query_token_and_no_devTaskToken_and_no_resume_storage",
        hasLaunchQueryToken: resolution.launchQuery,
        hasDevTaskToken: resolution.devTaskToken,
        hasResumeToken: resolution.resumeToken,
        next: "/pages/start-claim/start-claim",
      });
      this.setBusy("navigating", true);
      wx.redirectTo({
        url: "/pages/start-claim/start-claim",
        fail: () => {
          qaPathLog("EARLY_EXIT", {
            page: "entry",
            reason: "token_missing_and_redirect_failed",
            errorCode: "token_missing",
          });
          this.setData({
            launchSource: "",
            loadingMessage: "正在打开您的资料…",
            errorState: entryErrorState("token_missing"),
          });
          this.setBusy("navigating", false);
          this.setBusy("loading", false);
        },
      });
      return;
    }

    this.setData({
      launchSource: ctx.source,
      loadingMessage: loadingMessageForSource(ctx.source),
    });

    try {
      qaPathLog("BOOTSTRAP", {
        page: "entry",
        phase: "fetch_task",
        tokenSource: ctx.source,
      });
      const task = await this.fetchTask(ctx.token);
      this.persistLaunch(ctx);
      const app = getApp<IAppOption>();
      app.taskToken = ctx.token;
      app.task = task;

      if (ctx.source === "resume_storage") {
        markResumeRestoredHint();
      }

      const target = isSubmitted(task)
        ? "/pages/receipt/receipt"
        : "/pages/task-home/task-home";
      this.setBusy("navigating", true);
      wx.reLaunch({
        url: target,
        fail: () => {
          this.setData({
            errorState: entryErrorState("navigation_failed"),
          });
          this.setBusy("navigating", false);
          this.setBusy("loading", false);
        },
      });
    } catch (err) {
      const code =
        err instanceof ApiRequestError ? err.code : "network_error";
      const status = err instanceof ApiRequestError ? err.status : 0;
      const detail =
        err instanceof ApiRequestError && err.detail && typeof err.detail === "object"
          ? (err.detail as { errMsg?: unknown; errno?: unknown })
          : null;
      // QA-safe only: AppID/host/code — never token / PII.
      devLog(
        "[entry] task open failed",
        buildQaRuntimeDiagnostic({
          apiProfile: appConfig.apiProfile,
          apiBaseUrl: appConfig.apiBaseUrl,
          path: "/health/live|/api/h5/tasks/{token}/intake",
          errorCode: code,
          httpStatus: status,
          errMsg: String(detail?.errMsg || ""),
        }),
      );
      if (code === "invalid_or_expired_task_link") {
        clearResumeToken();
      }
      this.setData({
        errorState: entryErrorState(code),
      });
      this.setBusy("loading", false);
    }
  },

  onRetry() {
    if (this.isBusy("loading") || this.isBusy("navigating")) return;
    if (!this.data.errorState.retryable) {
      this.onContactBroker();
      return;
    }
    const now = Date.now();
    if (now < this.data.retryMeta.cooldownUntil) {
      wx.showToast({ title: "请稍候再试", icon: "none" });
      return;
    }
    resetApiHealthCache();
    this.setData({
      retryMeta: {
        attempts: this.data.retryMeta.attempts + 1,
        cooldownUntil: now + ENTRY_RETRY_COOLDOWN_MS,
      },
    });
    const app = getApp<IAppOption>();
    const token = String(app.taskToken || "").trim();
    void this.bootstrap(token ? { token } : {});
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
    });
  },
});
