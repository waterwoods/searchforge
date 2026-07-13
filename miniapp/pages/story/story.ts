import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import type { CustomerTask } from "../../types/task";
import {
  resolveTaskViewModel,
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import { contactBrokerModalCopy } from "../../utils/taskMapping";

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载事故经过…",
    story: "",
    charCount: 0,
    localDirty: false,
    minLength: 10,
    task: null as CustomerTask | null,
    taskViewModel: EMPTY_TASK_VIEW_MODEL,
    ...taskShellBindingsFromViewModel(EMPTY_TASK_VIEW_MODEL),
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
  },

  async onShow() {
    const token = this.requireToken();
    if (!token) return;
    await this.loadTask({ silent: false });
    if (this.data.localDirty) return;
    const existing = String(this.data.task?.key_facts?.accident_description || "");
    this.setData({ story: existing, charCount: existing.length });
  },

  onInput(e: WechatMiniprogram.Input) {
    const story = e.detail.value || "";
    this.setData({ story, charCount: story.length, localDirty: true });
  },

  onRetry() {
    void this.retryLoadTask();
  },

  async onSave() {
    const story = (this.data.story || "").trim();
    if (story.length < this.data.minLength) {
      wx.showToast({ title: `请至少填写${this.data.minLength}个字`, icon: "none" });
      return;
    }

    const token = this.requireToken();
    if (!token) return;
    await this.saveAndReturn(async () => {
      await CustomerTaskApi.saveStory(token, story);
      const readBack = await CustomerTaskApi.getTask(token);
      const app = getApp<IAppOption>();
      app.task = readBack;
      this.commitTaskViewModel(
        resolveTaskViewModel(
          readBack,
          readBack.task_contract,
          {
            route: (this as { route?: string }).route,
            busy: { ...this.data.busy, saving: true },
          },
          null,
        ),
      );
      this.setData({
        task: readBack,
        errorState: EMPTY_TASK_ERROR,
        story,
        charCount: story.length,
        localDirty: false,
      });
      wx.showToast({ title: "已保存", icon: "success" });
    });
  },

  onLater() {
    wx.navigateBack();
  },

  onContactBroker() {
    const copy = contactBrokerModalCopy();
    wx.showModal({
      title: copy.title,
      content: copy.content,
      showCancel: false,
      confirmText: "知道了",
    });
  },
});
