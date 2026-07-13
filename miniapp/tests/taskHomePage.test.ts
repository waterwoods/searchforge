import test from "node:test";
import assert from "node:assert/strict";

import {
  getLatestPage,
  installMiniProgramGlobals,
} from "./miniprogramMocks";
import type { TaskViewModel } from "../types/task";
import {
  DEFAULT_SAFETY_COPY,
  EMPTY_TASK_VIEW_MODEL,
  taskShellBindingsFromViewModel,
} from "../utils/resolveTaskViewModel";

installMiniProgramGlobals();

let cachedPage: CapturedPageOptions | null = null;

async function loadTaskHomePage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/task-home/task-home");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

function buildVm(overrides?: Partial<TaskViewModel>): TaskViewModel {
  return {
    source: "contract",
    shellMode: "content",
    title: "我的事故资料",
    instruction: "请继续完善资料",
    statusLabel: "进行中",
    statusTone: "active",
    progress: { completed: 2, total: 5, percent: 40 },
    cta: {
      label: "继续填写",
      actionType: "go_to_section",
      target: "story",
      disabled: false,
      loading: false,
      disabledReason: "",
    },
    missingItems: [
      {
        key: "accident_description",
        label: "事故经过",
        statusText: "未填写",
        actionable: true,
        route: "/pages/story/story",
        hint: "",
      },
    ],
    evidenceRequirements: [],
    reviewReady: false,
    submitReady: false,
    safetyCopy: "此记录用于办公室整理事故信息，不代表已向保险公司正式报案。",
    error: null,
    ...overrides,
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
    route: "/pages/task-home/task-home",
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

test("initial merged page data exposes string shell bindings", async () => {
  const page = await loadTaskHomePage();
  const ctx = createPageContext(page);

  assert.equal(typeof ctx.data.shellSafetyCopy, "string");
  assert.equal(typeof ctx.data.ctaDisabledReason, "string");
  assert.equal(ctx.data.shellSafetyCopy, DEFAULT_SAFETY_COPY);
  assert.equal(ctx.data.ctaDisabledReason, "");
});

test("initial render bindings stay strings when nested vm fields are absent", async () => {
  const page = await loadTaskHomePage();
  const brokenVm = { ...EMPTY_TASK_VIEW_MODEL } as TaskViewModel & {
    safetyCopy?: string | null;
    cta: { disabledReason?: string | null };
  };
  delete (brokenVm as { safetyCopy?: string }).safetyCopy;
  brokenVm.cta = { ...brokenVm.cta, disabledReason: undefined };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      taskViewModel: brokenVm,
      ...taskShellBindingsFromViewModel(brokenVm),
    },
  });

  assert.equal(typeof ctx.data.shellSafetyCopy, "string");
  assert.equal(typeof ctx.data.ctaDisabledReason, "string");
});

test("onShow delegates loading to shared behavior", async () => {
  const page = await loadTaskHomePage();
  let loadCalled = 0;
  const ctx = createPageContext(page, {
    loadTask: async () => {
      loadCalled += 1;
      return null;
    },
  });

  page.onShow.call(ctx);
  await Promise.resolve();
  assert.equal(loadCalled, 1);
});

test("primary action navigates from view model CTA", async () => {
  const page = await loadTaskHomePage();
  const routes: string[] = [];
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      taskViewModel: buildVm({
        cta: {
          label: "继续填写",
          actionType: "go_to_section",
          target: "photos",
          disabled: false,
          loading: false,
          disabledReason: "",
        },
      }),
    },
    isBusy: () => false,
    setBusy: () => undefined,
  });
  (globalThis as Record<string, any>).wx.navigateTo = ({ url, complete }: { url: string; complete?: () => void }) => {
    routes.push(url);
    complete?.();
  };

  page.onPrimaryAction.call(ctx);
  assert.deepEqual(routes, ["/pages/photos/photos"]);
});

test("retry button delegates to shared retryLoadTask", async () => {
  const page = await loadTaskHomePage();
  let retried = 0;
  const ctx = createPageContext(page, {
    retryLoadTask: async () => {
      retried += 1;
      return null;
    },
  });

  page.onRetry.call(ctx);
  await Promise.resolve();
  assert.equal(retried, 1);
});

test("navigation guard blocks duplicate CTA taps", async () => {
  const page = await loadTaskHomePage();
  let navigateCount = 0;
  (globalThis as Record<string, any>).wx.navigateTo = () => {
    navigateCount += 1;
  };

  const ctx = createPageContext(page, {
    isBusy: () => true,
    data: {
      ...page.data,
      taskViewModel: buildVm(),
    },
  });
  page.onPrimaryAction.call(ctx);
  assert.equal(navigateCount, 0);
});
