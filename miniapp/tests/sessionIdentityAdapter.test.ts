import assert from "node:assert/strict";
import test from "node:test";

import { installMiniProgramGlobals } from "./miniprogramMocks";

installMiniProgramGlobals();

async function withIdentityApi(
  contextBody: Record<string, unknown>,
  run: () => Promise<void>,
): Promise<void> {
  installMiniProgramGlobals();
  const config = await import("../utils/config");
  const originalBase = config.appConfig.apiBaseUrl;
  const originalPrototype = config.appConfig.prototypeMode;
  (config.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
  (config.appConfig as { prototypeMode: boolean }).prototypeMode = true;
  const wx = (globalThis as { wx: Record<string, any> }).wx;
  wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
    opts?.success?.({ code: "sim:customer-context" });
  };
  wx.request = (opts: { url: string; success?: (res: { statusCode: number; data: unknown }) => void }) => {
    if (opts.url.includes("/health/live")) {
      opts.success?.({ statusCode: 200, data: { ok: true } });
    } else if (opts.url.includes("/customer/session")) {
      opts.success?.({ statusCode: 200, data: { ok: true, session_id: "wx_context_session_01" } });
    } else if (opts.url.includes("/customer/context")) {
      opts.success?.({ statusCode: 200, data: contextBody });
    } else {
      opts.success?.({ statusCode: 500, data: { detail: "unexpected" } });
    }
  };
  try {
    await run();
  } finally {
    (config.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (config.appConfig as { prototypeMode: boolean }).prototypeMode = originalPrototype;
  }
}

test("identity establishment does not decide Active Case", async () => {
  await withIdentityApi({ has_active_case: false, next_action: "START_NEW_CLAIM" }, async () => {
    const { ensureCustomerSession } = await import("../services/sessionIdentityAdapter");
    const session = await ensureCustomerSession();
    assert.equal(session.sessionId, "wx_context_session_01");
    assert.equal("hasActiveCase" in session, false);
  });
});

test("Customer Context alone updates the resume cache and next action", async () => {
  await withIdentityApi(
    {
      has_active_case: true,
      resume_token: "h5t1.context-authority",
      resume_expires_at: "2099-01-01T00:00:00Z",
      next_action: "UPLOAD_REQUEST_ITEM",
    },
    async () => {
      const { resolveCustomerContext } = await import("../services/sessionIdentityAdapter");
      const { loadResumeToken } = await import("../utils/storage");
      const context = await resolveCustomerContext();
      assert.equal(context.nextAction, "UPLOAD_REQUEST_ITEM");
      assert.equal(context.hasActiveCase, true);
      assert.equal(loadResumeToken(), "h5t1.context-authority");
    },
  );
});

test("Customer Context clears stale cached resume when no Active Case exists", async () => {
  await withIdentityApi({ has_active_case: false, next_action: "START_NEW_CLAIM" }, async () => {
    const { saveResumeToken, loadResumeToken } = await import("../utils/storage");
    const { resolveCustomerContext } = await import("../services/sessionIdentityAdapter");
    saveResumeToken("h5t1.stale-cache");
    const context = await resolveCustomerContext();
    assert.equal(context.nextAction, "START_NEW_CLAIM");
    assert.equal(loadResumeToken(), "");
  });
});
