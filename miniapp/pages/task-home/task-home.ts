import { taskPage } from "../../behaviors/taskPage";
import { appConfig } from "../../utils/config";
import type { TaskViewModel } from "../../types/task";
import { contactBrokerModalCopy } from "../../utils/taskMapping";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import { consumeResumeRestoredHint } from "../../utils/resumeHint";
import {
  isSlice1CustomerFlow,
  mapSlice1CustomerView,
  REQUEST_ITEM_ROUTE,
  type Slice1CustomerView,
} from "../../utils/slice1Customer";
import type { Slice1RequestItem } from "../../types/task";

type PageData = {
  loadingMessage: string;
  taskViewModel: TaskViewModel;
  errorState: {
    code: string;
    message: string;
    retryable: boolean;
    blocking: boolean;
  };
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
  slice1Enabled: boolean;
  slice1WaitingForBroker: boolean;
  slice1PrimaryLabel: string;
  slice1Instruction: string;
  slice1ProgressText: string;
  slice1QueuedItems: Slice1RequestItem[];
  slice1SatisfiedItems: Slice1RequestItem[];
  slice1BrokerStatusLabel: string;
};

function brokerStatusLabel(status: string): string {
  if (status === "waiting_for_customer" || status === "wait_for_customer_item") return "等待您补充";
  if (status === "review_ready" || status === "review_customer_response") return "等待经纪人审核";
  return "";
}

function slice1PagePatch(view: Slice1CustomerView): Partial<PageData> {
  return {
    slice1Enabled: view.enabled,
    slice1WaitingForBroker: view.waitingForBroker,
    slice1PrimaryLabel: view.waitingForBroker
      ? "资料已提交，等待经纪人审核"
      : view.primaryCtaLabel || "补充陈总需要的资料",
    slice1Instruction: String(view.nextAction?.instructions || view.nextAction?.title || ""),
    slice1ProgressText:
      view.progress.total > 0 ? `进度 ${view.progress.satisfied}/${view.progress.total}` : "",
    slice1QueuedItems: view.queuedItems,
    slice1SatisfiedItems: view.satisfiedItems,
    slice1BrokerStatusLabel: brokerStatusLabel(view.brokerStatus),
  };
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载我的资料…",
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
    slice1Enabled: false,
    slice1WaitingForBroker: false,
    slice1PrimaryLabel: "",
    slice1Instruction: "",
    slice1ProgressText: "",
    slice1QueuedItems: [],
    slice1SatisfiedItems: [],
    slice1BrokerStatusLabel: "",
  } as PageData,

  onLoad() {
    void this.ensureTaskInitialized({ ownerLoad: true }).then((task) => {
      if (task) this.applySlice1Overlay(task);
    });
  },

  onShow() {
    this.setBusy("navigating", false);
    this.setBusy("uploading", false);
    if (consumeResumeRestoredHint()) {
      wx.showToast({
        title: "已恢复您上次填写的内容",
        icon: "none",
        duration: 2500,
      });
    }
    void this.ensureTaskInitialized().then((task) => {
      if (task) this.applySlice1Overlay(task);
    });
  },

  onUnload() {
    this.markTaskPageDestroyed();
  },

  onPullDownRefresh() {
    void this.rehydrateAuthoritativeTask()
      .then((task) => {
        if (task) this.applySlice1Overlay(task);
      })
      .finally(() => wx.stopPullDownRefresh());
  },

  applySlice1Overlay(task: Parameters<typeof mapSlice1CustomerView>[0]) {
    const view = mapSlice1CustomerView(task);
    this.setData(slice1PagePatch(view));
  },

  onRetry() {
    void this.retryLoadTask().then((task) => {
      if (task) this.applySlice1Overlay(task);
    });
  },

  onPrimaryAction() {
    const task = this.data.task;
    if (task && isSlice1CustomerFlow(task)) {
      const view = mapSlice1CustomerView(task);
      if (view.waitingForBroker) {
        this.onViewReceipt();
        return;
      }
      if (view.primaryActionable) {
        this.navigateOnce(REQUEST_ITEM_ROUTE);
        return;
      }
      this.onContactBroker();
      return;
    }

    if (task && (task.submitted || task.current_step === "done")) {
      this.onEditSupplementInfo();
      return;
    }
    const vm = this.data.taskViewModel;
    if (vm.cta.disabled) return;
    const route = this.resolveRouteFromCta(vm);
    if (!route || route === "/pages/task-home/task-home") return;
    this.navigateOnce(route);
  },

  resolveRouteFromCta(vm: TaskViewModel): string {
    const target = String(vm.cta.target || "").trim();
    if (target.startsWith("/pages/")) {
      return target;
    }
    if (vm.cta.actionType === "view_status") {
      return "/pages/receipt/receipt";
    }
    if (vm.cta.actionType === "submit") {
      return "/pages/review/review";
    }
    const sectionRouteMap: Record<string, string> = {
      story: "/pages/story/story",
      basics: "/pages/basics/basics",
      injury: "/pages/basics/basics",
      time_location: "/pages/basics/basics",
      photos: "/pages/photos/photos",
      review: "/pages/review/review",
      receipt: "/pages/receipt/receipt",
    };
    return sectionRouteMap[target] || "";
  },

  onTapSupplementRow(e: WechatMiniprogram.TouchEvent) {
    if (this.data.slice1Enabled) return;
    const detail = (e as WechatMiniprogram.CustomEvent<{ index?: number }>).detail;
    const index = Number(detail?.index ?? e.currentTarget.dataset.index);
    const row = this.data.taskViewModel?.missingItems[index];
    if (!row?.actionable || !row.route) return;
    this.navigateOnce(row.route);
  },

  navigateOnce(route: string) {
    if (!route || this.isBusy("navigating")) return;
    this.setBusy("navigating", true);
    wx.navigateTo({
      url: route,
      complete: () => this.setBusy("navigating", false),
    });
  },

  onViewAll() {
    const vm = this.data.taskViewModel;
    const lines: string[] = [];
    if (this.data.slice1Enabled) {
      if (this.data.slice1Instruction) lines.push(this.data.slice1Instruction);
      if (this.data.slice1QueuedItems.length) {
        lines.push(
          "稍后还需：\n" + this.data.slice1QueuedItems.map((row) => row.label).join("、"),
        );
      }
      if (this.data.slice1SatisfiedItems.length) {
        lines.push(
          "已完成：\n" + this.data.slice1SatisfiedItems.map((row) => row.label).join("、"),
        );
      }
    } else {
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
    }
    wx.showModal({
      title: "全部资料",
      content: lines.join("\n\n") || "暂无详情",
      showCancel: false,
    });
  },

  onEditSupplementInfo() {
    if (this.data.slice1Enabled) {
      if (this.data.slice1WaitingForBroker) {
        wx.showToast({ title: "资料已提交，等待经纪人审核", icon: "none" });
        return;
      }
      this.navigateOnce(REQUEST_ITEM_ROUTE);
      return;
    }
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
        if (route) this.navigateOnce(route);
      },
    });
  },

  onViewReceipt() {
    if (this.isBusy("navigating")) return;
    this.navigateOnce("/pages/receipt/receipt");
  },

  onShowDisclaimer() {
    const vm = this.data.taskViewModel;
    wx.showModal({
      title: appConfig.tenantDisplayName,
      content: vm.safetyCopy,
      showCancel: false,
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
});
