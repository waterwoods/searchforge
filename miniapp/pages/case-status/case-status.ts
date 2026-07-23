/**
 * D-014 Case Status — Waiting Broker surface (not a fake Task Home).
 *
 * Rehydrates on show so Broker Request More flips this page to Task Home
 * without a second QR / token change.
 */

import { taskPage } from "../../behaviors/taskPage";
import { qaPathLog, summarizeLaunchQuery } from "../../utils/qaPathLog";
import { contactBrokerModalCopy } from "../../utils/taskMapping";
import {
  EMPTY_TASK_ERROR,
  DEFAULT_SAFETY_COPY,
} from "../../utils/resolveTaskViewModel";
import {
  CASE_STATUS_BODY_LINES,
  CASE_STATUS_TITLE,
  TASK_HOME_ROUTE,
  buildCaseStatusViewModel,
  canVoluntarySupplement,
  customerOwesWork,
  type CaseStatusViewModel,
} from "../../utils/customerCaseSurface";
import type { CustomerTask } from "../../types/task";

type PageData = CaseStatusViewModel & {
  loadingMessage: string;
  errorState: typeof EMPTY_TASK_ERROR;
  busy: {
    loading: boolean;
    saving: boolean;
    uploading: boolean;
    submitting: boolean;
    navigating: boolean;
    retrying: boolean;
  };
  shellSafetyCopy: string;
  showVoluntarySupplement: boolean;
};

function emptyStatus(): CaseStatusViewModel {
  return {
    title: CASE_STATUS_TITLE,
    bodyLines: [...CASE_STATUS_BODY_LINES],
    why: "",
    after: "",
    statusLabel: "审核中",
    lastSubmittedLines: [],
    completedLines: [],
    careLine: "",
    careNote: "",
  };
}

Page({
  behaviors: [taskPage],
  data: {
    loadingMessage: "正在加载案件状态…",
    errorState: EMPTY_TASK_ERROR,
    busy: {
      loading: true,
      saving: false,
      uploading: false,
      submitting: false,
      navigating: false,
      retrying: false,
    },
    shellSafetyCopy: DEFAULT_SAFETY_COPY,
    showVoluntarySupplement: false,
    ...emptyStatus(),
  } as PageData,

  onLoad(options: Record<string, string | undefined>) {
    const q = summarizeLaunchQuery(options || {});
    qaPathLog("ENTRY", {
      page: "pages/case-status/case-status",
      queryKeys: q.queryKeys,
      queryRawSafe: q.queryRawSafe,
      hasToken: q.hasToken,
      note: "waiting_broker_case_status",
    });
    void this.ensureTaskInitialized({ ownerLoad: true }).then((task) => {
      this.applyStatusOrRedirect(task);
    });
  },

  onShow() {
    this.setBusy("navigating", false);
    void this.ensureTaskInitialized().then((task) => {
      this.applyStatusOrRedirect(task);
    });
  },

  onUnload() {
    this.markTaskPageDestroyed();
  },

  onPullDownRefresh() {
    void this.rehydrateAuthoritativeTask()
      .then((task) => {
        this.applyStatusOrRedirect(task);
      })
      .finally(() => wx.stopPullDownRefresh());
  },

  applyStatusOrRedirect(task: CustomerTask | null | undefined) {
    if (!task) return;
    // Request More / new work → leave Waiting surface for Task Home.
    if (customerOwesWork(task)) {
      if (this.isBusy("navigating")) return;
      this.setBusy("navigating", true);
      wx.reLaunch({
        url: TASK_HOME_ROUTE,
        complete: () => this.setBusy("navigating", false),
        fail: () => {
          wx.redirectTo({
            url: TASK_HOME_ROUTE,
            complete: () => this.setBusy("navigating", false),
          });
        },
      });
      return;
    }
    const vm = buildCaseStatusViewModel(task);
    this.setData({
      ...vm,
      // Never show retired wait-today copy as the page title.
      title: CASE_STATUS_TITLE,
      showVoluntarySupplement: canVoluntarySupplement(task),
    });
  },

  onRetry() {
    void this.retryLoadTask().then((task) => {
      this.applyStatusOrRedirect(task);
    });
  },

  onViewSubmitted() {
    const lines = this.data.completedLines.length
      ? this.data.completedLines
      : this.data.lastSubmittedLines;
    wx.showModal({
      title: "已提交资料",
      content: lines.length ? lines.join("\n") : "暂无已提交明细，陈总已收到您的资料。",
      showCancel: false,
      confirmText: "知道了",
    });
  },

  /**
   * Voluntary append (D-014 Commit 2): same Active Case / resume token.
   * Photos append-first; short note via Story. Never creates a second case.
   */
  onVoluntarySupplement() {
    if (!this.data.showVoluntarySupplement || this.isBusy("navigating")) return;
    wx.showActionSheet({
      itemList: ["补充照片", "补充说明"],
      success: (res) => {
        const routes = ["/pages/photos/photos", "/pages/story/story"];
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
      fail: () => {
        wx.redirectTo({
          url: route,
          complete: () => this.setBusy("navigating", false),
        });
      },
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
