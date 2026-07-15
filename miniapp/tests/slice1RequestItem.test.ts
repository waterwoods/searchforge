import test from "node:test";
import assert from "node:assert/strict";

import {
  applySlice1ProjectionToTask,
  extractSlice1Projection,
  factFieldForItemType,
  isEvidenceItemType,
  isSlice1CustomerFlow,
  isTextItemType,
  mapSlice1CustomerView,
  normalizeVin,
  REQUEST_ITEM_ROUTE,
  validateFreeText,
  validateVin,
} from "../utils/slice1Customer";
import {
  clearRequestItemDraft,
  loadRequestItemDraft,
  newClientDraftId,
  newCommandIdentity,
  saveRequestItemDraft,
} from "../utils/requestItemDraft";
import { resolveTaskViewModel } from "../utils/resolveTaskViewModel";
import type { CustomerTask, Slice1Projection } from "../types/task";
import { installMiniProgramGlobals, getLatestPage, resetMiniProgramCaptures } from "./miniprogramMocks";

installMiniProgramGlobals();

const storage = new Map<string, unknown>();
(globalThis as { wx: Record<string, unknown> }).wx = {
  ...(globalThis as { wx: Record<string, unknown> }).wx,
  setStorageSync: (key: string, value: unknown) => {
    storage.set(key, value);
  },
  getStorageSync: (key: string) => storage.get(key),
  removeStorageSync: (key: string) => {
    storage.delete(key);
  },
};

function buildProjection(overrides?: Partial<Slice1Projection>): Slice1Projection {
  return {
    case_id: "case_1",
    workflow_state: "broker_more_requested",
    aggregate_version: 2,
    customer_next_action: {
      action_type: "provide_fact",
      request_id: "req_1",
      request_item_id: "item_1",
      title: "请提供 VIN",
      instructions: "请填写车辆 VIN",
      required_input: "vin",
      status: "active",
      ordering: { position: 1, total: 2 },
      allowed_actions: ["submit_request_item"],
      version: 2,
      last_updated_at: "2026-07-15T00:00:00Z",
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
      active_item: {
        request_item_id: "item_1",
        request_id: "req_1",
        item_type: "vin",
        label: "VIN",
        instructions: "请填写车辆 VIN",
        required: true,
        position: 1,
        status: "active",
        actionable: true,
      },
      queued_items: [
        {
          request_item_id: "item_2",
          request_id: "req_1",
          item_type: "policy_or_insurance_card",
          label: "Insurance card",
          instructions: "请上传保险卡",
          required: true,
          position: 2,
          status: "queued",
          actionable: false,
        },
      ],
      items: [
        {
          request_item_id: "item_1",
          request_id: "req_1",
          item_type: "vin",
          label: "VIN",
          instructions: "请填写车辆 VIN",
          required: true,
          position: 1,
          status: "active",
          actionable: true,
        },
        {
          request_item_id: "item_2",
          request_id: "req_1",
          item_type: "policy_or_insurance_card",
          label: "Insurance card",
          instructions: "请上传保险卡",
          required: true,
          position: 2,
          status: "queued",
          actionable: false,
        },
      ],
      progress: { satisfied: 0, total: 2, remaining: 2 },
    },
    queued_request_items: [
      {
        request_item_id: "item_2",
        request_id: "req_1",
        item_type: "policy_or_insurance_card",
        label: "Insurance card",
        instructions: "请上传保险卡",
        required: true,
        position: 2,
        status: "queued",
        actionable: false,
      },
    ],
    request_progress: { satisfied: 0, total: 2, remaining: 2 },
    server_timestamp: "2026-07-15T00:00:00Z",
    ...overrides,
  };
}

function buildTask(projection?: Slice1Projection | null): CustomerTask {
  const base: CustomerTask = {
    lane: "claim",
    flow: "claim_intake_form",
    case_id: "case_1",
    title: "我的事故资料",
    safety_copy: "safety",
    steps: [],
    current_step: "review",
    completed_count: 3,
    step_total: 4,
    submitted: true,
    phase: "broker_needs_more_info",
    key_facts: {},
    missing_info: [],
  };
  if (!projection) return base;
  return applySlice1ProjectionToTask(base, projection);
}

test("active Next Action maps correctly", () => {
  const view = mapSlice1CustomerView(buildTask(buildProjection()));
  assert.equal(view.enabled, true);
  assert.equal(view.nextAction?.request_item_id, "item_1");
  assert.equal(view.primaryActionable, true);
  assert.equal(view.primaryRoute, REQUEST_ITEM_ROUTE);
});

test("queued items are not primary", () => {
  const view = mapSlice1CustomerView(buildTask(buildProjection()));
  assert.equal(view.queuedItems.length, 1);
  assert.equal(view.queuedItems[0].actionable, false);
  assert.notEqual(view.queuedItems[0].request_item_id, view.nextAction?.request_item_id);
});

