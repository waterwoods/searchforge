import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { CONTINUE_CLAIM_TITLE, START_CLAIM_PRIMARY_TITLE, START_NEW_CLAIM_LABEL } from "../utils/serviceHome";
import { clearResumeToken, loadResumeToken, saveResumeToken } from "../utils/storage";

installMiniProgramGlobals();

type CapturedPageOptions = {
  data: Record<string, unknown>;
  [key: string]: any;
};

let cachedPage: CapturedPageOptions | null = null;

async function loadServiceHomePage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/service-home/service-home");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

function createPageContext(page: CapturedPageOptions) {
  const data = { ...(page.data || {}) } as Record<string, any>;
  const ctx: Record<string, any> = {
    ...page,
    route: "/pages/service-home/service-home",
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(data, patch);
      this.data = data;
    },
  };
  return ctx;
}

async function withHomeEnv(run: () => Promise<void>): Promise<void> {
  installMiniProgramGlobals();
  const { resetApiHealthCache } = await import("../utils/apiHealth");
  resetApiHealthCache();
  const { clearCustomerIdentityForTests } = await import("../services/sessionIdentityAdapter");
  clearCustomerIdentityForTests();
  const configMod = await import("../utils/config");
  const originalBase = configMod.appConfig.apiBaseUrl;
  const originalProto = configMod.appConfig.prototypeMode;
  (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = "http://127.0.0.1:8001";
  (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = true;
  try {
    await run();
  } finally {
    clearCustomerIdentityForTests();
    resetApiHealthCache();
    (configMod.appConfig as { apiBaseUrl: string }).apiBaseUrl = originalBase;
    (configMod.appConfig as { prototypeMode: boolean }).prototypeMode = originalProto;
  }
}

function wireSession(
  wx: Record<string, any>,
  sessionBody: Record<string, unknown>,
  intakeBody?: Record<string, unknown>,
) {
  wx.login = (opts?: { success?: (res: { code: string }) => void }) => {
    opts?.success?.({ code: "sim:service-home" });
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
      opts.success?.({ statusCode: 200, data: sessionBody });
      return;
    }
    if (url.includes("/tasks/") && url.includes("/intake") && intakeBody) {
      opts.success?.({ statusCode: 200, data: intakeBody });
      return;
    }
    opts.success?.({ statusCode: 500, data: { detail: "unexpected" } });
  };
}

test("Scenario A — Home shows Continue after server Active session", async () => {
  await withHomeEnv(async () => {
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homeactive0001",
      has_active_case: true,
      resume_token: "h5t1.home-active",
      resume_expires_at: "2099-01-01T00:00:00Z",
    });
    const ctx = createPageContext(page);
    page.onShow.call(ctx);
    assert.equal(ctx.data.hasActiveSession, false); // shell first
    await page.syncIdentityAndRefresh.call(ctx);
    assert.equal(ctx.data.hasActiveSession, true);
    assert.equal(ctx.data.continueTitle, CONTINUE_CLAIM_TITLE);
    assert.equal(ctx.data.startNewClaimLabel, START_NEW_CLAIM_LABEL);
    assert.equal(loadResumeToken(), "h5t1.home-active");
  });
});

test("Scenario B — Broker Close → session false → Home Start Claim", async () => {
  await withHomeEnv(async () => {
    saveResumeToken("h5t1.stale-closed");
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homeclosed0001",
      has_active_case: false,
    });
    const ctx = createPageContext(page);
    page.onShow.call(ctx);
    await page.syncIdentityAndRefresh.call(ctx);
    assert.equal(ctx.data.hasActiveSession, false);
    assert.equal(ctx.data.startClaimTitle, START_CLAIM_PRIMARY_TITLE);
    assert.equal(loadResumeToken(), "");
  });
});

test("Scenario C — clear storage + server Active → Continue", async () => {
  await withHomeEnv(async () => {
    clearResumeToken();
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homerestore0001",
      has_active_case: true,
      resume_token: "h5t1.home-restored",
      resume_expires_at: "2099-01-01T00:00:00Z",
    });
    const ctx = createPageContext(page);
    await page.syncIdentityAndRefresh.call(ctx);
    assert.equal(ctx.data.hasActiveSession, true);
    assert.equal(loadResumeToken(), "h5t1.home-restored");
  });
});

test("Scenario D — clear storage + server no Active → Start Claim", async () => {
  await withHomeEnv(async () => {
    clearResumeToken();
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homeempty0001",
      has_active_case: false,
    });
    const ctx = createPageContext(page);
    await page.syncIdentityAndRefresh.call(ctx);
    assert.equal(ctx.data.hasActiveSession, false);
    assert.equal(loadResumeToken(), "");
  });
});

test("Scenario E — restart Home matches server (stale cache discarded)", async () => {
  await withHomeEnv(async () => {
    saveResumeToken("h5t1.should-be-cleared");
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homerestart0001",
      has_active_case: false,
    });
    const ctx = createPageContext(page);
    page.onShow.call(ctx);
    await page.syncIdentityAndRefresh.call(ctx);
    assert.equal(ctx.data.hasActiveSession, false);
    assert.equal(loadResumeToken(), "");
  });
});

test("Continue Current Claim relaunches Entry when server Active", async () => {
  await withHomeEnv(async () => {
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homecontinue01",
      has_active_case: true,
      resume_token: "h5t1.continue",
      resume_expires_at: "2099-01-01T00:00:00Z",
    });
    const launches: string[] = [];
    wx.reLaunch = ({ url }: { url: string }) => {
      launches.push(url);
    };
    const ctx = createPageContext(page);
    await page.syncIdentityAndRefresh.call(ctx);
    page.onContinueCurrentClaim.call(ctx);
    assert.deepEqual(launches, ["/pages/entry/entry"]);
    assert.equal(loadResumeToken(), "h5t1.continue");
  });
});

test("Start New Claim with Active shows policy and does not clear resume", async () => {
  await withHomeEnv(async () => {
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homepolicy0001",
      has_active_case: true,
      resume_token: "h5t1.policy",
      resume_expires_at: "2099-01-01T00:00:00Z",
    });
    const launches: string[] = [];
    const modals: Array<Record<string, unknown>> = [];
    wx.reLaunch = ({ url }: { url: string }) => {
      launches.push(url);
    };
    wx.showModal = (opts: Record<string, unknown>) => {
      modals.push(opts);
    };
    const ctx = createPageContext(page);
    await page.syncIdentityAndRefresh.call(ctx);
    page.onStartNewClaim.call(ctx);
    assert.equal(modals.length, 1);
    assert.match(String(modals[0]?.title || ""), /正在处理的报案/);
    assert.deepEqual(launches, []);
    assert.equal(loadResumeToken(), "h5t1.policy");
  });
});

test("Start New Claim without Active opens Start Claim form", async () => {
  await withHomeEnv(async () => {
    clearResumeToken();
    const page = await loadServiceHomePage();
    const wx = (globalThis as { wx: Record<string, any> }).wx;
    wireSession(wx, {
      ok: true,
      session_id: "wx_homestart0001",
      has_active_case: false,
    });
    const launches: string[] = [];
    wx.reLaunch = ({ url }: { url: string }) => {
      launches.push(url);
    };
    const ctx = createPageContext(page);
    await page.syncIdentityAndRefresh.call(ctx);
    assert.equal(ctx.data.hasActiveSession, false);
    page.onStartNewClaim.call(ctx);
    assert.deepEqual(launches, ["/pages/start-claim/start-claim?entry=form"]);
  });
});
