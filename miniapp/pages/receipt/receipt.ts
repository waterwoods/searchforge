import { CustomerTaskApi } from "../../services/taskApi";
import { appConfig } from "../../utils/config";
import { isSubmitted, mapErrorMessage, photoCount } from "../../utils/taskMapping";
import { ApiRequestError } from "../../utils/request";

Page({
  data: {
    title: "资料已提交",
    message: "",
    status: "",
    photoCount: 0,
    nextStep: "",
    disclaimer: "",
    submitted: true,
  },

  onShow() {
    this.refresh();
  },

  async refresh() {
    const app = getApp<{ taskToken?: string; task?: import("../../types/task").CustomerTask }>();
    const token = app.taskToken;
    if (!token) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }

    try {
      const task = await CustomerTaskApi.getTask(token);
      app.task = task;
      const summary = task.completion_summary;
      const dash = task.dashboard_summary;
      this.setData({
        title: summary?.title || (isSubmitted(task) ? "资料已提交" : "当前状态"),
        message: summary?.message || dash?.subtitle || "",
        status: dash?.status || "",
        photoCount: photoCount(task),
        nextStep: summary?.next_step || dash?.next_action || `等待${appConfig.brokerDisplayName}查看`,
        disclaimer:
          summary?.disclaimer ||
          dash?.warning ||
          "这只是资料收集，不代表已向保险公司正式报案。",
        submitted: isSubmitted(task),
      });
    } catch (err) {
      const code =
        err instanceof ApiRequestError ? err.code : "network_error";
      if (app.task) {
        wx.showToast({ title: mapErrorMessage(code), icon: "none" });
        return;
      }
      wx.redirectTo({ url: "/pages/entry/entry" });
    }
  },

  onViewStatus() {
    wx.redirectTo({ url: "/pages/task-home/task-home" });
  },

  onSupplement() {
    wx.navigateTo({ url: "/pages/photos/photos" });
  },
});
