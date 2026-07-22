import assert from "node:assert/strict";
import test from "node:test";

import { installMiniProgramGlobals, resetMiniProgramCaptures } from "./miniprogramMocks";

installMiniProgramGlobals();

async function withCleanIdentity(run: () => Promise<void>): Promise<void> {
  resetMiniProgramCaptures();
  installMiniProgramGlobals();
  const { resetApiHealthCache } = await import("../utils/apiHealth");
  resetApiHealthCache();
  const { clearCustomerIdentityForTests } = await import("../services/sessionIdentityAdapter");
  clearCustomerIdentityForTests();
  try {
    await run();
  } finally {
    clearCustomerIdentityForTests();
    resetApiHealthCache();
  }
}

test("prototype anon fallback is blocked against Production API", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = configMod.PRODUCTION_API_BASE_URL;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const { allowPrototypeAnonFallback, isProductionApiTarget } = await import(
      "../services/sessionIdentityAdapter"
    );
    assert.equal(isProductionApiTarget(), true);
    assert.equal(allowPrototypeAnonFallback(), false);

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("Scenario A — session Active Case saves resume (Home Continue)", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
      opts?.success?.({ code: "sim:adapter-active" });
    };
    wx.request = (opts: {
      url: string;
      success?: (res: { statusCode: number; data: unknown }) => void;
    }) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) {
        opts.success?.({ statusCode: 200, data: { ok: true } });
        return;
      }
      if (url.includes("/customer/session")) {
        opts.success?.({
          statusCode: 200,
          data: {
            ok: true,
            session_id: "wx_adapteractivecase01",
            has_active_case: true,
            resume_token: "h5t1.adapter-resume",
            resume_expires_at: "2099-01-01T00:00:00Z",
          },
        });
        return;
      }
      opts.success?.({ statusCode: 500, data: { detail: "unexpected" } });
    };

    const { ensureCustomerSession } = await import("../services/sessionIdentityAdapter");
    const { loadResumeToken } = await import("../utils/storage");
    const session = await ensureCustomerSession();
    assert.equal(session.hasActiveCase, true);
    assert.equal(session.authoritySource, "customer_session");
    assert.equal(loadResumeToken(), "h5t1.adapter-resume");

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("Scenario B — session has_active_case false clears stale resume", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const { saveResumeToken, loadResumeToken } = await import("../utils/storage");
    saveResumeToken("h5t1.stale-after-close");

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
      opts?.success?.({ code: "sim:adapter-closed" });
    };
    wx.request = (opts: {
      url: string;
      success?: (res: { statusCode: number; data: unknown }) => void;
    }) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) {
        opts.success?.({ statusCode: 200, data: { ok: true } });
        return;
      }
      if (url.includes("/customer/session")) {
        opts.success?.({
          statusCode: 200,
          data: {
            ok: true,
            session_id: "wx_adapterclosedcase01",
            has_active_case: false,
          },
        });
        return;
      }
      opts.success?.({ statusCode: 500, data: { detail: "unexpected" } });
    };

    const { ensureCustomerSession, applyServerActiveCaseAuthority } = await import(
      "../services/sessionIdentityAdapter"
    );
    const cleared = applyServerActiveCaseAuthority({ has_active_case: false });
    assert.equal(cleared.hasActiveCase, false);
    assert.equal(loadResumeToken(), "");

    saveResumeToken("h5t1.stale-after-close");
    const session = await ensureCustomerSession();
    assert.equal(session.hasActiveCase, false);
    assert.equal(loadResumeToken(), "");

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("Scenario C — cleared storage + server Active restores Continue", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const { clearResumeToken, loadResumeToken } = await import("../utils/storage");
    clearResumeToken();
    assert.equal(loadResumeToken(), "");

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
      opts?.success?.({ code: "sim:adapter-restore" });
    };
    wx.request = (opts: {
      url: string;
      success?: (res: { statusCode: number; data: unknown }) => void;
    }) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) {
        opts.success?.({ statusCode: 200, data: { ok: true } });
        return;
      }
      if (url.includes("/customer/session")) {
        opts.success?.({
          statusCode: 200,
          data: {
            ok: true,
            session_id: "wx_adapterrestorecase01",
            has_active_case: true,
            resume_token: "h5t1.restored-from-server",
            resume_expires_at: "2099-01-01T00:00:00Z",
          },
        });
        return;
      }
      opts.success?.({ statusCode: 500, data: { detail: "unexpected" } });
    };

    const { ensureCustomerSession } = await import("../services/sessionIdentityAdapter");
    const session = await ensureCustomerSession();
    assert.equal(session.hasActiveCase, true);
    assert.equal(loadResumeToken(), "h5t1.restored-from-server");

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("Scenario D — cleared storage + server no Active → Start Claim", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const { clearResumeToken, loadResumeToken } = await import("../utils/storage");
    clearResumeToken();

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
      opts?.success?.({ code: "sim:adapter-empty" });
    };
    wx.request = (opts: {
      url: string;
      success?: (res: { statusCode: number; data: unknown }) => void;
    }) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) {
        opts.success?.({ statusCode: 200, data: { ok: true } });
        return;
      }
      if (url.includes("/customer/session")) {
        opts.success?.({
          statusCode: 200,
          data: { ok: true, session_id: "wx_adapteremptycase01", has_active_case: false },
        });
        return;
      }
      opts.success?.({ statusCode: 500, data: { detail: "unexpected" } });
    };

    const { ensureCustomerSession } = await import("../services/sessionIdentityAdapter");
    const session = await ensureCustomerSession();
    assert.equal(session.hasActiveCase, false);
    assert.equal(loadResumeToken(), "");

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("Scenario E — session fail + closed History resume clears Continue", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const { saveResumeToken, loadResumeToken } = await import("../utils/storage");
    saveResumeToken("h5t1.closed-history-token");

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
      opts?.success?.({ code: "sim:will-fail-session" });
    };
    wx.request = (opts: {
      url: string;
      success?: (res: { statusCode: number; data: unknown }) => void;
      fail?: (err: { errMsg: string }) => void;
    }) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) {
        opts.success?.({ statusCode: 200, data: { ok: true } });
        return;
      }
      if (url.includes("/customer/session")) {
        opts.success?.({ statusCode: 503, data: { detail: "wechat_mp_not_configured" } });
        return;
      }
      if (url.includes("/tasks/") && url.includes("/intake")) {
        opts.success?.({
          statusCode: 200,
          data: {
            case_id: "case_closed",
            case_status: "closed",
            case_history_state: "history",
            case_closed_read_only: true,
          },
        });
        return;
      }
      opts.success?.({ statusCode: 500, data: { detail: "unexpected" } });
    };

    const { ensureCustomerSession } = await import("../services/sessionIdentityAdapter");
    const session = await ensureCustomerSession();
    assert.equal(session.hasActiveCase, false);
    assert.equal(session.authoritySource, "none");
    assert.equal(loadResumeToken(), "");

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("session fail + open case resume keeps Continue (QA WeChat gap)", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const { saveResumeToken, loadResumeToken } = await import("../utils/storage");
    saveResumeToken("h5t1.open-case-token");

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { fail?: () => void }) => {
      opts?.fail?.();
    };
    wx.request = (opts: {
      url: string;
      success?: (res: { statusCode: number; data: unknown }) => void;
      fail?: (err: { errMsg: string }) => void;
    }) => {
      const url = String(opts.url || "");
      if (url.includes("/health/live")) {
        opts.success?.({ statusCode: 200, data: { ok: true } });
        return;
      }
      if (url.includes("/customer/session")) {
        opts.success?.({ statusCode: 503, data: { detail: "wechat_mp_not_configured" } });
        return;
      }
      if (url.includes("/tasks/") && url.includes("/intake")) {
        opts.success?.({
          statusCode: 200,
          data: {
            case_id: "case_open",
            case_status: "reviewing",
            case_closed_read_only: false,
          },
        });
        return;
      }
      opts.fail?.({ errMsg: "request:fail" });
    };

    const { ensureCustomerSession } = await import("../services/sessionIdentityAdapter");
    const session = await ensureCustomerSession();
    assert.equal(session.hasActiveCase, true);
    assert.equal(session.authoritySource, "resume_reconcile");
    assert.equal(loadResumeToken(), "h5t1.open-case-token");

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});
