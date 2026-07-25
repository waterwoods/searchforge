import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import type { CustomerTask } from "../types/task";

installMiniProgramGlobals();

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

let cachedPage: CapturedPageOptions | null = null;

async function loadBasicsPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/basics/basics");
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
    steps: ["start", "injury", "time_location", "story", "vehicle_other_party", "review", "done"],
    current_step: "injury",
    completed_count: 1,
    step_total: 5,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {
      anyone_injured: "no",
      police_involved: "no",
      accident_datetime: "2026-07-13 10:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
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
    route: "/pages/basics/basics",
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

test("Basics page uses shared taskPage behavior", async () => {
  const page = await loadBasicsPage();
  assert.ok(Array.isArray(page.behaviors));
  assert.equal(page.behaviors?.length, 1);
});

test("onShow prefills initial values from task data", async () => {
  const page = await loadBasicsPage();
  const appState: IAppOption = { taskToken: "h5t1.valid", task: buildTask() };
  (globalThis as Record<string, unknown>).getApp = () => appState;

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => buildTask(),
  });
  await page.onShow.call(ctx);

  assert.equal(ctx.data.anyoneInjured, "no");
  assert.equal(ctx.data.policeInvolved, "no");
  assert.equal(ctx.data.accidentDatetime, "2026-07-13 10:00");
});

test("injury and police choices update local state", async () => {
  const page = await loadBasicsPage();
  const ctx = createPageContext(page);
  page.onInjurySelect.call(ctx, { detail: { value: "yes" } });
  page.onPoliceSelect.call(ctx, { detail: { value: "unknown" } });
  assert.equal(ctx.data.anyoneInjured, "yes");
  assert.equal(ctx.data.policeInvolved, "unknown");
  assert.equal(ctx.data.localDirty, true);
});

test("save calls injury and police related patches with read-back", async () => {
  const page = await loadBasicsPage();
  const appState: IAppOption = { taskToken: "h5t1.valid" };
  (globalThis as Record<string, unknown>).getApp = () => appState;

  const patchCalls: Array<{ step: string; fields: Record<string, string> }> = [];
  const originalSaveBasics = CustomerTaskApi.saveBasics;
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.saveBasics = async (_token, fields, step) => {
    patchCalls.push({ step, fields });
    return buildTask();
  };
  CustomerTaskApi.getTask = async () =>
    buildTask({
      key_facts: {
        anyone_injured: "yes",
        police_involved: "yes",
        accident_datetime: "2026-07-13 10:00",
        accident_location: "Irvine Blvd",
        own_vehicle_info: "2020 Toyota Camry",
      },
    });

  let navigated = 0;
  (globalThis as Record<string, any>).wx.navigateBack = ({ success }: { success?: () => void }) => {
    navigated += 1;
    success?.();
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      anyoneInjured: "yes",
      policeInvolved: "yes",
      accidentDatetime: "2026-07-13 10:00",
      accidentLocation: "Irvine Blvd",
      ownVehicleInfo: "2020 Toyota Camry",
      busy: { ...(page.data.busy as Record<string, boolean>), loading: false, saving: false },
    },
  });
  await page.onSave.call(ctx);

  assert.equal(patchCalls[0].step, "injury");
  assert.equal(patchCalls[0].fields.anyone_injured, "yes");
  assert.equal(patchCalls[2].step, "vehicle_other_party");
  assert.equal(patchCalls[2].fields.police_involved, "yes");
  assert.equal(navigated, 1);

  CustomerTaskApi.saveBasics = originalSaveBasics;
  CustomerTaskApi.getTask = originalGetTask;
});

test("duplicate save tap is blocked while saving", async () => {
  const page = await loadBasicsPage();
  const originalSaveBasics = CustomerTaskApi.saveBasics;
  let callCount = 0;
  CustomerTaskApi.saveBasics = async () => {
    callCount += 1;
    return buildTask();
  };

  const ctx = createPageContext(page, {
    isBusy: (key?: string) => key === "saving",
    data: {
      ...page.data,
      anyoneInjured: "no",
      policeInvolved: "no",
      accidentDatetime: "2026-07-13 10:00",
      accidentLocation: "Irvine Blvd",
      ownVehicleInfo: "2020 Toyota Camry",
    },
  });
  await page.onSave.call(ctx);
  assert.equal(callCount, 0);
  CustomerTaskApi.saveBasics = originalSaveBasics;
});

