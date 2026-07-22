import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { ApiRequestError } from "../utils/request";
import type { CustomerTask } from "../types/task";

installMiniProgramGlobals();

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

let cachedPage: CapturedPageOptions | null = null;

async function loadEntryPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/entry/entry");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_1",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "review", "done"],
    current_step: "review",
    completed_count: 1,
    step_total: 3,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {},
    missing_info: [],
    ...overrides,
  };
}

function idleBusy() {
  return {
    loading: false,
    saving: false,
    uploading: false,
    submitting: false,
    navigating: false,
    retrying: false,
  };
}

function createPageContext(page: CapturedPageOptions, overrides?: Record<string, unknown>) {
  const behavior = (page.behaviors?.[0] || {}) as {
    data?: Record<string, unknown>;
    methods?: Record<string, (...args: any[]) => any>;
  };
  const data = {
    ...(behavior.data || {}),
    ...(page.data || {}),
  } as Record<string, any>;
  const ctx: Record<string, any> = {
    route: "/pages/entry/entry",
    data,
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...(behavior.methods || {}),
    ...page,
    ...overrides,
  };
  return ctx;
}

test("Entry page uses shared taskPage behavior", async () => {
  const page = await loadEntryPage();
  assert.ok(Array.isArray(page.behaviors));
  assert.equal(page.behaviors?.length, 1);
});

test("missing token redirects to start-claim", async () => {
  const page = await loadEntryPage();
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({
    url,
    fail,
  }: {
    url: string;
    fail?: () => void;
  }) => {
    redirects.push(url);
  };
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: idleBusy(),
      launchSource: "",
      errorState: { code: "", message: "", retryable: false, blocking: false },
      retryMeta: { attempts: 0, cooldownUntil: 0 },
    },
    resolveLaunchContext: () => null,
  });

  await page.bootstrap.call(ctx, {});
  assert.deepEqual(redirects, ["/pages/start-claim/start-claim"]);
  assert.equal(ctx.data.busy.navigating, true);
});

test("missing token falls back to recovery error if redirect fails", async () => {
  const page = await loadEntryPage();
  (globalThis as Record<string, any>).wx.redirectTo = ({
    fail,
  }: {
    url: string;
    fail?: () => void;
  }) => {
    fail?.();
  };
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: idleBusy(),
      launchSource: "",
      errorState: { code: "", message: "", retryable: false, blocking: false },
      retryMeta: { attempts: 0, cooldownUntil: 0 },
    },
    resolveLaunchContext: () => null,
  });

  await page.bootstrap.call(ctx, {});
  assert.equal(ctx.data.errorState.code, "token_missing");
  assert.equal(ctx.data.errorState.retryable, false);
  assert.equal(ctx.data.busy.loading, false);
  assert.equal(ctx.data.busy.navigating, false);
});

test("resume source uses restore loading copy then relaunches task home", async () => {
  const page = await loadEntryPage();
  const relaunches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    relaunches.push(url);
  };
  const appState: Record<string, unknown> = {};
  (globalThis as Record<string, unknown>).getApp = () => appState;

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: idleBusy(),
      launchSource: "",
      errorState: { code: "", message: "", retryable: false, blocking: false },
      retryMeta: { attempts: 0, cooldownUntil: 0 },
    },
    resolveLaunchContext: () => ({
      token: "h5t1.resume",
      source: "resume_storage",
    }),
    persistLaunch: () => undefined,
    fetchTask: async () => buildTask(),
  });

  await page.bootstrap.call(ctx, {});
  assert.match(String(ctx.data.loadingMessage), /恢复/);
  assert.deepEqual(relaunches, ["/pages/task-home/task-home"]);
  assert.equal(ctx.data.busy.navigating, true);
  assert.equal(Boolean(appState.__mp_resume_restored_hint), true);
});

test("submitted resume relaunches receipt", async () => {
  const page = await loadEntryPage();
  const relaunches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) => {
    relaunches.push(url);
  };
  (globalThis as Record<string, unknown>).getApp = () => ({});

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: idleBusy(),
      launchSource: "",
      errorState: { code: "", message: "", retryable: false, blocking: false },
      retryMeta: { attempts: 0, cooldownUntil: 0 },
    },
    resolveLaunchContext: () => ({
      token: "h5t1.done",
      source: "launch_query",
    }),
    persistLaunch: () => undefined,
    fetchTask: async () => buildTask({ submitted: true, current_step: "done" }),
  });

  await page.bootstrap.call(ctx, {});
  assert.deepEqual(relaunches, ["/pages/receipt/receipt"]);
});

test("network failure keeps retryable error and clears loading", async () => {
  const page = await loadEntryPage();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: idleBusy(),
      launchSource: "",
      errorState: { code: "", message: "", retryable: false, blocking: false },
      retryMeta: { attempts: 0, cooldownUntil: 0 },
    },
    resolveLaunchContext: () => ({
      token: "h5t1.valid",
      source: "dev_config",
    }),
    fetchTask: async () => {
      throw new ApiRequestError("network_error");
    },
  });

  await page.bootstrap.call(ctx, {});
  assert.equal(ctx.data.errorState.code, "network_error");
  assert.equal(ctx.data.errorState.retryable, true);
  assert.equal(ctx.data.busy.loading, false);
});

test("domain_not_allowed is non-retryable and not the opaque fallback", async () => {
  const page = await loadEntryPage();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      busy: idleBusy(),
      launchSource: "",
      errorState: { code: "", message: "", retryable: false, blocking: false },
      retryMeta: { attempts: 0, cooldownUntil: 0 },
    },
    resolveLaunchContext: () => ({
      token: "h5t1.valid",
      source: "launch_query",
    }),
    fetchTask: async () => {
      throw new ApiRequestError("domain_not_allowed", 0, {
        errMsg: "request:fail url not in domain list",
      });
    },
  });

  await page.bootstrap.call(ctx, {});
  assert.equal(ctx.data.errorState.code, "domain_not_allowed");
  assert.equal(ctx.data.errorState.retryable, false);
  assert.match(String(ctx.data.errorState.message), /域名未授权|报案服务/);
  assert.notEqual(ctx.data.errorState.message, "暂时无法完成操作，请稍后再试。");
  assert.equal(ctx.data.busy.loading, false);
});
