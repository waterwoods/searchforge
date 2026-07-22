// P19M-1 — Unified Claim Mini Program Prototype
import { appConfig } from "./utils/config";
import { ensureCustomerSession } from "./services/sessionIdentityAdapter";
import { qaPathLog, summarizeLaunchQuery } from "./utils/qaPathLog";

type LaunchLike = {
  path?: string;
  scene?: number;
  query?: Record<string, unknown>;
};

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

App({
  globalData: {
    prototypeMode: true,
  },
  onLaunch(options: LaunchLike) {
    logPreviewLaunch("app.onLaunch", options);
    // Warm durable identity (wx.login → session). Never block launch on failure.
    void ensureCustomerSession().catch(() => undefined);
  },
  onShow(options: LaunchLike) {
    logPreviewLaunch("app.onShow", options);
  },
});
