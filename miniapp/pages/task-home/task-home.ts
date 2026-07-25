import { taskPage } from "../../behaviors/taskPage";
import { appConfig } from "../../utils/config";
import type { TaskViewModel } from "../../types/task";
import { qaPathLog, summarizeLaunchQuery } from "../../utils/qaPathLog";
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
import {
  resolveCustomerTaskCardsFromTask,
  resolveTaskHomePrimaryRoute,
  type CustomerTaskCardView,
} from "../../utils/resolveCustomerTaskCards";
import {
  CASE_STATUS_ROUTE,
  isWaitingBrokerSurface,
} from "../../utils/customerCaseSurface";

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
  /** P26A — Constitution Focus + Task Cards */
  constitutionEnabled: boolean;
  constitutionToday: string;
  constitutionWhy: string;
  constitutionAfter: string;
  careLine: string;
  careNote: string;
  showCareLine: boolean;
  showWaiting: boolean;
  waitingLabel: string;
  taskCards: CustomerTaskCardView[];
};

function brokerStatusLabel(status: string): string {
  if (status === "waiting_for_customer" || status === "wait_for_customer_item") return "等待您补充";
  if (status === "review_ready" || status === "review_customer_response") return "等待陈总审核";
  return "";
}

function slice1PagePatch(
  view: Slice1CustomerView,
  task: Parameters<typeof resolveCustomerTaskCardsFromTask>[0],
  taskCards: CustomerTaskCardView[],
): Partial<PageData> {
  const focusInstruction = String(
    view.constitutionToday ||
      view.nextAction?.title ||
      view.constitutionWhy ||
      view.nextAction?.instructions ||
      "",
  );
  const waiting =
    view.waitingForBroker || view.currentStage === "waiting_broker" || view.currentStage === "waiting";
  const serverCustomer = task?.constitution_projection?.customer;
  const hasServerConstitution = Boolean(
    serverCustomer &&
      (String(serverCustomer.today || "").trim() ||
        (Array.isArray(serverCustomer.tasks) && serverCustomer.tasks.length)),
  );
  return {
    slice1Enabled: view.enabled,
    slice1WaitingForBroker: view.waitingForBroker,
    slice1PrimaryLabel: view.waitingForBroker
      ? "资料已提交，等待陈总审核"
      : view.primaryCtaLabel || "补充陈总需要的资料",
    slice1Instruction: focusInstruction,
    slice1ProgressText:
      view.progress.total > 0 ? `进度 ${view.progress.satisfied}/${view.progress.total}` : "",
    slice1QueuedItems: view.queuedItems,
    slice1SatisfiedItems: view.satisfiedItems,
    slice1BrokerStatusLabel: brokerStatusLabel(view.brokerStatus),
    // Constitution-first UI only when server projection (or its task cards) is present.
    constitutionEnabled: hasServerConstitution || taskCards.length > 0,
    constitutionToday: view.constitutionToday,
    constitutionWhy: view.constitutionWhy,
    constitutionAfter: view.constitutionAfter,
    careLine: view.careLine,
    careNote: view.careNote,
    showCareLine: Boolean(view.careLine),
    showWaiting: waiting && !view.primaryActionable,
    waitingLabel: waiting ? view.constitutionToday || "先不用操作" : "",
  };
}

function taskCardsPatch(task: Parameters<typeof resolveCustomerTaskCardsFromTask>[0]): {
  taskCards: CustomerTaskCardView[];
} {
  return {
    taskCards: resolveCustomerTaskCardsFromTask(task),
  };
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载我的报案…",
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
    constitutionEnabled: false,
    constitutionToday: "",
    constitutionWhy: "",
    constitutionAfter: "",
    careLine: "",
    careNote: "",
    showCareLine: false,
    showWaiting: false,
    waitingLabel: "",
    taskCards: [],
  } as PageData,

  onLoad(options: Record<string, string | undefined>) {
    const q = summarizeLaunchQuery(options || {});
    qaPathLog("ENTRY", {
      page: "pages/task-home/task-home",
      queryKeys: q.queryKeys,
      queryRawSafe: q.queryRawSafe,
      hasToken: q.hasToken,
      note: "first_js_page_onload_or_navigated",
    });
    void this.ensureTaskInitialized({ ownerLoad: true }).then((task) => {
      if (task && this.redirectIfWaitingBroker(task)) return;
      if (task) this.applyConstitutionOverlay(task);
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
      if (task && this.redirectIfWaitingBroker(task)) return;
      if (task) this.applyConstitutionOverlay(task);
    });
  },

  onUnload() {
    this.markTaskPageDestroyed();
  },

  onPullDownRefresh() {
    void this.rehydrateAuthoritativeTask()
      .then((task) => {
        if (task && this.redirectIfWaitingBroker(task)) return;
        if (task) this.applyConstitutionOverlay(task);
      })
      .finally(() => wx.stopPullDownRefresh());
  },

  /** D-014: Waiting Broker is Case Status — never a fake Task Home. */
  redirectIfWaitingBroker(task: Parameters<typeof mapSlice1CustomerView>[0]): boolean {
    if (!isWaitingBrokerSurface(task)) return false;
    if (this.isBusy("navigating")) return true;
    this.setBusy("navigating", true);
    wx.reLaunch({
      url: CASE_STATUS_ROUTE,
      complete: () => this.setBusy("navigating", false),
      fail: () => {
        wx.redirectTo({
          url: CASE_STATUS_ROUTE,
          complete: () => this.setBusy("navigating", false),
        });
      },
    });
    return true;
  },

  applyConstitutionOverlay(task: Parameters<typeof mapSlice1CustomerView>[0]) {
    const view = mapSlice1CustomerView(task);
    const cards = taskCardsPatch(task);
    this.setData({
      ...slice1PagePatch(view, task, cards.taskCards),
      ...cards,
    });
  },

  onRetry() {
    void this.retryLoadTask().then((task) => {
      if (task) this.applyConstitutionOverlay(task);
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
      const route = resolveTaskHomePrimaryRoute(task) || (view.primaryActionable ? REQUEST_ITEM_ROUTE : "");
      if (route) {
        this.navigateOnce(route);
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

  onTapTaskCard(e: WechatMiniprogram.CustomEvent<{ taskId?: string }>) {
    const taskId = String(e.detail?.taskId || "").trim();
    const card = this.data.taskCards.find((row) => row.taskId === taskId);
    if (!card?.actionable || !card.route) {
      if (card?.state === "blocked") {
        wx.showToast({ title: "请先完成今天的任务", icon: "none" });
      }
      return;
    }
    this.navigateOnce(card.route);
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
    if (this.data.slice1Enabled || this.data.taskCards.length) return;
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
    if (this.data.taskCards.length) {
      lines.push(
        "任务：\n" +
          this.data.taskCards
            .map((row) => `${row.title}（${row.stateLabel} · ${row.progressText}）`)
            .join("\n"),
      );
    } else if (this.data.slice1Enabled) {
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
        wx.showToast({ title: "资料已提交，等待陈总审核", icon: "none" });
        return;
      }
      const route = resolveTaskHomePrimaryRoute(this.data.task) || REQUEST_ITEM_ROUTE;
      this.navigateOnce(route);
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
