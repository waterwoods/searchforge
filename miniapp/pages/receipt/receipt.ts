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
import {
  isSlice1CustomerFlow,
  mapSlice1CustomerView,
  REQUEST_ITEM_ROUTE,
  type Slice1CustomerView,
} from "../../utils/slice1Customer";
import { resolveCustomerConstitutionFromTask } from "../../utils/resolveCustomerConstitution";
import {
  OFFICE_PROCESSING_AFTER,
  OFFICE_PROCESSING_TITLE,
  isOfficeProcessingSurface,
} from "../../utils/customerCaseSurface";
import type { Slice1RequestItem } from "../../types/task";
import { reLaunchStartClaimHome } from "../../utils/startClaimEntry";

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
  /** False after office-materials accept — no primary customer task CTA. */
  showPrimaryTaskCta: boolean;
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
  slice1Enabled: boolean;
  slice1WaitingForBroker: boolean;
  slice1PrimaryLabel: string;
  slice1PrimaryActionable: boolean;
  slice1Instruction: string;
  slice1ProgressText: string;
  slice1QueuedItems: Slice1RequestItem[];
  slice1SatisfiedItems: Slice1RequestItem[];
  slice1LoadFailed: boolean;
};

function slice1PagePatch(view: Slice1CustomerView): Partial<PageData> {
  const focusInstruction = String(
    view.constitutionToday ||
      view.nextAction?.title ||
      view.constitutionWhy ||
      view.nextAction?.instructions ||
      "",
  );
  return {
    slice1Enabled: view.enabled,
    slice1WaitingForBroker: view.waitingForBroker,
    slice1PrimaryLabel: view.waitingForBroker
      ? "资料已提交，等待陈总审核"
      : view.primaryCtaLabel || "补充陈总需要的资料",
    slice1PrimaryActionable: view.primaryActionable,
    slice1Instruction: focusInstruction,
    slice1ProgressText:
      view.progress.total > 0 ? `进度 ${view.progress.satisfied}/${view.progress.total}` : "",
    slice1QueuedItems: view.queuedItems,
    slice1SatisfiedItems: view.satisfiedItems,
  };
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
    showPrimaryTaskCta: true,
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
    slice1Enabled: false,
    slice1WaitingForBroker: false,
    slice1PrimaryLabel: "",
    slice1PrimaryActionable: false,
    slice1Instruction: "",
    slice1ProgressText: "",
    slice1QueuedItems: [],
    slice1SatisfiedItems: [],
    slice1LoadFailed: false,
  } as PageData,

  async onLoad() {
    const task = await this.ensureTaskInitialized({ ownerLoad: true });
    if (task) {
      this.applyReceiptState(task);
      return;
    }
    if (this.data.errorState?.message) {
      this.safeSetData({ slice1LoadFailed: true });
    }
  },

  async onShow() {
    this.setBusy("navigating", false);
    if (consumeResumeRestoredHint()) {
      wx.showToast({
        title: "已恢复您上次填写的内容",
        icon: "none",
        duration: 2500,
      });
    }
    // Always re-load so resume/reload never shows a stale receipt.
    const task = await this.ensureTaskInitialized();
    if (task) {
      this.applyReceiptState(task);
      return;
    }
    if (this.data.errorState?.message) {
      this.safeSetData({ slice1LoadFailed: true });
    }
  },

  onUnload() {
    this.markTaskPageDestroyed();
  },

  onPullDownRefresh() {
    void this.rehydrateAuthoritativeTask()
      .then((task) => {
        if (task) this.applyReceiptState(task);
        else if (this.data.errorState?.message) {
          this.safeSetData({ slice1LoadFailed: true });
        }
      })
      .finally(() => wx.stopPullDownRefresh());
  },

  onRetry() {
    void this.retryLoadTask().then((task) => {
      if (task) {
        this.applyReceiptState(task);
        return;
      }
      if (this.data.errorState?.message) {
        this.safeSetData({ slice1LoadFailed: true });
      }
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
    const view = mapSlice1CustomerView(task);
    const summary = task.completion_summary;
    const dash = task.dashboard_summary;
    const submitted = isSubmitted(task);
    const broker = appConfig.brokerDisplayName;
    const submittedAt = formatSubmittedAt(
      String(task.task_contract?.timestamps?.updated_at || ""),
    );

    // Prefer server Constitution Focus/Trust only; otherwise keep prior receipt copy.
    const constitution = resolveCustomerConstitutionFromTask(task);
    const officeProcessing = isOfficeProcessingSurface(task);
    const serverToday =
      constitution.fieldAuthority.today === "server" ? constitution.today : "";
    const serverAfter =
      constitution.fieldAuthority.after === "server" ? constitution.after : "";
    const serverWhy =
      constitution.fieldAuthority.why === "server" ? constitution.why : "";
    const serverTrust =
      constitution.fieldAuthority.careLine === "server" ||
      constitution.fieldAuthority.careNote === "server"
        ? [constitution.careLine, constitution.careNote].filter(Boolean).join("。")
        : "";

    const nextStep = officeProcessing
      ? OFFICE_PROCESSING_AFTER
      : serverToday ||
        serverAfter ||
        (view.enabled
          ? view.waitingForBroker
            ? "资料已提交，等待陈总查看"
            : view.nextAction?.title ||
              view.nextAction?.instructions ||
              summary?.next_step ||
              dash?.next_action ||
              "请按陈总要求补充资料"
          : summary?.next_step ||
            dash?.next_action ||
            (submitted
              ? "已提交，等待陈总查看"
              : vm.cta.label || `等待${broker}查看`));

    const supplementHint = officeProcessing
      ? OFFICE_PROCESSING_AFTER
      : serverWhy ||
        (view.enabled
          ? view.waitingForBroker
            ? "资料已提交，等待陈总审核"
            : view.nextAction?.instructions ||
              view.nextAction?.title ||
              view.primaryCtaLabel ||
              ""
          : (task.missing_info || []).map((item) => item.label).filter(Boolean)[0] ||
            (vm.missingItems || []).map((item) => item.label).filter(Boolean)[0] ||
            (submitted ? "如有需要，可继续补充照片。" : ""));

    const supplementAllowed = officeProcessing
      ? false
      : view.enabled
        ? view.primaryActionable || view.waitingForBroker
        : Boolean(
            submitted || dash?.submitted_supplement_allowed || (task.missing_info || []).length > 0,
          );

    const brokerContactNote = officeProcessing
      ? OFFICE_PROCESSING_AFTER
      : serverTrust
        ? serverTrust
        : submitted
          ? `${broker}会尽快查看您提交的资料，并在需要时通过微信联系您。`
          : `如有问题，请通过微信联系${broker}。`;
    const materialsNote = supplementHint
      ? supplementHint
      : `如有需要，${broker}可能请您补充更多材料，请留意微信消息。`;

    const slice1Patch = slice1PagePatch(view);
    if (officeProcessing) {
      slice1Patch.slice1PrimaryLabel = OFFICE_PROCESSING_TITLE;
      slice1Patch.slice1PrimaryActionable = false;
      slice1Patch.slice1WaitingForBroker = true;
    }

    this.commitTaskViewModel(vm);
    this.safeSetData({
      task,
      title: officeProcessing
        ? OFFICE_PROCESSING_TITLE
        : summary?.title || (submitted ? "资料已提交" : vm.title || "当前状态"),
      message: officeProcessing
        ? OFFICE_PROCESSING_AFTER
        : summary?.message ||
          dash?.subtitle ||
          (submitted ? `已成功提交，${broker}会尽快处理。` : vm.instruction || ""),
      status: officeProcessing
        ? "办公室处理中"
        : view.enabled
          ? view.waitingForBroker
            ? "已提交"
            : "需补充材料"
          : dash?.status || vm.statusLabel || (submitted ? "已提交" : "进行中"),
      statusTone:
        view.enabled && !view.waitingForBroker && !officeProcessing
          ? "active"
          : submitted || vm.statusTone === "done" || officeProcessing
            ? "done"
            : "active",
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
      // Office-processing: no primary task CTA (footer hides via !showSupplement + wait).
      showSupplement: Boolean(
        officeProcessing
          ? false
          : view.enabled
            ? view.primaryActionable || view.waitingForBroker || submitted
            : supplementAllowed || (submitted && supplementHint),
      ),
      showPrimaryTaskCta: Boolean(submitted && !officeProcessing),
      supplementHint,
      errorState: EMPTY_TASK_ERROR,
      slice1LoadFailed: false,
      ...slice1Patch,
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
      url: "/pages/entry/entry",
      complete: () => this.setBusy("navigating", false),
      fail: () => {
        wx.navigateTo({
          url: "/pages/entry/entry",
          complete: () => this.setBusy("navigating", false),
        });
      },
    });
  },

  /**
   * Explicit Home / Start New Claim from Submit Result.
   * Active case → Service Home (preserves resume / Golden one-scan).
   * No active case → empty Start Claim form.
   */
  onBackHome() {
    if (this.isBusy("navigating")) return;
    this.setBusy("navigating", true);
    reLaunchStartClaimHome(wx);
    this.setBusy("navigating", false);
  },

  onViewAll() {
    const vm = this.data.taskViewModel;
    const lines: string[] = [];
    if (this.data.slice1Enabled) {
      if (this.data.slice1Instruction) lines.push(this.data.slice1Instruction);
      if (this.data.slice1ProgressText) lines.push(this.data.slice1ProgressText);
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

  /**
   * Receipt primary CTA.
   * Server Slice 1 projection is SSOT:
   * - active provide_fact / provide_evidence → route directly to request-item
   * - waiting for broker → toast, no legacy menu
   * - projection/load failure → retry, never silent legacy fallback
   * - legacy action sheet only when no active server-owned Slice 1 task
   */
  onEditSupplementInfo() {
    if (this.isBusy("navigating")) return;

    if (
      this.data.slice1LoadFailed
      || (this.data.errorState?.message && this.data.errorState.retryable)
    ) {
      void this.onRetry();
      return;
    }

    if (this.data.slice1Enabled || isSlice1CustomerFlow(this.data.task)) {
      if (this.data.slice1WaitingForBroker) {
        wx.showToast({ title: "资料已提交，等待陈总审核", icon: "none" });
        return;
      }
      if (this.data.slice1PrimaryActionable) {
        this.navigateOnce(REQUEST_ITEM_ROUTE);
        return;
      }
      this.onContactBroker();
      return;
    }

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
        this.navigateOnce(route);
      },
    });
  },

  navigateOnce(route: string) {
    if (!route || this.isBusy("navigating")) return;
    this.setBusy("navigating", true);
    wx.navigateTo({
      url: route,
      complete: () => this.setBusy("navigating", false),
    });
  },
});

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