test("failed step save preserves user values", async () => {
  const page = await loadBasicsPage();
  const appState: IAppOption = { taskToken: "h5t1.valid" };
  (globalThis as Record<string, unknown>).getApp = () => appState;
  const originalSaveBasics = CustomerTaskApi.saveBasics;
  CustomerTaskApi.saveBasics = async () => {
    throw new Error("network");
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      anyoneInjured: "unknown",
      policeInvolved: "yes",
      accidentDatetime: "X",
      accidentLocation: "Y",
      ownVehicleInfo: "Z1",
      busy: { ...(page.data.busy as Record<string, boolean>), loading: false, saving: false },
    },
  });
  await page.onSave.call(ctx);

  assert.equal(ctx.data.anyoneInjured, "unknown");
  assert.equal(ctx.data.policeInvolved, "yes");
  assert.equal(ctx.data.ownVehicleInfo, "Z1");

  CustomerTaskApi.saveBasics = originalSaveBasics;
});

test("navigation occurs only after authoritative read-back success", async () => {
  const page = await loadBasicsPage();
  const appState: IAppOption = { taskToken: "h5t1.valid" };
  (globalThis as Record<string, unknown>).getApp = () => appState;

  const originalSaveBasics = CustomerTaskApi.saveBasics;
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.saveBasics = async () => buildTask();
  CustomerTaskApi.getTask = async () => {
    throw new Error("read back failed");
  };

  let navigated = 0;
  (globalThis as Record<string, any>).wx.navigateBack = () => {
    navigated += 1;
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      anyoneInjured: "no",
      policeInvolved: "no",
      accidentDatetime: "2026-07-13 10:00",
      accidentLocation: "Irvine Blvd",
      ownVehicleInfo: "2020 Toyota Camry",
      busy: { ...(page.data.busy as Record<string, boolean>), loading: false, saving: false },
    },
  });
  await page.onSave.call(ctx);

  assert.equal(navigated, 0);
  CustomerTaskApi.saveBasics = originalSaveBasics;
  CustomerTaskApi.getTask = originalGetTask;
});

test("save path does not use fixed timeout", async () => {
  const page = await loadBasicsPage();
  const appState: IAppOption = { taskToken: "h5t1.valid" };
  (globalThis as Record<string, unknown>).getApp = () => appState;

  const originalSaveBasics = CustomerTaskApi.saveBasics;
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.saveBasics = async () => buildTask();
  CustomerTaskApi.getTask = async () => buildTask({ key_facts: { ...buildTask().key_facts, police_involved: "no" } });

  const originalSetTimeout = globalThis.setTimeout;
  const originalNavigateBack = (globalThis as Record<string, any>).wx.navigateBack;
  let timeoutCalls = 0;
  (globalThis as Record<string, unknown>).setTimeout = ((..._args: unknown[]) => {
    timeoutCalls += 1;
    return 1 as unknown as ReturnType<typeof setTimeout>;
  }) as typeof setTimeout;
  (globalThis as Record<string, any>).wx.navigateBack = ({ success }: { success?: () => void }) => {
    success?.();
  };

  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    data: {
      ...page.data,
      anyoneInjured: "no",
      policeInvolved: "no",
      accidentDatetime: "2026-07-13 10:00",
      accidentLocation: "Irvine Blvd",
      ownVehicleInfo: "2020 Toyota Camry",
      busy: { ...(page.data.busy as Record<string, boolean>), loading: false, saving: false },
    },
  });
  await page.onSave.call(ctx);
  assert.equal(timeoutCalls, 0);

  (globalThis as Record<string, unknown>).setTimeout = originalSetTimeout;
  (globalThis as Record<string, any>).wx.navigateBack = originalNavigateBack;
  CustomerTaskApi.saveBasics = originalSaveBasics;
  CustomerTaskApi.getTask = originalGetTask;
});

test("Basics template does not render internal fields", async () => {
  const wxml = readFileSync(join(process.cwd(), "pages/basics/basics.wxml"), "utf8");
  assert.equal(wxml.includes("case_id"), false);
  assert.equal(wxml.includes("tenant_id"), false);
  assert.equal(wxml.includes("phase"), false);
});

test("long-form Basics fields use visible multiline inputs with clear placeholders", () => {
  const wxml = readFileSync(join(process.cwd(), "pages/basics/basics.wxml"), "utf8");
  assert.match(wxml, /事故地点[\s\S]*?<textarea[\s\S]*?compact-textarea/);
  assert.match(wxml, /您的车辆[\s\S]*?<textarea[\s\S]*?compact-textarea/);
  assert.match(wxml, /Irvine Blvd 与 Culver Dr 路口/);
  assert.match(wxml, /2020 Toyota Camry，白色/);
  assert.match(wxml, /adjust-position="\{\{true\}\}"/);
});

test("contact broker opens shared guidance modal, not postpone/back", async () => {
  const page = await loadBasicsPage();
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
  assert.match(modals[0].content, /打开微信/);
  assert.equal(backs.length, 0);
});
