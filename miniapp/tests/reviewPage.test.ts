import test from "node:test";
import assert from "node:assert/strict";

import { getLatestPage, installMiniProgramGlobals } from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import { ApiRequestError } from "../utils/request";
import type { CustomerTask, TaskContractV0 } from "../types/task";

installMiniProgramGlobals();

type CapturedPageOptions = {
  data: Record<string, unknown>;
  behaviors?: Array<Record<string, unknown>>;
  [key: string]: any;
};

let cachedPage: CapturedPageOptions | null = null;

async function loadReviewPage(): Promise<CapturedPageOptions> {
  if (!cachedPage) {
    await import("../pages/review/review");
    cachedPage = getLatestPage().options as CapturedPageOptions;
  }
  return cachedPage;
}

function buildContract(overrides?: Partial<TaskContractV0>): TaskContractV0 {
  return {
    contract_version: "0",
    task_id: "task_1",
    task_type: "claim_intake",
    task_status: "review_ready",
    title: "我的事故资料",
    instruction: "请检查后提交",
    progress: { completed: 4, total: 4 },
    sections: [],
    fields: {},
    missing_items: [],
    evidence_requirements: [],
    next_action: { type: "submit", target: "review", label: "提交给陈总审核" },
    review_ready: true,
    submit_ready: true,
    revision: 1,
    timestamps: { updated_at: "2026-07-14T10:00:00Z" },
    capabilities: { voice: false, scan: false },
    branding: { office_name: "陈总办公室", safety_copy: "安全文案" },
    error: null,
    ...overrides,
  };
}

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_1",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "story", "basics", "photos", "review", "done"],
    current_step: "review",
    completed_count: 4,
    step_total: 5,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "no",
      police_involved: "no",
      accident_datetime: "2026-07-14 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    missing_info: [],
    photo_count: 2,
    dashboard_summary: {
      title: "我的事故资料",
      subtitle: "资料已齐，可以提交",
      status: "待提交",
      received: ["事故经过", "基本资料", "事故照片"],
      missing: [],
      next_action: "提交给陈总审核",
      primary_cta: "提交给陈总审核",
      secondary_cta: "",
      submitted_supplement_allowed: false,
      warning: "",
    },
    task_contract: buildContract(),
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
    route: "/pages/review/review",
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

test("Review page uses shared taskPage behavior", async () => {
  const page = await loadReviewPage();
  assert.ok(Array.isArray(page.behaviors));
  assert.equal(page.behaviors?.length, 1);
});

test("submit ready enables CTA from shared resolver", async () => {
  const page = await loadReviewPage();
  const task = buildTask();
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.canSubmit, true);
  assert.equal(ctx.data.submitDisabledReason, "");
  assert.equal(ctx.data.story.includes("追尾"), true);
  assert.equal(ctx.data.photoCount, 2);
  assert.match(String(ctx.data.readySummary), /齐全|提交/);
  assert.ok(String(ctx.data.storyPreview).length > 0);
});

test("disabled reason shows when submit is not ready", async () => {
  const page = await loadReviewPage();
  const task = buildTask({
    key_facts: {
      accident_description: "短",
      anyone_injured: "no",
    },
    photo_count: 0,
    task_contract: buildContract({
      task_status: "collecting",
      review_ready: false,
      submit_ready: false,
      missing_items: [{ key: "accident_description", label: "事故经过" }],
    }),
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.canSubmit, false);
  assert.ok(String(ctx.data.submitDisabledReason).length > 0);
  assert.match(String(ctx.data.submitDisabledReason), /事故经过|补全|照片/);
});

test("duplicate submit is blocked while busy submitting", async () => {
  const page = await loadReviewPage();
  let submitCalls = 0;
  const originalSubmit = CustomerTaskApi.submitTask;
  CustomerTaskApi.submitTask = async () => {
    submitCalls += 1;
    return buildTask({ submitted: true, current_step: "done" });
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      canSubmit: true,
      submitDisabledReason: "",
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: true,
        navigating: false,
        retrying: false,
      },
    },
    requireToken: () => "h5t1.valid",
  });

  await page.onSubmit.call(ctx);
  assert.equal(submitCalls, 0);

  CustomerTaskApi.submitTask = originalSubmit;
});

