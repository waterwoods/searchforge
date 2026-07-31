import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  CASE_STATUS_ROUTE,
  CASE_STATUS_TITLE,
  DEFER_LATER_LABEL,
  LEGACY_WAIT_TODAY,
  OFFICE_PROCESSING_AFTER,
  OFFICE_PROCESSING_TITLE,
  SUBMIT_RECEIPT_COPY,
  TASK_HOME_ROUTE,
  RECEIPT_ROUTE,
  VOLUNTARY_SUPPLEMENT_LABEL,
  buildCaseStatusViewModel,
  buildSubmitReceiptCopy,
  canVoluntarySupplement,
  customerOwesWork,
  isCustomerCaseClosedReadOnly,
  isOfficeProcessingSurface,
  isWaitingBrokerSurface,
  resolveCustomerCaseSurface,
  resolveCustomerCaseSurfaceRoute,
} from "../utils/customerCaseSurface";
import { applySlice1ProjectionToTask } from "../utils/slice1Customer";
import type { CustomerTask, Slice1Projection } from "../types/task";
import { saveResumeToken, loadResumeToken, clearResumeToken } from "../utils/storage";
import { installMiniProgramGlobals } from "./miniprogramMocks";

installMiniProgramGlobals();

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

function baseTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_wait",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "review", "done"],
    current_step: "review",
    completed_count: 1,
    step_total: 3,
    submitted: false,
    phase: "broker_review",
    key_facts: {},
    missing_info: [],
    ...overrides,
  };
}

function waitingProjection(): Slice1Projection {
  return {
    case_id: "case_wait",
    workflow_state: "broker_review_ready",
    aggregate_version: 2,
    customer_next_action: {
      action_type: "wait_for_broker_review",
      title: LEGACY_WAIT_TODAY,
      instructions: "资料已齐，陈总正在审核。",
      request_id: "req_1",
      request_item_id: "",
      item_type: "",
      last_updated_at: "2026-07-22T10:00:00Z",
    },
    queued_request_items: [],
    request_progress: { satisfied: 1, total: 1, remaining: 0 },
    server_timestamp: "2026-07-22T10:00:00Z",
    open_request: {
      request_id: "req_1",
      items: [
        {
          request_item_id: "item_ins",
          request_id: "req_1",
          item_type: "policy_or_insurance_card",
          label: "上传保险卡",
          status: "satisfied",
          position: 1,
          actionable: false,
        },
      ],
      queued_items: [],
      progress: { satisfied: 1, total: 1, remaining: 0 },
    },
    broker_next_action: { action_type: "review_customer_response", status: "review_ready" },
  };
}

function actionableProjection(): Slice1Projection {
  return {
    case_id: "case_wait",
    workflow_state: "waiting_for_customer",
    aggregate_version: 3,
    customer_next_action: {
      action_type: "provide_evidence",
      title: "上传保险卡",
      instructions: "请上传",
      request_id: "req_2",
      request_item_id: "item_2",
      item_type: "policy_or_insurance_card",
      last_updated_at: "2026-07-22T11:00:00Z",
    },
    queued_request_items: [],
    request_progress: { satisfied: 0, total: 1, remaining: 1 },
    server_timestamp: "2026-07-22T11:00:00Z",
    open_request: {
      request_id: "req_2",
      items: [
        {
          request_item_id: "item_2",
          request_id: "req_2",
          item_type: "policy_or_insurance_card",
          label: "上传保险卡",
          status: "active",
          position: 1,
          actionable: true,
        },
      ],
      queued_items: [],
      progress: { satisfied: 0, total: 1, remaining: 1 },
    },
    broker_next_action: null,
  };
}

test("Office processing → Case Status copy; no Task Home / no owed work", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), waitingProjection()),
    constitution_projection: {
      current_stage: "waiting_broker",
      customer: {
        today: LEGACY_WAIT_TODAY,
        why: OFFICE_PROCESSING_TITLE,
        after: OFFICE_PROCESSING_AFTER,
        current_stage: "waiting_broker",
        office_materials_accepted: true,
        office_processing: true,
        trust: { care_line: "办公室处理中", care_note: "如需补充，我们会再通知您" },
        tasks: [
          {
            task_id: "insurance",
            title: "保险卡",
            state: "waiting_broker",
            actionable: false,
          },
        ],
      },
    },
  };
  assert.equal(isOfficeProcessingSurface(task), true);
  assert.equal(customerOwesWork(task), false);
  assert.equal(resolveCustomerCaseSurface(task), "case_status");
  const vm = buildCaseStatusViewModel(task);
  assert.equal(vm.title, OFFICE_PROCESSING_TITLE);
  assert.equal(vm.after, OFFICE_PROCESSING_AFTER);
  assert.equal(vm.statusLabel, "办公室处理中");
});

