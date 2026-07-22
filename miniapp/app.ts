// P19M-1 — Unified Claim Mini Program Prototype
import { appConfig } from "./utils/config";
import { qaPathLog, summarizeLaunchQuery } from "./utils/qaPathLog";

function logPreviewLaunch(source: string, options?: WechatMiniprogram.LaunchShowOption | Record<string, unknown>): void {
  let path = "";
  let scene = 0;
  let query: Record<string, unknown> | string = {};

  try {
    const sync =
      typeof wx !== "undefined" && typeof wx.getLaunchOptionsSync === "function"
        ? wx.getLaunchOptionsSync()
        : null;
    path = String((options as { path?: string })?.path || sync?.path || "");
    scene = Number((options as { scene?: number })?.scene ?? sync?.scene ?? 0) || 0;
    query =
      ((options as { query?: Record<string, unknown> })?.query as Record<string, unknown>) ||
      (sync?.query as Record<string, unknown>) ||
      {};
  } catch {
    path = String((options as { path?: string })?.path || "");
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
    // Prove which compile/default root WeChat opened — not an API call.
    appPages0: "pages/start-claim/start-claim",
  });
}

App({
  globalData: {
    prototypeMode: true,
  },
  onLaunch(options: WechatMiniprogram.App.LaunchShowOption) {
    // Prototype: no production wx.login / openid binding
    logPreviewLaunch("app.onLaunch", options);
  },
  onShow(options: WechatMiniprogram.App.LaunchShowOption) {
    logPreviewLaunch("app.onShow", options);
  },
});
