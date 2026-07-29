/**
 * P24D2.1 — Production customer pages bind Focus via resolveCustomerConstitutionFromTask.
 * Values must come from mocked API constitution_projection, not page-local Camry hardcoding.
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  applySlice1ProjectionToTask,
  mapSlice1CustomerView,
} from "../utils/slice1Customer";
import {
  resolveCustomerConstitutionFromTask,
  type ConstitutionProjection,
} from "../utils/resolveCustomerConstitution";
import { resolveTaskViewModel } from "../utils/resolveTaskViewModel";
import type { CustomerTask, Slice1Projection } from "../types/task";

function camryBeforeServer(): ConstitutionProjection {
  return {
    projection_version: 1,
    case_id: "case-chen-camry",
    current_stage: "customer_action_needed",
    customer: {
      today: "上传保险卡",
      why: "事故经过和现场照片已经完成。",
      after: "陈总会尽快联系您。",
      trust: {
        care_line: "陈总已收到资料",
        care_note: "如有需要，我们会联系您",
      },
      current_stage: "customer_action_needed",
    },
  };
}

function camryAfterServer(): ConstitutionProjection {
  return {
    projection_version: 1,
    case_id: "case-chen-camry",
    current_stage: "waiting_broker",
    customer: {
      today: "先不用操作",
      why: "资料已齐，陈总正在看。",
      after: "请等待确认。",
      trust: {
        care_line: "下一步由陈总联系您",
        care_note: "我们会联系您（如需要）",
      },
      current_stage: "waiting_broker",
    },
  };
}

function baseTask(): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake_form",
    case_id: "case-chen-camry",
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
}

function actionableProjection(): Slice1Projection {
  return {
    case_id: "case-chen-camry",
    workflow_state: "broker_more_requested",
    aggregate_version: 3,
    customer_next_action: {
      action_type: "provide_evidence",
      request_id: "req_camry",
      request_item_id: "item_card",
      title: "请上传保险卡（Slice1 local）",
      instructions: "Slice1 local why — must not win when server present",
      required_input: "policy_or_insurance_card",
      status: "active",
      ordering: { position: 1, total: 1 },
      allowed_actions: ["submit_request_item"],
      version: 3,
      last_updated_at: "2026-07-17T00:00:00Z",
    },
    broker_next_action: {
      action_type: "wait_for_customer_item",
      status: "waiting_for_customer",
      request_id: "req_camry",
      version: 3,
    },
    open_request: {
      request_id: "req_camry",
      status: "open",
      active_item: {
        request_item_id: "item_card",
        request_id: "req_camry",
        item_type: "policy_or_insurance_card",
        label: "保险卡",
        instructions: "请上传",
        required: true,
        position: 1,
        status: "active",
        actionable: true,
      },
      queued_items: [],
      items: [],
      progress: { satisfied: 0, total: 1, remaining: 1 },
    },
    queued_request_items: [],
    request_progress: { satisfied: 0, total: 1, remaining: 1 },
    server_timestamp: "2026-07-17T00:00:00Z",
  };
}

function waitingProjection(): Slice1Projection {
  return {
    case_id: "case-chen-camry",
    workflow_state: "waiting_broker_review",
    aggregate_version: 4,
    customer_next_action: {
      action_type: "wait_for_broker_review",
      request_id: "req_camry",
      request_item_id: "",
      title: "资料已提交（Slice1 local）",
      instructions: "Slice1 waiting why — must not win when server present",
      required_input: "",
      status: "active",
      ordering: { position: 1, total: 1 },
      allowed_actions: [],
      version: 4,
      last_updated_at: "2026-07-17T01:00:00Z",
    },
    broker_next_action: {
      action_type: "review_customer_response",
      status: "review_ready",
      request_id: "req_camry",
      version: 4,
    },
    open_request: null,
    queued_request_items: [],
    request_progress: { satisfied: 1, total: 1, remaining: 0 },
    server_timestamp: "2026-07-17T01:00:00Z",
  };
}

test("Camry before-upload: production view prefers mocked API Constitution", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), actionableProjection()),
    constitution_projection: camryBeforeServer(),
  };
  const resolved = resolveCustomerConstitutionFromTask(task);
  assert.equal(resolved.fieldAuthority.today, "server");
  assert.equal(resolved.today, "上传保险卡");
  assert.equal(resolved.why, "事故经过和现场照片已经完成。");
  assert.equal(resolved.after, "陈总会尽快联系您。");
  assert.equal(resolved.careLine, "陈总已收到资料");
  assert.equal(resolved.careNote, "如有需要，我们会联系您");
  assert.equal(resolved.currentStage, "customer_action_needed");

  const view = mapSlice1CustomerView(task);
  assert.equal(view.constitutionToday, "上传保险卡");
  assert.equal(view.constitutionWhy, "事故经过和现场照片已经完成。");
  assert.equal(view.constitutionAfter, "陈总会尽快联系您。");
  assert.equal(view.nextAction?.title, "上传保险卡");
  assert.equal(view.nextAction?.instructions, "事故经过和现场照片已经完成。");
  assert.equal(view.primaryCtaLabel, "上传保险卡");
  assert.equal(view.waitingForBroker, false);

  const vm = resolveTaskViewModel(task, null, { route: "/pages/task-home/task-home" });
  assert.equal(vm.instruction, "上传保险卡");
  assert.equal(vm.cta.label, "上传保险卡");
});

test("Camry after-upload: Focus from server; wait CTA unchanged", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), waitingProjection()),
    constitution_projection: camryAfterServer(),
  };
  const resolved = resolveCustomerConstitutionFromTask(task);
  assert.equal(resolved.today, "先不用操作");
  assert.equal(resolved.why, "资料已齐，陈总正在看。");
  assert.equal(resolved.after, "请等待确认。");
  assert.equal(resolved.careLine, "下一步由陈总联系您");
  assert.equal(resolved.careNote, "我们会联系您（如需要）");
  assert.equal(resolved.currentStage, "waiting_broker");
  assert.equal(resolved.fieldAuthority.today, "server");

  const view = mapSlice1CustomerView(task);
  assert.equal(view.waitingForBroker, true);
  assert.equal(view.constitutionToday, "先不用操作");
  assert.equal(view.nextAction?.title, "先不用操作");
  assert.equal(view.nextAction?.instructions, "资料已齐，陈总正在看。");
  // Cap3B wait acknowledgment CTA must remain (not Focus Today).
  assert.equal(view.primaryCtaLabel, "已提交，陈总正在看");

  const vm = resolveTaskViewModel(task, null, { route: "/pages/task-home/task-home" });
  assert.equal(vm.instruction, "先不用操作");
  assert.equal(vm.cta.label, "已提交，陈总正在看");
  assert.equal(vm.cta.disabled, true);
});

test("absent Constitution: production Slice1 copy unchanged", () => {
  const task = applySlice1ProjectionToTask(baseTask(), actionableProjection());
  const view = mapSlice1CustomerView(task);
  assert.equal(view.nextAction?.title, "请上传保险卡（Slice1 local）");
  assert.equal(view.nextAction?.instructions, "Slice1 local why — must not win when server present");
  assert.equal(view.primaryCtaLabel, "请上传保险卡（Slice1 local）");
  assert.equal(view.constitutionToday, "请上传保险卡（Slice1 local）");
  assert.ok(view.constitutionToday, "no blank Today when Constitution absent");

  const vm = resolveTaskViewModel(task, null, { route: "/pages/task-home/task-home" });
  assert.equal(vm.instruction, "请上传保险卡（Slice1 local）");
  assert.match(vm.cta.label, /保险卡|补充/);
});

test("partial server Constitution uses task-contract / Slice1 field-by-field", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), actionableProjection()),
    constitution_projection: {
      customer: {
        today: "上传保险卡",
        why: null,
        after: "",
      },
    },
  };
  const resolved = resolveCustomerConstitutionFromTask(task);
  assert.equal(resolved.today, "上传保险卡");
  assert.equal(resolved.fieldAuthority.today, "server");
  assert.equal(resolved.why, "Slice1 local why — must not win when server present");
  assert.equal(resolved.fieldAuthority.why, "task_contract");
});
