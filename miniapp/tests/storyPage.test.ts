import test from "node:test";
import assert from "node:assert/strict";

import {
  getLatestPage,
  installMiniProgramGlobals,
} from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import type { CustomerTask } from "../types/task";

installMiniProgramGlobals();

let cachedPage: CapturedPageOptions | null = null;

async function loadStoryPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/story/story");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_1",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "story", "review", "done"],
    current_step: "story",
    completed_count: 1,
    step_total: 3,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {
      accident_description: "我在红灯前被追尾。",
    },
    missing_info: [],
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
    route: "/pages/story/story",
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

test("onShow uses behavior token guard and skips load without token", async () => {
  const page = await loadStoryPage();
  let loadCount = 0;
  const ctx = createPageContext(page, {
    requireToken: () => null,
    loadTask: async () => {
      loadCount += 1;
      return null;
    },
  });

  await page.onShow.call(ctx);
  assert.equal(loadCount, 0);
});

test("onShow prefills story from loaded task when not dirty", async () => {
  const page = await loadStoryPage();
  const task = buildTask({ key_facts: { accident_description: "已有事故经过" } });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => {
      ctx.setData({ task });
      return task;
    },
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.story, "已有事故经过");
  assert.equal(ctx.data.charCount, 6);
});

test("short story is rejected before API call", async () => {
  const page = await loadStoryPage();
  const toasts: string[] = [];
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) => toasts.push(title);
  let saveCalled = 0;
  const originalSaveStory = CustomerTaskApi.saveStory;
  CustomerTaskApi.saveStory = async () => {
    saveCalled += 1;
    return buildTask();
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      story: "太短",
      minLength: 10,
    },
  });
  await page.onSave.call(ctx);

  assert.equal(saveCalled, 0);
  assert.ok(toasts.some((title) => title.includes("请至少填写")));
  CustomerTaskApi.saveStory = originalSaveStory;
});

test("successful save performs API save plus authoritative read-back", async () => {
  const page = await loadStoryPage();
  const savedTask = buildTask({ case_id: "saved_case" });
  const readBackTask = buildTask({ case_id: "read_back_case" });
  const appState: IAppOption = { taskToken: "h5t1.valid" };
  (globalThis as Record<string, unknown>).getApp = () => appState;

  const originalSaveStory = CustomerTaskApi.saveStory;
  const originalGetTask = CustomerTaskApi.getTask;
  let saveCalls = 0;
  let readBackCalls = 0;
  CustomerTaskApi.saveStory = async () => {
    saveCalls += 1;
    return savedTask;
  };
  CustomerTaskApi.getTask = async () => {
    readBackCalls += 1;
    return readBackTask;
  };

  let saveAndReturnCalled = 0;
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      story: "这是一段足够长的事故描述，满足最小字数要求。",
      minLength: 10,
    },
    saveAndReturn: async (saveFn: () => Promise<void>) => {
      saveAndReturnCalled += 1;
      await saveFn();
      return true;
    },
  });

  await page.onSave.call(ctx);
  assert.equal(saveAndReturnCalled, 1);
  assert.equal(saveCalls, 1);
  assert.equal(readBackCalls, 1);
  assert.equal(appState.task?.case_id, "read_back_case");

  CustomerTaskApi.saveStory = originalSaveStory;
  CustomerTaskApi.getTask = originalGetTask;
});

test("failed save keeps user text unchanged", async () => {
  const page = await loadStoryPage();
  const originalStory = "保存失败后不应丢失的文本内容。";
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      story: originalStory,
      charCount: originalStory.length,
      minLength: 10,
    },
    saveAndReturn: async (_saveFn: () => Promise<void>) => false,
  });

  await page.onSave.call(ctx);
  assert.equal(ctx.data.story, originalStory);
  assert.equal(ctx.data.charCount, originalStory.length);
});

test("save path no longer uses fixed timeout navigation", async () => {
  const page = await loadStoryPage();
  const originalSaveStory = CustomerTaskApi.saveStory;
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.saveStory = async () => buildTask();
  CustomerTaskApi.getTask = async () => buildTask();

  let timeoutCalls = 0;
  const originalSetTimeout = globalThis.setTimeout;
  (globalThis as Record<string, unknown>).setTimeout = ((..._args: unknown[]) => {
    timeoutCalls += 1;
    return 1 as unknown as ReturnType<typeof setTimeout>;
  }) as typeof setTimeout;

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      story: "这是一段足够长的事故描述，满足最小字数要求。",
      minLength: 10,
    },
    saveAndReturn: async (saveFn: () => Promise<void>) => {
      await saveFn();
      return true;
    },
  });
  await page.onSave.call(ctx);

  assert.equal(timeoutCalls, 0);
  CustomerTaskApi.saveStory = originalSaveStory;
  CustomerTaskApi.getTask = originalGetTask;
  (globalThis as Record<string, unknown>).setTimeout = originalSetTimeout;
});

test("contact broker opens shared guidance modal, not postpone/back", async () => {
  const page = await loadStoryPage();
  const modals: Array<{ title: string; content: string }> = [];
  const backs: number[] = [];
  (globalThis as Record<string, any>).wx.showModal = (opts: {
    title: string;
    content: string;
  }) => {
    modals.push(opts);
  };
  (globalThis as Record<string, any>).wx.navigateBack = () => {
    backs.push(1);
  };

  page.onContactBroker.call(createPageContext(page));
  assert.equal(modals.length, 1);
  assert.equal(modals[0].title, "联系陈总");
  assert.match(modals[0].content, /返回微信/);
  assert.equal(backs.length, 0);
});

test("story page exposes voice controls and preserves typed text on leave/resume", async () => {
  const { readFileSync } = await import("node:fs");
  const { dirname, join } = await import("node:path");
  const { fileURLToPath } = await import("node:url");
  const here = dirname(fileURLToPath(import.meta.url));
  const wxml = readFileSync(join(here, "../pages/story/story.wxml"), "utf8");
  assert.match(wxml, /onTapRecord/);
  assert.match(wxml, /showRecordBtn/);
  assert.match(wxml, /\{\{cardSubtitle\}\}/);

  const page = await loadStoryPage();
  assert.match(String(page.data.cardSubtitle || ""), /可录音转文字/);
  const task = buildTask({ key_facts: { accident_description: "服务器已保存的事故经过。" } });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => {
      ctx.setData({ task });
      return task;
    },
    data: {
      ...page.data,
      localDirty: true,
      story: "离开前未保存的本地草稿文字内容。",
      charCount: "离开前未保存的本地草稿文字内容。".length,
      showRecordBtn: true,
    },
  });
  await page.onShow.call(ctx);
  // Leave/return with localDirty must not wipe in-progress story.
  assert.equal(ctx.data.story, "离开前未保存的本地草稿文字内容。");
  assert.equal(ctx.data.showRecordBtn, true);
});