test("satisfied items map correctly", () => {
  const projection = buildProjection({
    open_request: {
      request_id: "req_1",
      status: "open",
      items: [
        {
          request_item_id: "item_1",
          request_id: "req_1",
          item_type: "vin",
          label: "VIN",
          instructions: "",
          required: true,
          position: 1,
          status: "satisfied",
          actionable: false,
        },
        {
          request_item_id: "item_2",
          request_id: "req_1",
          item_type: "free_text",
          label: "Date",
          instructions: "",
          required: true,
          position: 2,
          status: "active",
          actionable: true,
        },
      ],
      queued_items: [],
      progress: { satisfied: 1, total: 2, remaining: 1 },
    },
    customer_next_action: {
      action_type: "provide_fact",
      request_id: "req_1",
      request_item_id: "item_2",
      title: "确认事故时间",
      instructions: "请确认日期",
      required_input: "free_text",
    },
    queued_request_items: [],
    request_progress: { satisfied: 1, total: 2, remaining: 1 },
  });
  const view = mapSlice1CustomerView(buildTask(projection));
  assert.equal(view.satisfiedItems.length, 1);
  assert.equal(view.satisfiedItems[0].request_item_id, "item_1");
  assert.equal(view.nextAction?.request_item_id, "item_2");
});

test("waiting-for-Broker state has no submission action", () => {
  const projection = buildProjection({
    workflow_state: "broker_review_ready",
    customer_next_action: {
      action_type: "wait_for_broker_review",
      request_id: "req_1",
      request_item_id: null,
      title: "资料已提交给陈总审核",
      instructions: "陈总会查看你补充的资料。",
      required_input: null,
    },
    open_request: {
      request_id: "req_1",
      status: "completed",
      items: [],
      queued_items: [],
      progress: { satisfied: 2, total: 2, remaining: 0 },
    },
    queued_request_items: [],
    request_progress: { satisfied: 2, total: 2, remaining: 0 },
  });
  const view = mapSlice1CustomerView(buildTask(projection));
  assert.equal(view.waitingForBroker, true);
  assert.equal(view.primaryActionable, false);
  assert.equal(view.primaryRoute, "");
});

test("legacy case maps to legacy behavior", () => {
  const task = buildTask(null);
  assert.equal(isSlice1CustomerFlow(task), false);
  assert.equal(mapSlice1CustomerView(task).legacyFallback, true);
  const vm = resolveTaskViewModel(task, null, { route: "/pages/task-home/task-home" });
  assert.notEqual(vm.cta.target, REQUEST_ITEM_ROUTE);
});

test("item type helpers and validators", () => {
  assert.equal(isEvidenceItemType("policy_or_insurance_card"), true);
  assert.equal(isEvidenceItemType("photo_evidence"), true);
  assert.equal(isTextItemType("vin"), true);
  assert.equal(factFieldForItemType("vin"), "vin");
  assert.equal(normalizeVin("1hg cm82633a004352"), "1HGCM82633A004352");
  assert.equal(validateVin("1HGCM82633A004352").ok, true);
  assert.equal(validateVin("SHORT").ok, false);
  assert.equal(validateFreeText("").ok, false);
  assert.equal(validateFreeText("事故发生在周一上午").ok, true);
});

test("draft restore matches case/request/item and rejects stale item", () => {
  storage.clear();
  const draftId = newClientDraftId();
  saveRequestItemDraft({
    version: 1,
    case_id: "case_1",
    request_id: "req_1",
    request_item_id: "item_1",
    item_type: "vin",
    draft_value: "1HGCM82633A004352",
    client_draft_id: draftId,
    updated_at: "2026-07-15T00:00:00Z",
  });
  const ok = loadRequestItemDraft("case_1", "req_1", "item_1");
  assert.equal(ok?.draft_value, "1HGCM82633A004352");
  const stale = loadRequestItemDraft("case_1", "req_1", "item_2");
  assert.equal(stale, null);
  clearRequestItemDraft("case_1", "req_1", "item_1");
  assert.equal(loadRequestItemDraft("case_1", "req_1", "item_1"), null);
});

test("command identity is stable for retry reuse", () => {
  const first = newCommandIdentity("cmd_request_item");
  assert.ok(first.command_id.startsWith("cmd_request_item_"));
  assert.ok(first.idempotency_key.startsWith("idem_"));
  assert.notEqual(first.command_id, first.idempotency_key);
});

test("resolveTaskViewModel prefers Slice 1 server action", () => {
  const task = buildTask(buildProjection());
  const vm = resolveTaskViewModel(task, null, { route: "/pages/task-home/task-home" });
  assert.equal(vm.cta.target, REQUEST_ITEM_ROUTE);
  assert.equal(vm.missingItems.every((row) => row.actionable === false), true);
  assert.match(vm.statusLabel, /补充|审核/);
});

test("extractSlice1Projection reads additive fields", () => {
  const task = buildTask(buildProjection());
  assert.ok(extractSlice1Projection(task));
  assert.equal(extractSlice1Projection(task)?.aggregate_version, 2);
});

test("request-item page first-render defaults are defined", async () => {
  resetMiniProgramCaptures();
  await import("../pages/request-item/request-item");
  const page = getLatestPage().options as { data: Record<string, unknown> };
  const data = page.data;
  for (const key of [
    "loading",
    "pageError",
    "task",
    "nextAction",
    "queuedItems",
    "satisfiedItems",
    "progress",
    "brokerStatus",
    "submissionState",
    "uploadItems",
    "draftValue",
    "retryAvailable",
    "lastServerUpdate",
    "isDestroyed",
    "requestGeneration",
  ]) {
    assert.notEqual(data[key], undefined, `${key} must be defined`);
  }
  assert.equal(Array.isArray(data.queuedItems), true);
  assert.equal(Array.isArray(data.uploadItems), true);
  assert.equal(typeof data.requestGeneration, "number");
});
