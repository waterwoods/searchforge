import { taskPage } from "../../behaviors/taskPage";
import { appConfig } from "../../utils/config";
import type { CustomerTask } from "../../types/task";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  resolveTaskViewModel,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import {
  contactBrokerModalCopy,
  isSubmitted,
  photoCount,
} from "../../utils/taskMapping";
import { consumeResumeRestoredHint } from "../../utils/resumeHint";

type PageData = {
  loadingMessage: string;
  title: string;
  message: string;
  status: string;
  statusTone: "active" | "done";
  photoCount: number;
  nextStep: string;
  brokerContactNote: string;
  materialsNote: string;
  disclaimer: string;
  submitted: boolean;
  submittedAt: string;
  showSupplement: boolean;
  supplementHint: string;
  task: CustomerTask | null;
  taskViewModel: typeof EMPTY_TASK_VIEW_MODEL;
  shellSafetyCopy: string;
  ctaDisabledReason: string;
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
};

function formatSubmittedAt(iso: string): string {
  const raw = String(iso || "").trim();
  if (!raw) return "";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw;
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  const hh = String(date.getHours()).padStart(2, "0");
  const mm = String(date.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${d} ${hh}:${mm}`;
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载提交结果…",
    title: "资料已提交",
    message: "",
    status: "",
    statusTone: "done" as const,
    photoCount: 0,
    nextStep: "",
    brokerContactNote: "",
    materialsNote: "",
    disclaimer: "",
    submitted: false,
    submittedAt: "",
    showSupplement: false,
    supplementHint: "",
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
  } as PageData,

  async onShow() {
    const token = this.requireToken();
    if (!token) return;
    if (consumeResumeRestoredHint()) {
      wx.showToast({
        title: "已恢复您上次填写的内容",
        icon: "none",
        duration: 2500,
      });
    }
    // Always re-load so resume/reload never shows a stale receipt.
    const task = await this.loadTask();
    if (task) {
      this.applyReceiptState(task);
    }
  },

  onRetry() {
    void this.retryLoadTask().then((task) => {
      if (task) this.applyReceiptState(task);
    });
  },

  applyReceiptState(task: CustomerTask) {
    const busyForVm = {
      ...this.data.busy,
      loading: false,
    };
    const vm = resolveTaskViewModel(task, task.task_contract, {
      route: (this as { route?: string }).route || "/pages/receipt/receipt",
      busy: busyForVm,
    });
    const summary = task.completion_summary;
    const dash = task.dashboard_summary;
    const submitted = isSubmitted(task);
    const broker = appConfig.brokerDisplayName;
    const submittedAt = formatSubmittedAt(
      String(task.task_contract?.timestamps?.updated_at || ""),
    );
    const nextStep =
      summary?.next_step ||
      dash?.next_action ||
      (submitted
        ? "已提交，等待陈总查看"
        : vm.cta.label || `等待${broker}查看`);
    const supplementAllowed = Boolean(
      submitted || dash?.submitted_supplement_allowed || (task.missing_info || []).length > 0,
    );
    const supplementHint =
      (task.missing_info || []).map((item) => item.label).filter(Boolean)[0] ||
      (vm.missingItems || []).map((item) => item.label).filter(Boolean)[0] ||
      (supplementAllowed ? "如有需要，可继续补充照片。" : "");
    const brokerContactNote = submitted
      ? `${broker}会尽快查看您提交的资料，并在需要时通过微信联系您。`
      : `如有问题，请通过微信联系${broker}。`;
    const materialsNote = supplementHint
      ? supplementHint
      : `如有需要，${broker}可能请您补充更多材料，请留意微信消息。`;

    this.commitTaskViewModel(vm);
    this.setData({
      task,
      title: summary?.title || (submitted ? "资料已提交" : vm.title || "当前状态"),
      message:
        summary?.message ||
        dash?.subtitle ||
        (submitted ? `已成功提交，${broker}会尽快处理。` : vm.instruction || ""),
      status: dash?.status || vm.statusLabel || (submitted ? "已提交" : "进行中"),
      statusTone: submitted || vm.statusTone === "done" ? "done" : "active",
      photoCount: photoCount(task),
      nextStep,
      brokerContactNote,
      materialsNote,
      disclaimer:
        summary?.disclaimer ||
        dash?.warning ||
        vm.safetyCopy ||
        "这只是资料收集，不代表已向保险公司正式报案。",
      submitted,
      submittedAt,
      showSupplement: Boolean(supplementAllowed || (submitted && supplementHint)),
      supplementHint,
      errorState: EMPTY_TASK_ERROR,
    });
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

  onViewStatus() {
    if (this.isBusy("navigating")) return;
    this.setBusy("navigating", true);
    wx.redirectTo({
      url: "/pages/task-home/task-home",
      complete: () => this.setBusy("navigating", false),
      fail: () => {
        wx.navigateTo({
          url: "/pages/task-home/task-home",
          complete: () => this.setBusy("navigating", false),
        });
      },
    });
  },

  onViewAll() {
    const vm = this.data.taskViewModel;
    const lines: string[] = [];
    const received = this.data.task?.dashboard_summary?.received || [];
    if (received.length) {
      lines.push("已收到：\n" + received.join("、"));
    }
    if (vm.missingItems.length) {
      lines.push(
        "还需补充：\n" +
          vm.missingItems.map((row) => `${row.label}（${row.statusText}）`).join("、"),
      );
    }
    wx.showModal({
      title: "全部资料",
      content: lines.join("\n\n") || "暂无详情",
      showCancel: false,
    });
  },

  onEditSupplementInfo() {
    if (this.isBusy("navigating")) return;
    wx.showActionSheet({
      itemList: ["修改事故经过", "修改基本资料", "修改车辆及对方信息", "补充照片"],
      success: (res) => {
        const routes = [
          "/pages/story/story",
          "/pages/basics/basics",
          "/pages/basics/basics",
          "/pages/photos/photos",
        ];
        const route = routes[res.tapIndex];
        if (!route) return;
        wx.navigateTo({ url: route });
      },
    });
  },
});
