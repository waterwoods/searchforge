/**
 * P0 Founder QA UX Phase 2 — one QR scan, same persisted session,
 * foreground/page-show refresh discovers sequential Request More.
 */

import test from "node:test";
import assert from "node:assert/strict";

import {
  getLatestPage,
  installMiniProgramGlobals,
  resetMiniProgramCaptures,
} from "./miniprogramMocks";
import { CustomerTaskApi } from "../services/taskApi";
import { ApiRequestError } from "../utils/request";
import {
  clearResumeToken,
  loadResumeToken,
  saveResumeToken,
} from "../utils/storage";
import {
  persistLaunchToken,
  resolveTaskLaunchContext,
} from "../services/taskLaunchContext";
import type { CustomerTask, Slice1Projection } from "../types/task";

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

function installGetApp(appState: Record<string, unknown>) {
  (globalThis as Record<string, unknown>).getApp = () => appState;
}

function buildSlice1Projection(overrides?: Partial<Slice1Projection>): Slice1Projection {
  return {
    case_id: "case_phase2",
    workflow_state: "broker_more_requested",
    aggregate_version: 2,
    customer_next_action: {
      action_type: "upload_evidence",
      request_id: "req_1",
      request_item_id: "item_insurance",
      title: "上传保险卡",
      instructions: "请上传清晰的保险卡照片",
      required_input: "policy_or_insurance_card",
      status: "active",
      ordering: { position: 1, total: 1 },
      allowed_actions: ["submit_request_item"],
      version: 2,
      last_updated_at: "2026-07-22T00:00:00Z",
    },
    broker_next_action: {
      action_type: "wait_for_customer_item",
      status: "waiting_for_customer",
      request_id: "req_1",
      version: 2,
    },
    open_request: {
      request_id: "req_1",
      status: "open",
      reason: "Phase2",
      active_item: {
        request_item_id: "item_insurance",
        request_id: "req_1",
        item_type: "policy_or_insurance_card",
        label: "上传保险卡",
        instructions: "请上传清晰的保险卡照片",
        required: true,
        position: 1,
        status: "active",
        actionable: true,
      },
      queued_items: [],
      items: [
        {
          request_item_id: "item_insurance",
          request_id: "req_1",
          item_type: "policy_or_insurance_card",
          label: "上传保险卡",
          instructions: "请上传清晰的保险卡照片",
          required: true,
          position: 1,
          status: "active",
          actionable: true,
        },
      ],
      progress: { satisfied: 0, total: 1, remaining: 1 },
    },
    queued_request_items: [],
    request_progress: { satisfied: 0, total: 1, remaining: 1 },
    server_timestamp: "2026-07-22T00:00:00Z",
    latest_events: [],
    ...overrides,
  };
}

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  const projection = (overrides?.slice1_projection ||
    buildSlice1Projection()) as Slice1Projection;
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_phase2",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "review", "done"],
    current_step: "review",
    completed_count: 2,
    step_total: 3,
    submitted: false,
    phase: "broker_needs_more_info",
    key_facts: { own_vehicle_info: "2020 Toyota Camry" },
    missing_info: [],
    slice1_projection: projection,
    task_contract_v1: {
      contract_version: "1",
      task_id: "nonce",
      task_type: "claim_request_more",
      workflow_state: projection.workflow_state,
      aggregate_version: projection.aggregate_version,
      next_action: projection.customer_next_action,
      queued_request_items: projection.queued_request_items,
      request_progress: projection.request_progress,
      server_timestamp: projection.server_timestamp,
    },
    ...overrides,
  };
}

function waitingTask(): CustomerTask {
  return buildTask({
    submitted: true,
    phase: "submitted",
    slice1_projection: buildSlice1Projection({
      workflow_state: "broker_review_ready",
      aggregate_version: 3,
      customer_next_action: {
        action_type: "wait_for_broker_review",
        request_id: "req_1",
        request_item_id: "item_insurance",
        title: "等待陈总查看",
        instructions: "资料已提交",
        required_input: "",
        status: "waiting",
        ordering: { position: 1, total: 1 },
        allowed_actions: [],
        version: 3,
        last_updated_at: "2026-07-22T01:00:00Z",
      },
      open_request: {
        request_id: "req_1",
        status: "completed",
        reason: "Phase2",
        active_item: null,
        queued_items: [],
        items: [],
        progress: { satisfied: 1, total: 1, remaining: 0 },
      },
      request_progress: { satisfied: 1, total: 1, remaining: 0 },
    }),
  });
}

