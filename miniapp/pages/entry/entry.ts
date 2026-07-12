import { CustomerTaskApi } from "../../services/taskApi";
import {
  persistLaunchToken,
  resolveTaskLaunchContext,
} from "../../services/taskLaunchContext";
import { mapErrorMessage, isSubmitted } from "../../utils/taskMapping";
import { resetApiHealthCache } from "../../utils/apiHealth";
import { devLog } from "../../utils/config";
import { ApiRequestError } from "../../utils/request";
import { clearResumeToken } from "../../utils/storage";

const RETRY_COOLDOWN_MS = 5000;
let lastBootstrapAt = 0;

Page({
  data: {
    loading: true,
    errorMessage: "",
    errorCode: "",
  },

  onLoad(options: Record<string, string | undefined>) {
    this.bootstrap(options);
  },

  async bootstrap(options: Record<string, string | undefined>) {
    const now = Date.now();
    if (now - lastBootstrapAt < RETRY_COOLDOWN_MS && !this.data.loading) {
      wx.showToast({ title: "请稍候再试", icon: "none" });
      return;
    }
    lastBootstrapAt = now;

    this.setData({ loading: true, errorMessage: "", errorCode: "" });

    const ctx = resolveTaskLaunchContext(options);
    devLog("[prototype] entry bootstrap:", ctx ? `using ${ctx.source}` : "no token");
    if (!ctx) {
      this.setData({
        loading: false,
        errorCode: "token_missing",
        errorMessage: "未找到任务入口，请从微信任务卡片重新打开。",
      });
      return;
    }

    try {
      const task = await CustomerTaskApi.getTask(ctx.token);
      persistLaunchToken(ctx);
      const app = getApp<IAppOption>();
      app.taskToken = ctx.token;
      app.task = task;

      const target = isSubmitted(task)
        ? "/pages/receipt/receipt"
        : "/pages/task-home/task-home";
      wx.reLaunch({
        url: target,
        fail: () => {
          this.setData({
            loading: false,
            errorCode: "navigation_failed",
            errorMessage: mapErrorMessage("navigation_failed"),
          });
        },
      });
    } catch (err) {
      const code =
        err instanceof ApiRequestError ? err.code : "network_error";
      if (code === "invalid_or_expired_task_link") {
        clearResumeToken();
      }
      this.setData({
        loading: false,
        errorCode: code,
        errorMessage: mapErrorMessage(code),
      });
    }
  },

  onRetry() {
    resetApiHealthCache();
    const app = getApp<{ taskToken?: string }>();
    const token = app.taskToken || "";
    this.bootstrap(token ? { token } : {});
  },

  onContactBroker() {
    wx.showModal({
      title: "联系陈总",
      content: "请返回微信，给陈总发消息说明情况。",
      showCancel: false,
    });
  },
});
