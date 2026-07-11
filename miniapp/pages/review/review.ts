import { CustomerTaskApi } from "../../services/taskApi";
import { appConfig } from "../../utils/config";
import {
  basicsComplete,
  mapErrorMessage,
  missingItemLabel,
  photoCount,
  storyComplete,
} from "../../utils/taskMapping";
import { ApiRequestError } from "../../utils/request";

Page({
  data: {
    story: "",
    photoCount: 0,
    received: [] as string[],
    missing: [] as string[],
    submitting: false,
    canSubmit: false,
    disclaimer: "",
  },

  onShow() {
    this.refresh();
  },

  refresh() {
    const app = getApp<{ task?: import("../../types/task").CustomerTask }>();
    const task = app.task;
    if (!task) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }
    const dash = task.dashboard_summary;
    const story = String(task.key_facts?.accident_description || "");
    const canSubmit =
      storyComplete(task) &&
      basicsComplete(task) &&
      !task.submitted;

    this.setData({
      story,
      photoCount: photoCount(task),
      received: dash?.received || [],
      missing: (task.missing_info || []).map(missingItemLabel),
      canSubmit,
      disclaimer:
        `提交后，${appConfig.brokerDisplayName}会在工作台看到这些资料并进行人工查看。这不是向保险公司正式报案。`,
    });
  },

  async onSubmit() {
    if (!this.data.canSubmit) {
      wx.showToast({ title: "请先补全必填资料", icon: "none" });
      return;
    }

    const app = getApp<{ taskToken?: string; task?: import("../../types/task").CustomerTask }>();
    const token = app.taskToken;
    if (!token) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }

    this.setData({ submitting: true });
    try {
      const intent = CustomerTaskApi.getOrCreateSubmitIntentId();
      const task = await CustomerTaskApi.submitTask(token, intent);
      app.task = task;
      wx.redirectTo({ url: "/pages/receipt/receipt" });
    } catch (err) {
      const code = err instanceof ApiRequestError ? err.code : "submit_failed";
      if (code === "missing_required_fields") {
        wx.showModal({
          title: "还不能提交",
          content: mapErrorMessage(code),
          confirmText: "去补充",
          success(res) {
            if (res.confirm) wx.navigateTo({ url: "/pages/basics/basics" });
          },
        });
      } else {
        wx.showToast({ title: mapErrorMessage(code), icon: "none" });
      }
    } finally {
      this.setData({ submitting: false });
    }
  },

  onEditStory() {
    wx.navigateTo({ url: "/pages/story/story" });
  },

  onEditPhotos() {
    wx.navigateTo({ url: "/pages/photos/photos" });
  },
});
