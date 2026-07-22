import assert from "node:assert/strict";
import test from "node:test";

import { installMiniProgramGlobals, resetMiniProgramCaptures } from "./miniprogramMocks";

installMiniProgramGlobals();

async function withCleanIdentity(
  run: () => Promise<void>,
): Promise<void> {
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

    const {
      allowPrototypeAnonFallback,
      isProductionApiTarget,
    } = await import("../services/sessionIdentityAdapter");
    assert.equal(isProductionApiTarget(), true);
    assert.equal(allowPrototypeAnonFallback(), false);

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("local prototype allows anon fallback when durable login fails", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { fail?: () => void }) => {
      opts?.fail?.();
    };
    wx.request = (opts: {
      url?: string;
      fail?: (err: { errMsg: string }) => void;
    }) => {
      opts.fail?.({ errMsg: "request:fail" });
    };

    const { ensureCustomerSession } = await import("../services/sessionIdentityAdapter");
    const session = await ensureCustomerSession();
    assert.equal(session.identitySource, "prototype_anon");
    assert.ok(session.sessionId.startsWith("anon-"));

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});

test("durable session persists wx_* id and resume token from server", async () => {
  await withCleanIdentity(async () => {
    const configMod = await import("../utils/config");
    const originalBase = configMod.appConfig.apiBaseUrl;
    const originalProto = configMod.appConfig.prototypeMode;
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;

    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
      opts?.success?.({ code: "sim:adapter-test" });
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
            session_id: "wx_adaptertestdurable01",
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
    const { loadCustomerSessionId, loadResumeToken } = await import("../utils/storage");
    const session = await ensureCustomerSession();
    assert.equal(session.identitySource, "durable");
    assert.equal(session.sessionId, "wx_adaptertestdurable01");
    assert.equal(session.hasActiveCase, true);
    assert.equal(loadCustomerSessionId(), "wx_adaptertestdurable01");
    assert.equal(loadResumeToken(), "h5t1.adapter-resume");

    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  });
});
