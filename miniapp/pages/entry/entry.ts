import { CustomerTaskApi } from "../../services/taskApi";
import {
  persistLaunchToken,
  resolveTaskLaunchContext,
} from "../../services/taskLaunchContext";
import { mapErrorMessage, isSubmitted } from "../../utils/taskMapping";
import { ApiRequestError } from "../../utils/request";
import { clearResumeToken } from "../../utils/storage";

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
    this.setData({ loading: true, errorMessage: "", errorCode: "" });

    const ctx = resolveTaskLaunchContext(options);
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

      if (isSubmitted(task)) {
        wx.redirectTo({ url: "/pages/receipt/receipt" });
        return;
      }

      wx.redirectTo({ url: "/pages/task-home/task-home" });
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
