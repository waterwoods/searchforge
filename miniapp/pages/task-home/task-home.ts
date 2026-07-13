import { taskPage } from "../../behaviors/taskPage";
import { appConfig } from "../../utils/config";
import {
  type SupplementTaskRow,
} from "../../utils/taskMapping";
import type { TaskViewModel } from "../../types/task";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";

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
};

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载当前任务和资料状态…",
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

  onShow() {
    void this.loadTask();
  },

  onRetry() {
    void this.retryLoadTask();
  },

  onPrimaryAction() {
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
    const index = Number(e.currentTarget.dataset.index);
    const row: SupplementTaskRow | undefined = this.data.taskViewModel?.missingItems[index];
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

  onShowDisclaimer() {
    const vm = this.data.taskViewModel;
    wx.showModal({
      title: appConfig.tenantDisplayName,
      content: vm.safetyCopy,
      showCancel: false,
    });
  },

  onContactBroker() {
    this.onShowDisclaimer();
  },
});
