/**
 * Lightweight Service Home — product entrance (Home ≠ Task Home).
 *
 * Continue / Start Claim UI is server-authoritative via ensureCustomerSession()
 * (/customer/session). Local resume token is cache only.
 */

import { appConfig } from "../../utils/config";
import { ensureCustomerSession } from "../../services/sessionIdentityAdapter";
import {
  ENTRY_ROUTE,
  ONE_ACTIVE_CASE_POLICY_CONTACT,
  ONE_ACTIVE_CASE_POLICY_CONTENT,
  ONE_ACTIVE_CASE_POLICY_CONTINUE,
  ONE_ACTIVE_CASE_POLICY_TITLE,
  hasActiveCustomerCase,
  reLaunchEmptyStartClaimForm,
} from "../../utils/startClaimEntry";
import { buildServiceHomeViewModel } from "../../utils/serviceHome";
import { contactBrokerModalCopy } from "../../utils/taskMapping";

type PageData = ReturnType<typeof buildServiceHomeViewModel> & {
  /** Last server-authoritative Active Case decision for this Home show. */
  serverHasActiveCase: boolean | null;
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
  } as PageData,

  /**
   * Apply Home cards from server authority (preferred) or post-sync cache.
   * Never invent Continue from an unsynced local token after a failed authority path
   * that already cleared storage.
   */
  applyHomeAuthority(hasActive: boolean) {
    const vm = buildServiceHomeViewModel(hasActive, {
      brandTitle: brandFromConfig(),
      brokerName: brokerFromConfig(),
    });
    this.setData({
      ...vm,
      serverHasActiveCase: hasActive,
    });
  },

  onShow() {
    // Shell first (North Star §J): default Start Claim until server authority returns.
    this.applyHomeAuthority(false);
    void this.syncIdentityAndRefresh();
  },

  async syncIdentityAndRefresh() {
    try {
      const session = await ensureCustomerSession();
      // Server (or closed-case reconcile) decides — not raw storage alone.
      this.applyHomeAuthority(Boolean(session.hasActiveCase));
    } catch {
      // Durable identity hard-fail: show Start Claim (fail closed for Continue).
      this.applyHomeAuthority(false);
    }
  },

  /** Continue / View Progress → Entry → Task Home or Case Status (system decides). */
  onContinueCurrentClaim() {
    if (!this.data.hasActiveSession || !hasActiveCustomerCase()) {
      this.applyHomeAuthority(false);
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
    if (this.data.hasActiveSession && hasActiveCustomerCase()) {
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
