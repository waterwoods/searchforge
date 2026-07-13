import { taskPage } from "../../behaviors/taskPage";
import { CustomerTaskApi } from "../../services/taskApi";
import { appConfig } from "../../utils/config";
import type { CustomerTask } from "../../types/task";
import { ApiRequestError } from "../../utils/request";
import {
  EMPTY_TASK_ERROR,
  EMPTY_TASK_VIEW_MODEL,
  resolveTaskViewModel,
  resolveSubmitDisabledReason,
  taskShellBindingsFromViewModel,
} from "../../utils/resolveTaskViewModel";
import {
  contactBrokerModalCopy,
  isSubmitted,
  mapErrorMessage,
  mapServerMissingItem,
  photoCount,
  resolveSupplementAction,
} from "../../utils/taskMapping";

type MissingRow = {
  key: string;
  label: string;
  actionable: boolean;
  route: string;
};

type PageData = {
  loadingMessage: string;
  story: string;
  storyPreview: string;
  photoCount: number;
  received: string[];
  missing: string[];
  missingRows: MissingRow[];
  showSupplementCta: boolean;
  supplementCtaLabel: string;
  supplementRoute: string;
  canSubmit: boolean;
  readyLabel: string;
  readySummary: string;
  submitDisabledReason: string;
  disclaimer: string;
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

function previewStory(story: string): string {
  const raw = String(story || "").trim();
  if (!raw) return "未填写";
  if (raw.length <= 48) return raw;
  return `${raw.slice(0, 48)}…`;
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载提交前检查…",
    story: "",
    storyPreview: "未填写",
    photoCount: 0,
    received: [] as string[],
    missing: [] as string[],
    missingRows: [] as MissingRow[],
    showSupplementCta: false,
    supplementCtaLabel: "去补充资料",
    supplementRoute: "",
    canSubmit: false,
    readyLabel: "请确认内容是否正确",
    readySummary: "正在检查资料…",
    submitDisabledReason: "请先补全必填资料",
    disclaimer: "",
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
    const task = await this.loadTask();
    if (task) {
      this.applyReviewState(task);
    }
  },

  onRetry() {
    void this.retryLoadTask().then((task) => {
      if (task) this.applyReviewState(task);
    });
  },

  applyReviewState(task: CustomerTask) {
    // Called only after successful load/read-back — treat loading as cleared.
    const busyForVm = {
      ...this.data.busy,
      loading: false,
    };
    const vm = resolveTaskViewModel(task, task.task_contract, {
      route: (this as { route?: string }).route || "/pages/review/review",
      busy: busyForVm,
    });
    const dash = task.dashboard_summary;
    const story = String(task.key_facts?.accident_description || "");
    let missingRows: MissingRow[] = (vm.missingItems || [])
      .map((item) => ({
        key: String(item.key || ""),
        label: String(item.label || "").trim(),
        actionable: Boolean(item.actionable && item.route),
        route: String(item.route || ""),
      }))
      .filter((item) => item.label);
    if (!missingRows.length) {
      for (const item of task.missing_info || []) {
        const row = mapServerMissingItem(item, task);
        if (!row?.label) continue;
        missingRows.push({
          key: row.key,
          label: row.label,
          actionable: Boolean(row.actionable && row.route),
          route: String(row.route || ""),
        });
      }
    }
    const missing = missingRows.map((item) => item.label);
    const canSubmit = Boolean(vm.submitReady) && !isSubmitted(task);
    const submitDisabledReason = resolveSubmitDisabledReason(
      task,
      canSubmit,
      busyForVm,
      this.data.errorState?.message ? this.data.errorState : null,
    );
    const readyLabel = canSubmit ? "内容正确即可提交" : "还有资料需要确认";
    const readySummary = canSubmit
      ? "主要资料已齐全，可以提交给陈总审核。"
      : missing.length
        ? `还需补充：${missing.slice(0, 2).join("、")}${missing.length > 2 ? "等" : ""}。`
        : "请先补全必填资料后再提交。";
    const supplement = resolveSupplementAction(missingRows);

    this.commitTaskViewModel(vm);
    this.setData({
      task,
      story,
      storyPreview: previewStory(story),
      photoCount: photoCount(task),
      received: dash?.received || [],
      missing,
      missingRows,
      showSupplementCta: Boolean(supplement),
      supplementCtaLabel: supplement?.label || "去补充资料",
      supplementRoute: supplement?.route || "",
      canSubmit,
      readyLabel,
      readySummary,
      submitDisabledReason,
      disclaimer:
        vm.safetyCopy ||
        `提交后，${appConfig.brokerDisplayName}会查看这些资料并尽快回复您。这不是向保险公司正式报案。`,
      errorState: EMPTY_TASK_ERROR,
    });
  },

  navigateOnce(route: string) {
    if (!route || this.isBusy("navigating") || this.isBusy("submitting")) return;
    this.setBusy("navigating", true);
    wx.navigateTo({
      url: route,
      complete: () => this.setBusy("navigating", false),
    });
  },

  onTapMissingRow(e: WechatMiniprogram.TouchEvent) {
    const index = Number(e.currentTarget.dataset.index);
    const row = this.data.missingRows[index];
    if (!row?.actionable || !row.route) return;
    this.navigateOnce(row.route);
  },

  onSupplement() {
    if (!this.data.showSupplementCta || !this.data.supplementRoute) return;
    this.navigateOnce(this.data.supplementRoute);
  },

  async onSubmit() {
    if (this.isBusy("submitting") || this.isBusy("navigating")) {
      return;
    }
    if (!this.data.canSubmit) {
      wx.showToast({
        title: this.data.submitDisabledReason || "请先补全必填资料",
        icon: "none",
      });
      return;
    }

    const token = this.requireToken();
    if (!token) return;

    this.setBusy("submitting", true);
    this.setData({
      errorState: EMPTY_TASK_ERROR,
      submitDisabledReason: "正在提交…",
    });
    try {
      const intent = CustomerTaskApi.getOrCreateSubmitIntentId();
      await CustomerTaskApi.submitTask(token, intent);
      const readBack = await this.loadTask({ silent: true });
      if (!readBack || !isSubmitted(readBack)) {
        throw new ApiRequestError("submit_failed");
      }
      this.applyReviewState(readBack);
      wx.showToast({ title: "提交成功", icon: "success", duration: 1200 });
      this.setBusy("navigating", true);
      wx.redirectTo({
        url: "/pages/receipt/receipt",
        complete: () => this.setBusy("navigating", false),
      });
    } catch (err) {
      const code = err instanceof ApiRequestError ? err.code : "submit_failed";
      if (code === "missing_required_fields") {
        const supplementRoute = this.data.supplementRoute || "/pages/task-home/task-home";
        this.setData({
          errorState: {
            code,
            message: mapErrorMessage(code),
            retryable: false,
            blocking: false,
          },
          canSubmit: false,
          submitDisabledReason: mapErrorMessage(code),
        });
        wx.showModal({
          title: "还不能提交",
          content: mapErrorMessage(code),
          confirmText: "去补充",
          success: (res) => {
            if (res.confirm) this.navigateOnce(supplementRoute);
          },
        });
      } else if (code === "already_submitted") {
        const readBack = await this.loadTask({ silent: true });
        if (readBack && isSubmitted(readBack)) {
          this.applyReviewState(readBack);
          this.setBusy("navigating", true);
          wx.redirectTo({
            url: "/pages/receipt/receipt",
            complete: () => this.setBusy("navigating", false),
          });
          return;
        }
        this.setData({
          errorState: {
            code,
            message: mapErrorMessage(code),
            retryable: false,
            blocking: false,
          },
          canSubmit: false,
          submitDisabledReason: mapErrorMessage(code),
        });
        wx.showToast({ title: mapErrorMessage(code), icon: "none" });
      } else {
        this.setData({
          errorState: {
            code,
            message: mapErrorMessage(code),
            retryable: true,
            blocking: false,
          },
        });
        wx.showToast({ title: mapErrorMessage(code), icon: "none" });
      }
    } finally {
      this.setBusy("submitting", false);
    }
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

  onLater() {
    if (this.isBusy("submitting")) return;
    wx.navigateBack({
      fail: () => {
        wx.redirectTo({ url: "/pages/task-home/task-home" });
      },
    });
  },
});
