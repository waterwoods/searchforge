/**
 * Lightweight Service Home — product entrance (Home ≠ Task Home).
 *
 * Continue / Start Claim UI is server-authoritative via Customer Context.
 * Never fail-open into Start Claim before / without a successful context read.
 */

import { appConfig } from "../../utils/config";
import { resolveCustomerContext } from "../../services/sessionIdentityAdapter";
import { resetApiHealthCache } from "../../utils/apiHealth";
import {
  ENTRY_ROUTE,
  ONE_ACTIVE_CASE_POLICY_CONTACT,
  ONE_ACTIVE_CASE_POLICY_CONTENT,
  ONE_ACTIVE_CASE_POLICY_CONTINUE,
  ONE_ACTIVE_CASE_POLICY_TITLE,
  reLaunchEmptyStartClaimForm,
} from "../../utils/startClaimEntry";
import { buildServiceHomeViewModel } from "../../utils/serviceHome";
import { contactBrokerModalCopy } from "../../utils/taskMapping";

type HomePhase = "checking" | "ready" | "error";

type PageData = ReturnType<typeof buildServiceHomeViewModel> & {
  /** Last server-authoritative Active Case decision for this Home show. */
  serverHasActiveCase: boolean | null;
  homePhase: HomePhase;
  contextErrorMessage: string;
};

function brandFromConfig(): string {
  return String(appConfig.tenantDisplayName || "陈总保险办公室").trim() || "陈总保险办公室";
}

function brokerFromConfig(): string {
  return String(appConfig.brokerDisplayName || "陈总").trim() || "陈总";
}

Page({
  data: {
    ...buildServiceHomeViewModel(false, {
      brandTitle: brandFromConfig(),
      brokerName: brokerFromConfig(),
    }),
    serverHasActiveCase: null,
    homePhase: "checking",
    contextErrorMessage: "",
  } as PageData,

  /**
   * Apply Home cards only after a successful Customer Context read.
   */
  applyHomeAuthority(hasActive: boolean) {
    const vm = buildServiceHomeViewModel(hasActive, {
      brandTitle: brandFromConfig(),
      brokerName: brokerFromConfig(),
    });
    this.setData({
      ...vm,
      serverHasActiveCase: hasActive,
      homePhase: "ready",
      contextErrorMessage: "",
    });
  },

  showContextError() {
    this.setData({
      homePhase: "error",
      serverHasActiveCase: null,
      hasActiveSession: false,
      contextErrorMessage: "请重试，或直接联系陈总。",
    });
  },

  onShow() {
    // Neutral checking shell only — never Start Claim until context succeeds.
    this.setData({
      homePhase: "checking",
      serverHasActiveCase: null,
      hasActiveSession: false,
      contextErrorMessage: "",
    });
    void this.syncIdentityAndRefresh();
  },

  async syncIdentityAndRefresh() {
    try {
      const context = await resolveCustomerContext();
      this.applyHomeAuthority(context.hasActiveCase);
    } catch {
      this.showContextError();
    }
  },

  onRetryContext() {
    resetApiHealthCache();
    this.setData({
      homePhase: "checking",
      contextErrorMessage: "",
    });
    void this.syncIdentityAndRefresh();
  },

  /** Continue / View Progress → Entry → Task Home or Case Status (system decides). */
  onContinueCurrentClaim() {
    if (this.data.homePhase !== "ready" || !this.data.hasActiveSession) {
      return;
    }
    wx.reLaunch({
      url: ENTRY_ROUTE,
      fail: () => {
        wx.redirectTo({ url: ENTRY_ROUTE });
      },
    });
  },

  onViewProgress() {
    this.onContinueCurrentClaim();
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

  /**
   * P30 One Active Case:
   * - No Active Case → Start Claim form
   * - Active Case → policy modal (continue / contact); never clear resume / never second case
   */
  onStartNewClaim() {
    if (this.data.homePhase !== "ready") {
      return;
    }
    if (this.data.hasActiveSession) {
      this.showOneActiveCasePolicy();
      return;
    }
    reLaunchEmptyStartClaimForm(wx);
  },

  showOneActiveCasePolicy() {
    wx.showModal({
      title: ONE_ACTIVE_CASE_POLICY_TITLE,
      content: ONE_ACTIVE_CASE_POLICY_CONTENT,
      confirmText: ONE_ACTIVE_CASE_POLICY_CONTINUE,
      cancelText: ONE_ACTIVE_CASE_POLICY_CONTACT,
      success: (res) => {
        if (res.confirm) {
          this.onContinueCurrentClaim();
          return;
        }
        if (res.cancel) {
          this.onContactBroker();
        }
      },
      fail: () => {
        // Modal failure must not open a second-case create path.
        this.onContinueCurrentClaim();
      },
    });
  },
});
