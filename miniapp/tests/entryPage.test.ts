import assert from "node:assert/strict";
import test from "node:test";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";

installMiniProgramGlobals();

type PageOptions = Record<string, any>;
let cached: PageOptions | null = null;

async function entryPage(): Promise<PageOptions> {
  if (!cached) {
    await import("../pages/entry/entry");
    cached = getLatestPage().options as PageOptions;
  }
  return cached;
}

function idleBusy() {
  return { loading: false, saving: false, uploading: false, submitting: false, navigating: false, retrying: false };
}

function context(page: PageOptions, overrides?: Record<string, unknown>): Record<string, any> {
  const behavior = page.behaviors?.[0] || {};
  const data = { ...behavior.data, ...page.data, busy: idleBusy(), launchSource: "", ...overrides };
  return {
    ...behavior.methods,
    ...page,
    data,
    route: "/pages/entry/entry",
    setData(patch: Record<string, unknown>) {
      Object.assign(data, patch);
    },
    ...overrides,
  };
}

test("Entry uses the shared task-page behavior", async () => {
  const page = await entryPage();
  assert.equal(page.behaviors?.length, 1);
});

test("Entry maps server START_NEW_CLAIM context to the Start Claim form", async () => {
  const page = await entryPage();
  const launches: string[] = [];
  const wx = (globalThis as { wx: Record<string, any> }).wx;
  wx.reLaunch = ({ url }: { url: string }) => launches.push(url);
  wx.login = (opts: any) => opts.success({ code: "sim:entry-start" });
  wx.request = (opts: any) => {
    if (opts.url.includes("/health/live")) opts.success({ statusCode: 200, data: { ok: true } });
    else if (opts.url.includes("/customer/session")) opts.success({ statusCode: 200, data: { session_id: "wx_entry_start_01" } });
    else if (opts.url.includes("/customer/context")) opts.success({ statusCode: 200, data: { has_active_case: false, next_action: "START_NEW_CLAIM" } });
  };
  const ctx = context(page);
  await page.bootstrap.call(ctx, {});
  assert.deepEqual(launches, ["/pages/start-claim/start-claim?entry=form"]);
});

test("server-owned action map sends BROKER_REVIEW to Case Status", async () => {
  const { routeForCustomerNextAction } = await import("../utils/customerContextRoute");
  assert.equal(routeForCustomerNextAction("BROKER_REVIEW"), "/pages/case-status/case-status");
});
