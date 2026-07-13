import { taskPage } from "../../behaviors/taskPage";
import {
  contactBrokerModalCopy,
  mapErrorMessage,
} from "../../utils/taskMapping";
import { DEFAULT_SAFETY_COPY, EMPTY_TASK_ERROR } from "../../utils/resolveTaskViewModel";

const NON_RETRYABLE_CODES = new Set([
  "token_missing",
  "invalid_or_expired_task_link",
]);

type PageData = {
  loadingMessage: string;
  title: string;
  errorState: typeof EMPTY_TASK_ERROR;
  shellError: typeof EMPTY_TASK_ERROR;
  busy: {
    loading: boolean;
    saving: boolean;
    uploading: boolean;
    submitting: boolean;
    navigating: boolean;
    retrying: boolean;
  };
  shellSafetyCopy: string;
  ctaDisabledReason: string;
};

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在准备恢复…",
    title: "暂时无法继续",
    errorState: EMPTY_TASK_ERROR,
    shellError: EMPTY_TASK_ERROR,
    busy: {
      loading: false,
      saving: false,
      uploading: false,
      submitting: false,
      navigating: false,
      retrying: false,
    },
    shellSafetyCopy: DEFAULT_SAFETY_COPY,
    ctaDisabledReason: "",
  } as PageData,

  onLoad(options: Record<string, string | undefined>) {
    const code = String(options.code || "unknown").trim() || "unknown";
    const retryable = !NON_RETRYABLE_CODES.has(code);
    this.setData({
      title: "暂时无法继续",
      errorState: {
        code,
        message: mapErrorMessage(code),
        retryable,
        blocking: false,
      },
      ctaDisabledReason: retryable ? "" : "请从微信任务卡片重新打开，或联系陈总。",
    });
  },

  onRetry() {
    if (this.isBusy("navigating")) return;
    if (!this.data.errorState.retryable) {
      this.onContactBroker();
      return;
    }
    this.setBusy("navigating", true);
    wx.reLaunch({
      url: "/pages/entry/entry",
      complete: () => this.setBusy("navigating", false),
      fail: () => {
        wx.showToast({ title: mapErrorMessage("navigation_failed"), icon: "none" });
        this.setBusy("navigating", false);
      },
    });
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
