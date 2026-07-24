import { taskPage } from "../../behaviors/taskPage";
import { resolveCustomerContext } from "../../services/sessionIdentityAdapter";
import { appConfig, devLog } from "../../utils/config";
import {
  contactBrokerModalCopy,
  mapErrorMessage,
} from "../../utils/taskMapping";
import { resetApiHealthCache } from "../../utils/apiHealth";
import { DEFAULT_SAFETY_COPY, EMPTY_TASK_ERROR } from "../../utils/resolveTaskViewModel";
import { ApiRequestError } from "../../utils/request";
import { buildQaRuntimeDiagnostic } from "../../utils/requestErrors";
import { qaPathLog, summarizeLaunchQuery } from "../../utils/qaPathLog";
import { routeForCustomerNextAction } from "../../utils/customerContextRoute";
import { SERVICE_HOME_ROUTE } from "../../utils/serviceHome";
import { clearResumeToken } from "../../utils/storage";

const ENTRY_RETRY_COOLDOWN_MS = 2000;
const NON_RETRYABLE_CODES = new Set([
  "token_missing",
  "invalid_or_expired_task_link",
  "case_not_found",
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
    try {
      const q = summarizeLaunchQuery(options || {});
      qaPathLog("ENTRY", {
        page: "pages/entry/entry",
        queryKeys: q.queryKeys,
        queryRawSafe: q.queryRawSafe,
        hasToken: q.hasToken,
        note: "first_js_page_onload",
      });
    } catch (_err) {
      // Never block Page lifecycle / registration on QA logging.
    }
    return this.bootstrap(options);
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

    this.setData({
      launchSource: "server_context",
      loadingMessage: "正在确认您的资料…",
    });

    try {
      const context = await resolveCustomerContext({
        launchToken: String(options?.token || "").trim(),
      });
      const target = routeForCustomerNextAction(context.nextAction);
      if (context.nextAction === "START_NEW_CLAIM") {
        this.setBusy("navigating", true);
        wx.reLaunch({
          url: target,
          fail: () => {
            this.setData({ errorState: entryErrorState("navigation_failed") });
            this.setBusy("navigating", false);
            this.setBusy("loading", false);
          },
        });
        return;
      }
      if (!context.resumeToken) {
        throw new ApiRequestError("token_missing");
      }
      const app = getApp<IAppOption>();
      app.taskToken = context.resumeToken;
      app.task = undefined;
      qaPathLog("BOOTSTRAP", {
        page: "entry",
        phase: "navigate_from_server_context",
        nextAction: context.nextAction,
      });
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
      if (code === "invalid_or_expired_task_link" || code === "case_not_found") {
        clearResumeToken();
        try {
          const app = getApp<IAppOption>();
          app.taskToken = "";
          app.task = undefined;
        } catch {
          // ignore
        }
      }
      // Missing/deleted case: recover to clean Service Home (no ghost Continue / Receipt).
      if (code === "case_not_found") {
        this.setBusy("navigating", true);
        this.setBusy("loading", false);
        wx.reLaunch({
          url: SERVICE_HOME_ROUTE,
          fail: () => {
            wx.redirectTo({
              url: SERVICE_HOME_ROUTE,
              fail: () => {
                this.setData({ errorState: entryErrorState(code) });
                this.setBusy("navigating", false);
              },
            });
          },
        });
        return;
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