function vehicleRequestTask(): CustomerTask {
  return buildTask({
    slice1_projection: buildSlice1Projection({
      workflow_state: "broker_more_requested",
      aggregate_version: 5,
      customer_next_action: {
        action_type: "provide_fact",
        request_id: "req_2",
        request_item_id: "item_vehicle",
        title: "车辆信息",
        instructions: "请补充本次事故车辆的基本信息",
        required_input: "vehicle_information",
        status: "active",
        ordering: { position: 1, total: 1 },
        allowed_actions: ["submit_request_item"],
        version: 5,
        last_updated_at: "2026-07-22T02:00:00Z",
      },
      open_request: {
        request_id: "req_2",
        status: "open",
        reason: "Need vehicle",
        active_item: {
          request_item_id: "item_vehicle",
          request_id: "req_2",
          item_type: "vehicle_information",
          label: "车辆信息",
          instructions: "请补充本次事故车辆的基本信息",
          required: true,
          position: 1,
          status: "active",
          actionable: true,
        },
        queued_items: [],
        items: [
          {
            request_item_id: "item_vehicle",
            request_id: "req_2",
            item_type: "vehicle_information",
            label: "车辆信息",
            instructions: "请补充本次事故车辆的基本信息",
            required: true,
            position: 1,
            status: "active",
            actionable: true,
          },
        ],
        progress: { satisfied: 0, total: 1, remaining: 1 },
      },
      request_progress: { satisfied: 0, total: 1, remaining: 1 },
    }),
  });
}

test("persisted QA binding is reused without minting a new token", () => {
  clearResumeToken();
  const launchToken = "h5t1.phase2-one-scan";
  persistLaunchToken({ token: launchToken, source: "launch_query" });
  assert.equal(loadResumeToken(), launchToken);

  const resumed = resolveTaskLaunchContext({});
  assert.equal(resumed?.source, "resume_storage");
  assert.equal(resumed?.token, launchToken);

  // Second "task discovery" still resolves the same stored token — no QR/token mint.
  const again = resolveTaskLaunchContext({});
  assert.equal(again?.token, launchToken);
  assert.equal(loadResumeToken(), launchToken);
  clearResumeToken();
});

test("Task Home page-show rehydrate discovers second Request More on same token", async () => {
  const page = await loadPage("../pages/task-home/task-home");
  const token = "h5t1.phase2-home";
  const appState: Record<string, unknown> = { taskToken: token };
  installGetApp(appState);

  const tokens: string[] = [];
  let round = 0;
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async (t: string) => {
    tokens.push(t);
    round += 1;
    return round === 1 ? buildTask() : vehicleRequestTask();
  };

  const ctx = createPageContext(page, {
    applyConstitutionOverlay(task: CustomerTask) {
      this.data.__lastTask = task;
    },
  });

  // First show path (after cold load already consumed via ownerLoad pattern).
  ctx.__taskPageState = {
    latestRequestSeq: 0,
    activeLoadPromise: null,
    activeLoadSeq: null,
    pageAlive: true,
    firstShowConsumed: true,
  };

  page.onShow.call(ctx);
  await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));

  assert.deepEqual(tokens, [token]);
  assert.equal(
    (ctx.data.__lastTask as CustomerTask)?.slice1_projection?.customer_next_action
      ?.required_input,
    "policy_or_insurance_card",
  );

  // Founder foregrounds after Broker sends task 2 — same token, new projection.
  page.onShow.call(ctx);
  await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));

  assert.deepEqual(tokens, [token, token], "second task must reuse same token");
  assert.equal(
    (ctx.data.__lastTask as CustomerTask)?.slice1_projection?.customer_next_action
      ?.required_input,
    "vehicle_information",
  );
  assert.equal(
    (ctx.data.__lastTask as CustomerTask)?.slice1_projection?.customer_next_action?.title,
    "车辆信息",
  );

  CustomerTaskApi.getTask = originalGetTask;
});