test("read-back success navigates to receipt only after submitted confirmed", async () => {
  const page = await loadReviewPage();
  const redirects: string[] = [];
  const toasts: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    redirects.push(url);
    complete?.();
  };
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) =>
    toasts.push(title);

  const originalSubmit = CustomerTaskApi.submitTask;
  let submitCalls = 0;
  CustomerTaskApi.submitTask = async () => {
    submitCalls += 1;
    return buildTask({ submitted: true, current_step: "done" });
  };

  const submittedTask = buildTask({
    submitted: true,
    current_step: "done",
    task_contract: buildContract({
      task_status: "submitted",
      review_ready: true,
      submit_ready: false,
    }),
  });

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      canSubmit: true,
      submitDisabledReason: "",
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
    requireToken: () => "h5t1.valid",
    loadTask: async () => submittedTask,
  });

  await page.onSubmit.call(ctx);
  assert.equal(submitCalls, 1);
  assert.deepEqual(redirects, ["/pages/receipt/receipt"]);
  assert.equal(ctx.data.busy.submitting, false);
  assert.ok(toasts.includes("提交成功"));

  CustomerTaskApi.submitTask = originalSubmit;
});

test("failed submit keeps user on review and clears busy submitting", async () => {
  const page = await loadReviewPage();
  const toasts: string[] = [];
  (globalThis as Record<string, any>).wx.showToast = ({ title }: { title: string }) =>
    toasts.push(title);
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) =>
    redirects.push(url);

  const originalSubmit = CustomerTaskApi.submitTask;
  CustomerTaskApi.submitTask = async () => {
    throw new ApiRequestError("submit_failed");
  };

  const readyTask = buildTask();
  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      canSubmit: true,
      submitDisabledReason: "",
      busy: {
        loading: false,
        saving: false,
        uploading: false,
        submitting: false,
        navigating: false,
        retrying: false,
      },
    },
    requireToken: () => "h5t1.valid",
    loadTask: async () => readyTask,
  });

  await page.onSubmit.call(ctx);
  assert.equal(redirects.length, 0);
  assert.equal(ctx.data.busy.submitting, false);
  assert.equal(ctx.data.errorState.code, "submit_failed");
  assert.ok(toasts.length > 0);

  CustomerTaskApi.submitTask = originalSubmit;
});

test("missing injury/police items show one Basics recovery action", async () => {
  const page = await loadReviewPage();
  const task = buildTask({
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "",
      police_involved: "",
      accident_datetime: "2026-07-14 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    task_contract: buildContract({
      task_status: "collecting",
      review_ready: false,
      submit_ready: false,
      missing_items: [
        { key: "anyone_injured", label: "是否有人受伤" },
        { key: "police_reported", label: "是否报警" },
      ],
    }),
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.canSubmit, false);
  assert.equal(ctx.data.showSupplementCta, true);
  assert.equal(ctx.data.supplementCtaLabel, "去补充基本资料");
  assert.equal(ctx.data.supplementRoute, "/pages/basics/basics");
  assert.equal(ctx.data.missingRows.length, 2);
  assert.ok(ctx.data.missingRows.every((row: { route: string }) => row.route === "/pages/basics/basics"));
});