test("Waiting Broker → case_status route; no Task Home", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), waitingProjection()),
    constitution_projection: {
      current_stage: "waiting_broker",
      customer: {
        today: LEGACY_WAIT_TODAY,
        why: "资料已齐，陈总正在审核。",
        after: "请等待确认。",
        current_stage: "waiting_broker",
        trust: { care_line: "下一步由陈总审核", care_note: "我们会联系您（如需要）" },
        tasks: [
          {
            task_id: "insurance",
            title: "上传保险卡",
            state: "completed",
            actionable: false,
          },
        ],
      },
    },
  };
  assert.equal(customerOwesWork(task), false);
  assert.equal(isWaitingBrokerSurface(task), true);
  assert.equal(resolveCustomerCaseSurface(task), "case_status");
  assert.equal(resolveCustomerCaseSurfaceRoute(task), CASE_STATUS_ROUTE);
  assert.notEqual(resolveCustomerCaseSurfaceRoute(task), TASK_HOME_ROUTE);
});

test("Action Needed → Task Home", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), actionableProjection()),
    constitution_projection: {
      current_stage: "customer_action_needed",
      customer: {
        today: "上传保险卡",
        why: "请上传",
        after: "陈总开始审核。",
        current_stage: "customer_action_needed",
      },
    },
  };
  assert.equal(customerOwesWork(task), true);
  assert.equal(resolveCustomerCaseSurface(task), "task_home");
  assert.equal(resolveCustomerCaseSurfaceRoute(task), TASK_HOME_ROUTE);
});

test("submitted → Receipt (unchanged closed path)", () => {
  const task = baseTask({ submitted: true, current_step: "done" });
  assert.equal(resolveCustomerCaseSurface(task), "receipt");
  assert.equal(resolveCustomerCaseSurfaceRoute(task), RECEIPT_ROUTE);
});

test("Case Status VM replaces 先不用操作 with production title", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), waitingProjection()),
    constitution_projection: {
      current_stage: "waiting_broker",
      customer: {
        today: LEGACY_WAIT_TODAY,
        why: "资料已齐，陈总正在审核。",
        after: "请等待确认。",
        current_stage: "waiting_broker",
        tasks: [{ task_id: "insurance", title: "上传保险卡", state: "completed" }],
      },
    },
  };
  const vm = buildCaseStatusViewModel(task);
  assert.equal(vm.title, CASE_STATUS_TITLE);
  assert.equal(CASE_STATUS_TITLE, "资料已收到，等待陈总审核");
  assert.equal(vm.title.includes(LEGACY_WAIT_TODAY), false);
  assert.ok(vm.bodyLines.length >= 3);
  assert.match(vm.bodyLines.join(""), /已收到/);
  assert.match(vm.bodyLines.join(""), /审核/);
  assert.ok(vm.lastSubmittedLines.length + vm.completedLines.length > 0);
  assert.match(vm.completedLines.join("、") || vm.lastSubmittedLines.join("、"), /保险卡/);
  assert.equal(VOLUNTARY_SUPPLEMENT_LABEL, "继续补充资料");
  assert.equal(SUBMIT_RECEIPT_COPY, "补充资料已收到，陈总会继续审核。");
  assert.equal(DEFER_LATER_LABEL, "先离开，稍后再继续");
  assert.equal(buildSubmitReceiptCopy(task), SUBMIT_RECEIPT_COPY);
});

test("Submit receipt names next step when customer still owes work", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), actionableProjection()),
    constitution_projection: {
      customer: {
        today: "上传事故照片",
        why: "保险卡已收到",
        after: "完成后由陈总审核",
        current_stage: "customer_action_needed",
        trust: { care_line: "陈总已收到资料", care_note: "请继续下一步" },
        tasks: [],
      },
    },
  } as CustomerTask;
  assert.equal(customerOwesWork(task), true);
  assert.equal(buildSubmitReceiptCopy(task), "已收到。下一步：上传事故照片");
});

