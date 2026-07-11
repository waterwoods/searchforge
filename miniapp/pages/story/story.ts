import { CustomerTaskApi } from "../../services/taskApi";
import { mapErrorMessage } from "../../utils/taskMapping";
import { ApiRequestError } from "../../utils/request";

Page({
  data: {
    story: "",
    charCount: 0,
    saving: false,
    minLength: 10,
  },

  onShow() {
    const app = getApp<{ task?: { key_facts?: Record<string, string | null> } }>();
    const existing = String(app.task?.key_facts?.accident_description || "");
    this.setData({ story: existing, charCount: existing.length });
  },

  onInput(e: WechatMiniprogram.Input) {
    const story = e.detail.value || "";
    this.setData({ story, charCount: story.length });
  },

  async onSave() {
    const story = (this.data.story || "").trim();
    if (story.length < this.data.minLength) {
      wx.showToast({ title: `请至少填写${this.data.minLength}个字`, icon: "none" });
      return;
    }

    const app = getApp<{ taskToken?: string; task?: unknown }>();
    const token = app.taskToken;
    if (!token) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }

    this.setData({ saving: true });
    try {
      const task = await CustomerTaskApi.saveStory(token, story);
      app.task = task;
      wx.showToast({ title: "已保存", icon: "success" });
      setTimeout(() => wx.navigateBack(), 400);
    } catch (err) {
      const code = err instanceof ApiRequestError ? err.code : "save_failed";
      wx.showToast({ title: mapErrorMessage(code), icon: "none" });
    } finally {
      this.setData({ saving: false });
    }
  },

  onLater() {
    wx.navigateBack();
  },
});
