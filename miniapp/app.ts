// P19M-1 — Unified Claim Mini Program Prototype
import { appConfig, devLog } from "./utils/config";
import { buildQaRuntimeDiagnostic } from "./utils/requestErrors";

App({
  globalData: {
    prototypeMode: true,
  },
  onLaunch() {
    // Prototype: no production wx.login / openid binding
    // QA-safe Preview identity — AppID/host only; never tokens/PII.
    devLog("[prototype] qa runtime", buildQaRuntimeDiagnostic({
      apiProfile: appConfig.apiProfile,
      apiBaseUrl: appConfig.apiBaseUrl,
    }));
  },
});