test("Continue decision preserves Golden resume token", () => {
  clearResumeToken();
  saveResumeToken("h5t1.golden-wait");
  const task = applySlice1ProjectionToTask(baseTask(), waitingProjection());
  assert.equal(resolveCustomerCaseSurfaceRoute(task), CASE_STATUS_ROUTE);
  assert.equal(loadResumeToken(), "h5t1.golden-wait");
  clearResumeToken();
});

test("Task Home wxml no longer presents 先不用操作 waiting block", () => {
  const wxml = readFileSync(join(miniappRoot, "pages/task-home/task-home.wxml"), "utf8");
  assert.equal(wxml.includes("先不用操作"), false);
  assert.equal(wxml.includes("waiting-block"), false);
});

test("Entry uses server Customer Context routing", () => {
  const entryTs = readFileSync(join(miniappRoot, "pages/entry/entry.ts"), "utf8");
  assert.match(entryTs, /resolveCustomerContext/);
  assert.match(entryTs, /routeForCustomerNextAction/);
  assert.equal(entryTs.includes('"/pages/task-home/task-home"'), false);
});

test("Case Status page registered and titled", () => {
  const appJson = JSON.parse(readFileSync(join(miniappRoot, "app.json"), "utf8")) as {
    pages?: string[];
  };
  assert.ok(appJson.pages?.includes("pages/case-status/case-status"));
  assert.equal(appJson.pages?.[0], "pages/start-claim/start-claim");
  const wxml = readFileSync(join(miniappRoot, "pages/case-status/case-status.wxml"), "utf8");
  assert.match(wxml, /\{\{title\}\}/);
  assert.match(wxml, /联系陈总/);
  assert.match(wxml, /查看已提交资料/);
  assert.match(wxml, /voluntarySupplementLabel/);
  assert.match(wxml, /showVoluntarySupplement/);
  assert.match(wxml, /btn-primary-append/);
  const ts = readFileSync(join(miniappRoot, "pages/case-status/case-status.ts"), "utf8");
  assert.match(ts, /customerOwesWork/);
  assert.match(ts, /TASK_HOME_ROUTE/);
  assert.match(ts, /onVoluntarySupplement/);
  assert.match(ts, /canVoluntarySupplement/);
  assert.match(ts, /VOLUNTARY_SUPPLEMENT_LABEL/);
  assert.match(ts, /pages\/photos\/photos/);
  assert.match(ts, /pages\/story\/story/);
});

test("Waiting Broker allows voluntary supplement; closed does not", () => {
  const waiting = applySlice1ProjectionToTask(baseTask(), waitingProjection());
  assert.equal(canVoluntarySupplement(waiting), true);
  assert.equal(isCustomerCaseClosedReadOnly(waiting), false);

  const closed = baseTask({
    submitted: true,
    current_step: "done",
    case_closed_read_only: true,
    case_status: "closed",
  });
  assert.equal(isCustomerCaseClosedReadOnly(closed), true);
  assert.equal(canVoluntarySupplement(closed), false);
});

test("Request More Action Needed prioritizes Task Home over Case Status supplement", () => {
  const task = {
    ...applySlice1ProjectionToTask(baseTask(), actionableProjection()),
    constitution_projection: {
      current_stage: "customer_action_needed",
      customer: {
        today: "上传保险卡",
        why: "请上传",
        after: "陈总开始审核。",
        current_stage: "customer_action_needed",
      },
    },
  };
  assert.equal(customerOwesWork(task), true);
  assert.equal(resolveCustomerCaseSurface(task), "task_home");
  assert.equal(canVoluntarySupplement(task), false);
});

test("One Active Case: voluntary supplement stays on same resume token", () => {
  clearResumeToken();
  saveResumeToken("h5t1.voluntary-append");
  const waiting = applySlice1ProjectionToTask(baseTask(), waitingProjection());
  assert.equal(canVoluntarySupplement(waiting), true);
  assert.equal(resolveCustomerCaseSurfaceRoute(waiting), CASE_STATUS_ROUTE);
  assert.equal(loadResumeToken(), "h5t1.voluntary-append");
  clearResumeToken();
});
