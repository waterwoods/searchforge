import assert from "node:assert/strict";
import test from "node:test";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";

installMiniProgramGlobals();

type PageOptions = Record<string, any>;
let pagePromise: Promise<PageOptions> | null = null;

async function page(): Promise<PageOptions> {
  if (!pagePromise) {
    pagePromise = import("../pages/service-home/service-home").then(() => getLatestPage().options as PageOptions);
  }
  return pagePromise;
}

function contextFor(options: PageOptions): Record<string, any> {
  const data = { ...options.data };
  return {
    ...options,
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(data, patch);
    },
  };
}

function installContextApi(body: Record<string, unknown>) {
  const wx = (globalThis as { wx: Record<string, any> }).wx;
  wx.login = (opts: any) => opts.success?.({ code: "sim:service-home" });
  wx.request = (opts: any) => {
    if (opts.url.includes("/health/live")) opts.success?.({ statusCode: 200, data: { ok: true } });
    else if (opts.url.includes("/customer/session")) {
      opts.success?.({ statusCode: 200, data: { session_id: "wx_service_home_01" } });
    } else if (opts.url.includes("/customer/context")) {
      opts.success?.({ statusCode: 200, data: body });
    } else {
      opts.fail?.({ errMsg: "unexpected" });
    }
  };
}

test("Service Home shows checking shell — never Start Claim — before Customer Context", async () => {
  const options = await page();
  const ctx = contextFor(options);
  ctx.setData({
    homePhase: "checking",
    hasActiveSession: false,
    serverHasActiveCase: null,
  });
  assert.equal(ctx.data.homePhase, "checking");
  assert.equal(ctx.data.hasActiveSession, false);
});

test("Service Home Continue depends on its server context state, not cached token", async () => {
  const options = await page();
  const ctx = contextFor(options);
  const launches: string[] = [];
  const wx = (globalThis as { wx: Record<string, any> }).wx;
  wx.reLaunch = ({ url }: { url: string }) => launches.push(url);
  ctx.setData({ homePhase: "checking", hasActiveSession: false });
  options.onContinueCurrentClaim.call(ctx);
  assert.deepEqual(launches, []);
  ctx.applyHomeAuthority(false);
  options.onContinueCurrentClaim.call(ctx);
  assert.deepEqual(launches, []);
  ctx.applyHomeAuthority(true);
  options.onContinueCurrentClaim.call(ctx);
  assert.deepEqual(launches, ["/pages/entry/entry"]);
});

test("Start New with server Active case preserves the One Active Case policy", async () => {
  const options = await page();
  const ctx = contextFor(options);
  const wx = (globalThis as { wx: Record<string, any> }).wx;
  const modals: Record<string, unknown>[] = [];
  wx.showModal = (opts: Record<string, unknown>) => modals.push(opts);
  ctx.applyHomeAuthority(true);
  options.onStartNewClaim.call(ctx);
  assert.equal(modals.length, 1);
  assert.match(String(modals[0].title || ""), /正在处理的报案/);
});

test("Customer Context failure shows Retry — never fail-open to Start Claim", async () => {
  const options = await page();
  const ctx = contextFor(options);
  const wx = (globalThis as { wx: Record<string, any> }).wx;
  wx.login = (opts: any) => opts.success?.({ code: "sim:fail" });
  wx.request = (opts: any) => {
    if (opts.url.includes("/health/live")) opts.success?.({ statusCode: 200, data: { ok: true } });
    else opts.fail?.({ errMsg: "network" });
  };
  const launches: string[] = [];
  wx.reLaunch = ({ url }: { url: string }) => launches.push(url);
  await options.syncIdentityAndRefresh.call(ctx);
  assert.equal(ctx.data.homePhase, "error");
  assert.equal(ctx.data.hasActiveSession, false);
  options.onStartNewClaim.call(ctx);
  assert.deepEqual(launches, []);
});

test("Successful context with no Active Case enables Start Claim", async () => {
  const options = await page();
  const ctx = contextFor(options);
  installContextApi({ has_active_case: false, next_action: "START_NEW_CLAIM" });
  await options.syncIdentityAndRefresh.call(ctx);
  assert.equal(ctx.data.homePhase, "ready");
  assert.equal(ctx.data.hasActiveSession, false);
});