test("tapping supplement CTA navigates to Basics once", async () => {
  const page = await loadReviewPage();
  const navigations: string[] = [];
  (globalThis as Record<string, any>).wx.navigateTo = ({
    url,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    navigations.push(url);
    // Intentionally skip complete() so navigating busy remains set.
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      showSupplementCta: true,
      supplementCtaLabel: "去补充基本资料",
      supplementRoute: "/pages/basics/basics",
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

  page.onSupplement.call(ctx);
  page.onSupplement.call(ctx);
  assert.deepEqual(navigations, ["/pages/basics/basics"]);
  assert.equal(ctx.data.busy.navigating, true);
});

test("tapping a missing injury row navigates to Basics", async () => {
  const page = await loadReviewPage();
  const navigations: string[] = [];
  (globalThis as Record<string, any>).wx.navigateTo = ({
    url,
    complete,
  }: {
    url: string;
    complete?: () => void;
  }) => {
    navigations.push(url);
    complete?.();
  };

  const ctx = createPageContext(page, {
    data: {
      ...page.data,
      missingRows: [
        {
          key: "anyone_injured",
          label: "是否有人受伤",
          actionable: true,
          route: "/pages/basics/basics",
        },
      ],
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

  page.onTapMissingRow.call(ctx, {
    currentTarget: { dataset: { index: 0 } },
  });
  assert.deepEqual(navigations, ["/pages/basics/basics"]);
});

test("returning from Basics refreshes Review and clears resolved missing items", async () => {
  const page = await loadReviewPage();
  const incomplete = buildTask({
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "",
      police_involved: "",
      accident_datetime: "2026-07-14 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    task_contract: buildContract({
      task_status: "collecting",
      review_ready: false,
      submit_ready: false,
      missing_items: [
        { key: "anyone_injured", label: "是否有人受伤" },
        { key: "police_involved", label: "是否报警" },
      ],
    }),
  });
  const complete = buildTask();
  let loadCount = 0;
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => {
      loadCount += 1;
      return loadCount === 1 ? incomplete : complete;
    },
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.showSupplementCta, true);
  assert.equal(ctx.data.canSubmit, false);
  assert.ok(ctx.data.missingRows.length >= 1);

  await page.onShow.call(ctx);
  assert.equal(ctx.data.showSupplementCta, false);
  assert.equal(ctx.data.canSubmit, true);
  assert.equal(ctx.data.missingRows.length, 0);
  assert.equal(ctx.data.supplementRoute, "");
});

test("Review has no dead-end when missing Basics fields", async () => {
  const { readFileSync } = await import("node:fs");
  const { join } = await import("node:path");
  const wxml = readFileSync(join(process.cwd(), "pages/review/review.wxml"), "utf8");
  assert.match(wxml, /onTapMissingRow/);
  assert.match(wxml, /onSupplement/);
  assert.match(wxml, /showSupplementCta/);
  assert.match(wxml, /返回我的报案/);

  const page = await loadReviewPage();
  const task = buildTask({
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "",
      police_involved: "",
      accident_datetime: "2026-07-14 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    task_contract: buildContract({
      task_status: "collecting",
      review_ready: false,
      submit_ready: false,
      missing_items: [
        { key: "anyone_injured", label: "是否有人受伤" },
        { key: "police_involved", label: "是否报警" },
      ],
    }),
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });
  await page.onShow.call(ctx);
  assert.equal(ctx.data.showSupplementCta, true);
  assert.notEqual(ctx.data.supplementRoute, "");
  assert.equal(ctx.data.canSubmit, false);
});

test("submitted + missing Basics still offers supplement CTA and blocks re-submit", async () => {
  const page = await loadReviewPage();
  const task = buildTask({
    submitted: true,
    current_step: "done",
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "",
      police_involved: "",
      accident_datetime: "2026-07-14 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    task_contract: buildContract({
      task_status: "submitted",
      review_ready: true,
      submit_ready: false,
      missing_items: [
        { key: "anyone_injured", label: "是否有人受伤" },
        { key: "police_reported", label: "是否报警" },
      ],
      next_action: { type: "go_to_section", target: "review", label: "继续补充资料" },
    }),
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.canSubmit, false);
  assert.match(String(ctx.data.submitDisabledReason), /已提交|无需重复提交/);
  assert.equal(ctx.data.showSupplementCta, true);
  assert.equal(ctx.data.supplementRoute, "/pages/basics/basics");
  assert.ok(ctx.data.missingRows.every((row: { actionable: boolean }) => row.actionable));
});

test("unknown injury/police (live token shape) still shows 去补充基本资料 on Review", async () => {
  const page = await loadReviewPage();
  const task = buildTask({
    submitted: true,
    current_step: "done",
    key_facts: {
      accident_description: "78890kpkpkpkp",
      injury_status: "unknown",
      police_involved: "unknown",
      accident_datetime: "77",
      accident_location: "890u90j0",
      own_vehicle_info: "grweyewrt",
    },
    photo_count: 3,
    missing_info: [
      { field: "anyone_injured", label: "是否有人受伤" },
      { field: "police_involved", label: "是否报警" },
    ],
    task_contract: buildContract({
      task_status: "submitted",
      review_ready: true,
      submit_ready: false,
      missing_items: [
        { key: "anyone_injured", label: "是否有人受伤" },
        { key: "police_involved", label: "是否报警" },
      ],
      next_action: { type: "go_to_section", target: "review", label: "继续补充资料" },
    }),
  });
  const ctx = createPageContext(page, {
    requireToken: () => "h5t1.valid",
    loadTask: async () => task,
  });

  await page.onShow.call(ctx);
  assert.equal(ctx.data.showSupplementCta, true);
  assert.equal(ctx.data.supplementCtaLabel, "去补充基本资料");
  assert.equal(ctx.data.supplementRoute, "/pages/basics/basics");
  assert.ok(ctx.data.missingRows.length >= 2);
});