test("Receipt page-show replaces waiting state with new Request More", async () => {
  const page = await loadPage("../pages/receipt/receipt");
  const token = "h5t1.phase2-receipt";
  installGetApp({ taskToken: token });

  const tokens: string[] = [];
  let round = 0;
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async (t: string) => {
    tokens.push(t);
    round += 1;
    return round === 1 ? waitingTask() : vehicleRequestTask();
  };

  const ctx = createPageContext(page, { route: "/pages/receipt/receipt" });
  ctx.__taskPageState = {
    latestRequestSeq: 0,
    activeLoadPromise: null,
    activeLoadSeq: null,
    pageAlive: true,
    firstShowConsumed: true,
  };

  await page.onShow.call(ctx);
  assert.equal(ctx.data.slice1WaitingForBroker, true);
  assert.equal(ctx.data.status, "已提交");

  await page.onShow.call(ctx);
  assert.deepEqual(tokens, [token, token]);
  assert.equal(ctx.data.slice1WaitingForBroker, false);
  assert.equal(ctx.data.slice1PrimaryActionable, true);
  assert.match(String(ctx.data.slice1PrimaryLabel || ctx.data.nextStep || ""), /车辆|补充/);

  CustomerTaskApi.getTask = originalGetTask;
});

test("duplicate onLoad+onShow lifecycle joins one request (no unsafe duplicate)", async () => {
  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as {
    data: Record<string, unknown>;
    methods: Record<string, (...args: any[]) => any>;
  };
  const token = "h5t1.phase2-join";
  installGetApp({ taskToken: token });

  let resolveSlow: ((value: CustomerTask) => void) | null = null;
  const slow = new Promise<CustomerTask>((resolve) => {
    resolveSlow = resolve;
  });
  let calls = 0;
  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async () => {
    calls += 1;
    return slow;
  };

  const data = JSON.parse(JSON.stringify(behavior.data));
  const ctx: Record<string, any> = {
    data,
    route: "/pages/task-home/task-home",
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...behavior.methods,
  };

  const owner = behavior.methods.ensureTaskInitialized.call(ctx, { ownerLoad: true });
  const show = behavior.methods.ensureTaskInitialized.call(ctx);
  resolveSlow?.(buildTask());
  const [a, b] = await Promise.all([owner, show]);

  assert.equal(calls, 1);
  assert.equal(a?.case_id, "case_phase2");
  assert.equal(b?.case_id, "case_phase2");

  CustomerTaskApi.getTask = originalGetTask;
});

test("expired session clears binding and shows restart redirect", async () => {
  clearResumeToken();
  saveResumeToken("h5t1.phase2-expired");
  const redirects: string[] = [];
  (globalThis as Record<string, any>).wx.redirectTo = ({ url }: { url: string }) => {
    redirects.push(url);
  };

  const module = await import("../behaviors/taskPage");
  const behavior = module.taskPage as {
    data: Record<string, unknown>;
    methods: Record<string, (...args: any[]) => any>;
  };
  const appState: Record<string, unknown> = {
    taskToken: "h5t1.phase2-expired",
    task: buildTask(),
  };
  installGetApp(appState);

  const originalGetTask = CustomerTaskApi.getTask;
  CustomerTaskApi.getTask = async () => {
    throw new ApiRequestError("invalid_or_expired_task_link", 403);
  };

  const data = JSON.parse(JSON.stringify(behavior.data));
  const ctx: Record<string, any> = {
    data,
    route: "/pages/receipt/receipt",
    setData(patch: Record<string, unknown>) {
      Object.assign(this.data, patch);
    },
    ...behavior.methods,
  };

  await behavior.methods.rehydrateAuthoritativeTask.call(ctx);

  assert.equal(loadResumeToken(), "");
  assert.equal(appState.taskToken, "");
  assert.deepEqual(redirects, ["/pages/error/error?code=invalid_or_expired_task_link"]);
  assert.match(String((ctx.data.errorState as { message: string }).message), /链接已失效/);

  CustomerTaskApi.getTask = originalGetTask;
  clearResumeToken();
});

test("App.onShow does not refresh current-task (page show owns Phase 2 refresh)", async () => {
  // Avoid duplicate requests: App foreground only logs; Page.onShow rehydrates.
  const fs = await import("node:fs");
  const path = await import("node:path");
  const source = fs.readFileSync(
    path.join(process.cwd(), "app.ts"),
    "utf8",
  );
  assert.match(source, /onShow\s*\(/);
  assert.doesNotMatch(source, /CustomerTaskApi|getTask|ensureTaskInitialized|rehydrateAuthoritativeTask/);
  assert.match(source, /logPreviewLaunch\("app\.onShow"/);
});
