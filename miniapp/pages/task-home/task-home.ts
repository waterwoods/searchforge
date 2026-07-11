import { CustomerTaskApi } from "../../services/taskApi";
import { appConfig } from "../../utils/config";
import {
  buildSupplementRows,
  isSubmitted,
  progressPercent,
  prototypePhotoTarget,
  resolveNextAction,
  type SupplementTaskRow,
} from "../../utils/taskMapping";

type PageData = {
  loading: boolean;
  title: string;
  subtitle: string;
  status: string;
  received: string[];
  supplementRows: SupplementTaskRow[];
  nextAction: string;
  primaryCta: string;
  progress: number;
  photoCount: number;
  photoTarget: number;
  submitted: boolean;
  disclaimer: string;
  primaryRoute: string;
  navigating: boolean;
};

Page({
  data: {
    loading: true,
    title: "我的事故资料",
    subtitle: "",
    status: "",
    received: [] as string[],
    supplementRows: [] as SupplementTaskRow[],
    nextAction: "",
    primaryCta: "",
    progress: 0,
    photoCount: 0,
    photoTarget: prototypePhotoTarget(),
    submitted: false,
    disclaimer: "",
    primaryRoute: "",
    navigating: false,
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

    this.setData({
      loading: false,
      title: dash?.title || task.title || "我的事故资料",
      subtitle: dash?.subtitle || "",
      status: dash?.status || "进行中",
      received: dash?.received || [],
      supplementRows: buildSupplementRows(task),
      nextAction: dash?.next_action || "",
      primaryCta: next.primaryCta,
      primaryRoute: next.route || "/pages/task-home/task-home",
      progress: progressPercent(task),
      photoCount: Number(task.photo_count ?? task.attachment_count ?? 0),
      submitted: isSubmitted(task),
      disclaimer: dash?.warning || task.safety_copy || "",
    });
  },

  onPrimaryAction() {
    if (this.data.navigating) return;

    const route = this.data.primaryRoute;
    if (this.data.submitted) {
      this.navigateOnce("/pages/receipt/receipt");
      return;
    }
    if (route && route !== "/pages/task-home/task-home") {
      this.navigateOnce(route);
    }
  },

  onTapSupplementRow(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index);
    const row = this.data.supplementRows[index];
    if (!row?.actionable || !row.route || this.data.navigating) return;
    this.navigateOnce(row.route);
  },

  navigateOnce(route: string) {
    this.setData({ navigating: true });
    wx.navigateTo({
      url: route,
      complete: () => this.setData({ navigating: false }),
    });
  },

  onViewAll() {
    const lines: string[] = [];
    const { received, supplementRows } = this.data;
    if (received.length) {
      lines.push("已收到：\n" + received.join("、"));
    }
    if (supplementRows.length) {
      lines.push(
        "还需补充：\n" +
          supplementRows.map((row) => `${row.label}（${row.statusText}）`).join("、"),
      );
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
