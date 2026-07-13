import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";

installMiniProgramGlobals();

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

let cachedPage: CapturedPageOptions | null = null;

async function loadErrorPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/error/error");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
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
    route: "/pages/error/error",
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

test("Error page uses shared taskPage behavior", async () => {
  const page = await loadErrorPage();
  assert.ok(Array.isArray(page.behaviors));
  assert.equal(page.behaviors?.length, 1);
});

test("onLoad maps retryable network error", async () => {
  const page = await loadErrorPage();
  const ctx = createPageContext(page);
  page.onLoad.call(ctx, { code: "network_error" });
  assert.equal(ctx.data.errorState.code, "network_error");
  assert.equal(ctx.data.errorState.retryable, true);
  assert.ok(String(ctx.data.errorState.message).length > 0);
  assert.equal(ctx.data.title, "暂时无法继续");
});

test("invalid link is non-retryable and points user to broker", async () => {
  const page = await loadErrorPage();
  const ctx = createPageContext(page);
  page.onLoad.call(ctx, { code: "invalid_or_expired_task_link" });
  assert.equal(ctx.data.errorState.retryable, false);
  assert.ok(String(ctx.data.ctaDisabledReason).includes("陈总"));
});

test("retry relaunches entry for recoverable errors", async () => {
  const page = await loadErrorPage();
  const relaunches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    relaunches.push(url);
    complete?.();
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      errorState: {
        code: "network_error",
        message: "网络暂时不可用，请稍后再试。",
        retryable: true,
        blocking: false,
      },
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
  });

  page.onRetry.call(ctx);
  assert.deepEqual(relaunches, ["/pages/entry/entry"]);
  assert.equal(ctx.data.busy.navigating, false);
});

test("non-retryable retry opens contact broker modal", async () => {
  const page = await loadErrorPage();
  const modals: Array<{ title: string; content: string }> = [];
  (globalThis as Record<string, any>).wx.showModal = (opts: {
    title: string;
    content: string;
  }) => {
    modals.push(opts);
  };
  const relaunches: string[] = [];
  (globalThis as Record<string, any>).wx.reLaunch = ({ url }: { url: string }) =>
    relaunches.push(url);

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      errorState: {
        code: "token_missing",
        message: "未找到任务入口",
        retryable: false,
        blocking: false,
      },
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
  });

  page.onRetry.call(ctx);
  assert.equal(relaunches.length, 0);
  assert.equal(modals.length, 1);
  assert.equal(modals[0].title, "联系陈总");
});
