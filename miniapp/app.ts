// P19M-1 — Unified Claim Mini Program Prototype
import { appConfig } from "./utils/config";
import { ensureCustomerSession } from "./services/sessionIdentityAdapter";
import { qaPathLog, summarizeLaunchQuery } from "./utils/qaPathLog";
import { resolveWarmDemoInviteRelaunchUrl } from "./utils/demoInviteLaunch";

type LaunchLike = {
  path?: string;
  scene?: number;
  query?: Record<string, unknown>;
};

/** Last Demo Invite dit force-handled this JS runtime (warm Preview reLaunch). */
let _lastHandledDemoInviteDit = "";

function logPreviewLaunch(source: string, options?: LaunchLike): void {
  try {
    let path = "";
    let scene = 0;
    let query: Record<string, unknown> = {};

    try {
      const sync =
        typeof wx !== "undefined" && typeof wx.getLaunchOptionsSync === "function"
          ? wx.getLaunchOptionsSync()
          : null;
      path = String((options && options.path) || (sync && sync.path) || "");
      scene = Number((options && options.scene) ?? (sync && sync.scene) ?? 0) || 0;
      query =
        (options && options.query) ||
        ((sync && sync.query) as Record<string, unknown>) ||
        {};
    } catch (_err) {
      path = String((options && options.path) || "");
    }

    const q = summarizeLaunchQuery(query);
    qaPathLog("LAUNCH", {
      source,
      path: path || "(unknown)",
      scene,
      queryKeys: q.queryKeys,
      queryRawSafe: q.queryRawSafe,
      hasToken: q.hasToken,
      apiProfile: appConfig.apiProfile,
      appPages0: "pages/start-claim/start-claim",
    });
  } catch (_err) {
    // Never block App / page registration on QA logging.
    console.info("[QA_PATH] LAUNCH", { source, path: "(log_failed)" });
  }
}

/**
 * Warm Preview / re-scan: if WeChat brings the Mini Program to foreground with a
 * new `dit=` while Case Status is still on the page stack, force reLaunch into
 * Start Claim so the new invite path is not ignored.
 *
 * Important: App.onShow `path` is the *enter* path (Preview QR), not the current
 * page — so we must not treat "path is start-claim" as proof the stack is clean.
 *
 * Isolated to Demo Invite `dit=` only — never bypasses Active Case after redeem.
 */
function maybeRelaunchForNewDemoInvite(source: "app.onLaunch" | "app.onShow", options?: LaunchLike): void {
  try {
    const enterQuery =
      (options && options.query) ||
      (typeof wx !== "undefined" && typeof wx.getEnterOptionsSync === "function"
        ? (wx.getEnterOptionsSync() || {}).query
        : undefined);
    const decision = resolveWarmDemoInviteRelaunchUrl({
      enterQuery: enterQuery as Record<string, unknown> | undefined,
      lastHandledDit: _lastHandledDemoInviteDit,
    });
    if (!decision.dit) return;

    // Cold start: pages[0]/compile path already loads with this dit. Track only
    // so the subsequent onShow does not double-reLaunch.
    if (source === "app.onLaunch") {
      _lastHandledDemoInviteDit = decision.dit;
      qaPathLog("LAUNCH", {
        source,
        phase: "demo_invite_dit_tracked_cold",
        hasDit: true,
      });
      return;
    }

    if (!decision.shouldRelaunch || !decision.url) return;

    _lastHandledDemoInviteDit = decision.dit;
    qaPathLog("LAUNCH", {
      source,
      phase: "demo_invite_warm_relaunch",
      hasDit: true,
      path: "pages/start-claim/start-claim",
    });
    wx.reLaunch({
      url: decision.url,
      fail: () => {
        wx.redirectTo({ url: decision.url });
      },
    });
  } catch (_err) {
    // Never block App lifecycle.
  }
}

App({
  globalData: {
    prototypeMode: true,
  },
  onLaunch(options: LaunchLike) {
    logPreviewLaunch("app.onLaunch", options);
    maybeRelaunchForNewDemoInvite("app.onLaunch", options);
    // Warm durable identity (wx.login → session). Never block launch on failure.
    void ensureCustomerSession().catch(() => undefined);
  },
  onShow(options: LaunchLike) {
    logPreviewLaunch("app.onShow", options);
    maybeRelaunchForNewDemoInvite("app.onShow", options);
  },
});
