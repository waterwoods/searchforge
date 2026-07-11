import { CustomerTaskApi } from "../../services/taskApi";
import { appConfig } from "../../utils/config";
import {
  isSubmitted,
  missingItemLabel,
  photoCount,
  progressPercent,
  prototypePhotoTarget,
  resolveNextAction,
  storyComplete,
} from "../../utils/taskMapping";

type PageData = {
  loading: boolean;
  title: string;
  subtitle: string;
  status: string;
  received: string[];
  missing: string[];
  nextAction: string;
  primaryCta: string;
  progress: number;
  photoCount: number;
  photoTarget: number;
  storyDone: boolean;
  submitted: boolean;
  disclaimer: string;
  primaryRoute: string;
};

Page({
  data: {
    loading: true,
    title: "我的事故资料",
    subtitle: "",
    status: "",
    received: [] as string[],
    missing: [] as string[],
    nextAction: "",
    primaryCta: "",
    progress: 0,
    photoCount: 0,
    photoTarget: prototypePhotoTarget(),
    storyDone: false,
    submitted: false,
    disclaimer: "",
    primaryRoute: "",
  } as PageData,

  onShow() {
    this.refreshTask();
  },

  async refreshTask() {
    const app = getApp<{ taskToken?: string; task?: import("../../types/task").CustomerTask }>();
    const token = app.taskToken;
    if (!token) {
      wx.redirectTo({ url: "/pages/entry/entry" });
      return;
    }

    this.setData({ loading: true });
    try {
      const task = await CustomerTaskApi.getTask(token);
      app.task = task;
      this.applyTask(task);
    } catch {
      wx.redirectTo({ url: "/pages/entry/entry" });
    }
  },

  applyTask(task: import("../../types/task").CustomerTask) {
    const dash = task.dashboard_summary;
    const next = resolveNextAction(task);
    const missing = (task.missing_info || []).map(missingItemLabel);

    this.setData({
      loading: false,
      title: dash?.title || task.title || "我的事故资料",
      subtitle: dash?.subtitle || "",
      status: dash?.status || "进行中",
      received: dash?.received || [],
      missing,
      nextAction: dash?.next_action || "",
      primaryCta: next.primaryCta,
      primaryRoute: next.route || "/pages/task-home/task-home",
      progress: progressPercent(task),
      photoCount: photoCount(task),
      storyDone: storyComplete(task),
      submitted: isSubmitted(task),
      disclaimer: dash?.warning || task.safety_copy || "",
    });
  },

  onPrimaryAction() {
    const route = this.data.primaryRoute;
    if (this.data.submitted) {
      wx.navigateTo({ url: "/pages/receipt/receipt" });
      return;
    }
    if (route && route !== "/pages/task-home/task-home") {
      wx.navigateTo({ url: route });
    }
  },

  onViewAll() {
    const lines: string[] = [];
    const { received, missing } = this.data;
    if (received.length) {
      lines.push("已收到：\n" + received.join("、"));
    }
    if (missing.length) {
      lines.push("还缺：\n" + missing.join("、"));
    }
    wx.showModal({
      title: "全部资料",
      content: lines.join("\n\n") || "暂无详情",
      showCancel: false,
    });
  },

  onShowDisclaimer() {
    wx.showModal({
      title: appConfig.tenantDisplayName,
      content: this.data.disclaimer,
      showCancel: false,
    });
  },
});
