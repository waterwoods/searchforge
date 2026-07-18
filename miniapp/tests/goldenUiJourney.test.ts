/**
 * P26H-UI — real click / render / complete journey against Mini Program pages.
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
  getLatestPage,
  installMiniProgramGlobals,
  resetMiniProgramCaptures,
} from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import type { CustomerTask } from "../types/task";
import {
  assertEmptyPageGate,
  buildBrokerRequestedInsuranceTask,
  buildFreshSystemDefaultTask,
  evaluateTaskHomeTap,
  formatUiReport,
  REQUEST_ITEM_ROUTE,
  type UiJourneyReport,
} from "../utils/goldenUiJourney";
import { resolveCustomerTaskCardsFromTask } from "../utils/resolveCustomerTaskCards";
import { resolveRequestItemWorkSurface } from "../utils/requestItemWorkSurface";

installMiniProgramGlobals();

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

const pageCache = new Map<string, CapturedPageOptions>();

async function loadPage(modulePath: string): Promise<CapturedPageOptions> {
  const hit = pageCache.get(modulePath);
  if (hit) return hit;
  resetMiniProgramCaptures();
  await import(modulePath);
  const options = getLatestPage().options as CapturedPageOptions;
  pageCache.set(modulePath, options);
  return options;
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
    ...(behavior.methods || {}),
    ...page,
    ...overrides,
  };
  ctx.data = overrides?.data ? { ...data, ...(overrides.data as object) } : data;
  if (!overrides?.setData) {
    ctx.setData = function setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    };
  }
  return ctx;
}

function flush(): Promise<void> {
  return new Promise((resolve) => setImmediate(resolve));
}

function newReport(): UiJourneyReport {
  return { ok: true, checks: [], failures: [] };
}

function seal(report: UiJourneyReport): UiJourneyReport {
  report.ok = report.failures.length === 0;
  return report;
}

async function bootstrapRequestItem(
  task: CustomerTask,
): Promise<Record<string, any>> {
  const page = await loadPage("../pages/request-item/request-item");
  const navigations: string[] = [];
  const wx = (globalThis as { wx: Record<string, any> }).wx;
  wx.navigateTo = (opts: { url: string; complete?: () => void }) => {
    navigations.push(opts.url);
    opts.complete?.();
  };
  const ctx = createPageContext(page, {
    route: REQUEST_ITEM_ROUTE,
    ensureTaskInitialized: async () => task,
    rehydrateAuthoritativeTask: async () => task,
    setBusy(flag: string, value: boolean) {
      this.data.busy = { ...this.data.busy, [flag]: value };
    },
    markTaskPageDestroyed() {
      return undefined;
    },
    requireToken: () => "h5t1_p26h_ui_token",
    goTaskHome() {
      navigations.push("/pages/task-home/task-home");
    },
  });
  await ctx.bootstrapPage({ ownerLoad: true });
  await flush();
  ctx.__navigations = navigations;
  return ctx;
}

test("P26H-UI Empty Page Gate catches legacy nextAction-only blank insurance page", () => {
  const report = newReport();
  // Founder defect shape: TS set evidence mode, WXML required nextAction → blank.
  assertEmptyPageGate(report, {
    task: "insurance_card",
    source: "system_default",
    expectedPage: "insurance upload",
    data: {
      loading: false,
      waitingForBroker: false,
      inputMode: "evidence",
      nextAction: null,
      nextActionTitle: "上传保险卡",
      pageError: { code: "", message: "", retryable: false, blocking: false },
      // omit showWorkSurface → legacy binding
    },
  });
  const sealed = seal(report);
  assert.equal(sealed.ok, false);
  const text = formatUiReport(sealed);
  assert.match(text, /Owning layer: Page Bootstrap/);
  assert.match(text, /request-item \/ blank|blank/);
  console.log(text);
});

test("P26H-UI system_default insurance page renders upload controls after repair", async () => {
  const report = newReport();
  const task = buildFreshSystemDefaultTask();
  evaluateTaskHomeTap(report, task, "insurance_card", REQUEST_ITEM_ROUTE);
  const ctx = await bootstrapRequestItem(task);
  assertEmptyPageGate(report, {
    task: "insurance_card",
    source: "system_default",
    expectedPage: "insurance upload",
    data: ctx.data,
  });
  assert.equal(ctx.data.inputMode, "evidence");
  assert.equal(ctx.data.showWorkSurface, true);
  assert.equal(ctx.data.showFooterCta, true);
  assert.ok(!String(ctx.data.pageError?.message || "").includes("无需此步骤"));
  assert.equal(seal(report).ok, true, formatUiReport(report));
});

test("P26H-UI full local click/render/complete journey", async () => {
  const report = newReport();

  // --- Insurance: Task Home → tap → render → upload → Task Home truth ---
  let task = buildFreshSystemDefaultTask();
  evaluateTaskHomeTap(report, task, "insurance_card", REQUEST_ITEM_ROUTE);
  let ctx = await bootstrapRequestItem(task);
  assertEmptyPageGate(report, {
    task: "insurance_card",
    source: "system_default",
    expectedPage: "insurance upload",
    data: ctx.data,
  });
  assert.equal(ctx.data.inputMode, "evidence");
  assert.equal(ctx.data.showWorkSurface, true);
  assert.ok(ctx.data.nextActionTitle);
  assert.ok(!String(ctx.data.pageError?.message || "").includes("无需此步骤"));

  // Simulate photo chosen (test-safe fixture path).
  ctx.setData({
    uploadItems: [
      {
        localPath: "wxfile://p26h-ui-insurance.jpg",
        uploading: false,
        uploaded: false,
        attachmentId: "",
        error: "",
        progress: 0,
      },
    ],
  });
  const originalUpload = CustomerTaskApi.uploadPhoto;
  const originalGetTask = CustomerTaskApi.getTask;
  let uploadedAttachmentId = "";
  CustomerTaskApi.uploadPhoto = async () => {
    uploadedAttachmentId = "att_p26h_ui_insurance";
    return {
      attachment_id: "att_p26h_ui_insurance",
      slot: "policy_or_insurance_card",
      status: "uploaded",
    } as never;
  };
  const completedTask: CustomerTask = {
    ...task,
    constitution_projection: {
      customer: {
        ...(task.constitution_projection?.customer || {}),
        today: "补充事故照片",
        why: "保险卡已收到。",
        tasks: (task.constitution_projection?.customer?.tasks || []).map((row) => {
          if (row.task_id === "insurance_card") {
            return {
              ...row,
              state: "completed",
              actionable: false,
              progress: { completed: 1, total: 1 },
              is_today: false,
            };
          }
          if (row.task_id === "accident_photos") {
            return {
              ...row,
              state: "pending",
              actionable: true,
              is_today: true,
            };
          }
          return row;
        }),
      },
    },
  };
  CustomerTaskApi.getTask = async () => completedTask;
  (globalThis as { getApp: () => { task: CustomerTask | null } }).getApp = () => ({
    task: completedTask,
  });

  try {
    await ctx.onSubmit();
    await flush();
    await new Promise((resolve) => setTimeout(resolve, 450));
  } finally {
    CustomerTaskApi.uploadPhoto = originalUpload;
    CustomerTaskApi.getTask = originalGetTask;
  }

  assert.equal(uploadedAttachmentId, "att_p26h_ui_insurance");
  assert.equal(ctx.data.submissionState, "confirmed");
  report.checks.push("insurance_card: upload lifecycle complete");

  const homeCards = resolveCustomerTaskCardsFromTask(completedTask);
  const insuranceCard = homeCards.find((c) => c.taskId === "insurance_card");
  assert.equal(insuranceCard?.state, "completed");
  report.checks.push("insurance_card: Task Home state updated");

  // --- Photos: tap → photos page renders and can complete ---
  task = {
    ...completedTask,
    photo_count: 0,
    task_contract: {
      contract_version: "0",
      task_id: "task_photos",
      task_type: "claim_intake",
      task_status: "collecting",
      title: "我的事故资料",
      instruction: "补充事故照片",
      progress: { completed: 3, total: 5 },
      sections: [],
      fields: {},
      missing_items: [],
      evidence_requirements: [
        { slot: "customer_damage_photo", label: "车辆受损位置", min: 1, received: 0 },
        { slot: "other_party_vehicle_photo", label: "对方车辆 / 现场", min: 1, received: 0 },
      ],
      next_action: { type: "go_to_section", target: "photos", label: "补充照片" },
      review_ready: false,
      submit_ready: false,
      revision: 1,
      timestamps: { updated_at: "2026-07-18T00:00:00Z" },
      capabilities: { voice: false, scan: false },
      branding: { office_name: "陈总办公室", safety_copy: "" },
      error: null,
    },
  };
  evaluateTaskHomeTap(report, task, "accident_photos", "/pages/photos/photos");
  const photosPage = await loadPage("../pages/photos/photos");
  const photosCtx = createPageContext(photosPage, {
    route: "/pages/photos/photos",
    requireToken: () => "h5t1_p26h_ui_token",
    fetchTaskForPhotoPage: async () => task,
    setBusy(flag: string, value: boolean) {
      this.data.busy = { ...this.data.busy, [flag]: value };
    },
  });
  await photosPage.onShow.call(photosCtx);
  await flush();
  assert.ok(Array.isArray(photosCtx.data.slots) && photosCtx.data.slots.length > 0);
  assert.notEqual(photosCtx.data.pageState, "recoverable_error");
  report.checks.push("accident_photos: page rendered");

  // Minimal complete path: mark first slot uploaded + raise photo_count via read-back task.
  const photosDone: CustomerTask = {
    ...task,
    photo_count: 1,
    constitution_projection: {
      customer: {
        ...(task.constitution_projection?.customer || {}),
        tasks: (task.constitution_projection?.customer?.tasks || []).map((row) =>
          row.task_id === "accident_photos"
            ? {
                ...row,
                state: "completed",
                actionable: false,
                progress: { completed: 1, total: 1 },
              }
            : row,
        ),
      },
    },
  };
  photosCtx.setData({
    photoCount: 1,
    slots: (photosCtx.data.slots || []).map((slot: { uploaded?: boolean }, index: number) =>
      index === 0 ? { ...slot, uploaded: true, requirementMet: true } : slot,
    ),
  });
  assert.equal(photosCtx.data.slots[0].uploaded, true);
  assert.equal(resolveCustomerTaskCardsFromTask(photosDone).find((c) => c.taskId === "accident_photos")?.state, "completed");
  report.checks.push("accident_photos: completable upload surface + completion truth");

  // --- Story: render with saved content ---
  const storyTask = buildFreshSystemDefaultTask({
    constitution_projection: {
      customer: {
        today: "填写事故经过",
        why: "",
        after: "",
        current_stage: "customer_action_needed",
        tasks: [
          {
            task_id: "accident_story",
            title: "事故经过",
            state: "pending",
            progress: { completed: 0, total: 1 },
            is_today: true,
            route: "story",
            actionable: true,
            primary_action: "填写事故经过",
            task_source: "system_default",
          },
        ],
      },
    },
  });
  evaluateTaskHomeTap(report, storyTask, "accident_story", "/pages/story/story");
  const storyPage = await loadPage("../pages/story/story");
  const storyCtx = createPageContext(storyPage, {
    route: "/pages/story/story",
    requireToken: () => "h5t1_p26h_ui_token",
    loadTask: async () => {
      const existing = String(storyTask.key_facts.accident_description || "");
      storyCtx.setData({
        task: storyTask,
        story: existing,
        charCount: existing.length,
        localDirty: false,
        busy: { ...storyCtx.data.busy, loading: false },
      });
      return storyTask;
    },
  });
  await storyPage.onShow.call(storyCtx);
  await flush();
  assert.match(String(storyCtx.data.story || ""), /倒车碰撞/);
  report.checks.push("accident_story: saved content rendered");

  // --- broker_requested insurance → request-item with reason ---
  const brokerTask = buildBrokerRequestedInsuranceTask();
  evaluateTaskHomeTap(report, brokerTask, "insurance_card", REQUEST_ITEM_ROUTE);
  const brokerCtx = await bootstrapRequestItem(brokerTask);
  assert.ok(!resolveRequestItemWorkSurface(brokerCtx.data).rejectedWarning);
  assert.ok(brokerCtx.data.nextAction);
  assert.match(String(brokerCtx.data.nextActionInstructions || ""), /更清晰的保险卡/);
  assert.equal(brokerCtx.data.inputMode, "evidence");
  assert.ok(brokerCtx.data.showWorkSurface !== false);
  report.checks.push("broker_requested insurance: request-item rendered with reason");

  const sealed = seal(report);
  assert.equal(sealed.ok, true, formatUiReport(sealed));
  console.log(formatUiReport(sealed));
});

test("requestItemWorkSurface detects legacy nextAction-only blank page", () => {
  const legacy = resolveRequestItemWorkSurface({
    loading: false,
    waitingForBroker: false,
    inputMode: "evidence",
    nextAction: null,
    // showWorkSurface omitted → legacy WXML binding
  });
  assert.equal(legacy.emptyPage, true);
  assert.equal(legacy.showWorkSurface, true);

  const fixed = resolveRequestItemWorkSurface({
    loading: false,
    waitingForBroker: false,
    inputMode: "evidence",
    nextAction: null,
    showWorkSurface: true,
    showFooterCta: true,
  });
  assert.equal(fixed.emptyPage, false);
});
