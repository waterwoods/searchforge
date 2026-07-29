/**
 * P26H-UI — Mini Program Golden UI Journey (click / render / complete).
 *
 * Uses the repo's existing Page() + miniprogramMocks automation path.
 * Does not invent completion in frontend-only state: destination pages must
 * bootstrap, render primary UI, and complete through page methods.
 */

import type { CustomerConstitutionTaskCard, CustomerTask } from "../types/task";
import {
  resolveCustomerTaskCardsFromTask,
  type CustomerTaskCardView,
} from "./resolveCustomerTaskCards";
import {
  insuranceUploadPrimaryUiPresent,
  resolveRequestItemWorkSurface,
} from "./requestItemWorkSurface";
import { REQUEST_ITEM_ROUTE } from "./slice1Customer";

export type UiLayer =
  | "Case Creation"
  | "Task Home"
  | "Mini Program Route"
  | "Page Bootstrap"
  | "Upload State Machine"
  | "Constitution Projection"
  | "Broker Follow-Up";

export type UiFailure = {
  task: string;
  source: string;
  expectedPage: string;
  actualPage: string;
  layer: UiLayer;
  detail?: string;
};

export type UiJourneyReport = {
  ok: boolean;
  checks: string[];
  failures: UiFailure[];
};

function fail(
  report: UiJourneyReport,
  failure: UiFailure,
): void {
  report.failures.push(failure);
}

function pass(report: UiJourneyReport, label: string): void {
  report.checks.push(label);
}

export function buildFreshSystemDefaultTask(overrides?: Partial<CustomerTask>): CustomerTask {
  const caseId = `case_p26h_ui_${Date.now().toString(36)}`;
  return {
    lane: "claim",
    flow: "claim_intake_form",
    case_id: caseId,
    title: "我的报案",
    safety_copy: "这是给办公室整理用的记录，不等于向保险公司正式报案。",
    steps: ["start", "injury", "time_location", "story", "vehicle_other_party", "evidence", "review", "done"],
    current_step: "review",
    completed_count: 4,
    step_total: 5,
    submitted: false,
    phase: "accident_basics_complete",
    key_facts: {
      accident_description: "停车场倒车碰撞，前保险杠受损",
      accident_datetime: "2026-07-18 10:00",
      accident_location: "停车场",
      injury_status: "no",
      anyone_injured: "no",
    },
    missing_info: [],
    photo_count: 0,
    upload_url: "https://example.com/h5t1.p26h_ui_upload",
    constitution_projection: {
      customer: {
        today: "上传保险卡",
        why: "事故经过已填写，请继续上传保险卡。",
        after: "陈总会尽快联系您。",
        current_stage: "customer_action_needed",
        trust: { care_line: "陈总已收到资料", care_note: "如有需要，我们会联系您" },
        tasks: [
          {
            task_id: "accident_story",
            title: "事故经过",
            state: "completed",
            progress: { completed: 1, total: 1 },
            is_today: false,
            route: "story",
            actionable: false,
            primary_action: "查看事故经过",
            task_source: "system_default",
          },
          {
            task_id: "accident_photos",
            title: "事故照片",
            state: "blocked",
            progress: { completed: 0, total: 1 },
            is_today: false,
            route: "photos",
            actionable: false,
            primary_action: "补充照片",
            task_source: "system_default",
          },
          {
            task_id: "insurance_card",
            title: "保险卡",
            state: "pending",
            progress: { completed: 0, total: 1 },
            is_today: true,
            route: "insurance",
            actionable: true,
            primary_action: "上传保险卡",
            task_source: "system_default",
          },
        ] as CustomerConstitutionTaskCard[],
      },
    },
    ...overrides,
  };
}

export function buildBrokerRequestedInsuranceTask(): CustomerTask {
  const base = buildFreshSystemDefaultTask();
  return {
    ...base,
    case_id: `${base.case_id}_broker`,
    phase: "broker_needs_more_info",
    slice1_projection: {
      case_id: `${base.case_id}_broker`,
      workflow_state: "broker_more_requested",
      aggregate_version: 1,
      customer_next_action: {
        action_type: "provide_evidence",
        request_id: "req_p26h_ui",
        request_item_id: "item_ins_followup",
        title: "上传保险卡",
        instructions: "请补一张更清晰的保险卡",
        required_input: "policy_or_insurance_card",
        status: "active",
        ordering: { position: 1, total: 1 },
        allowed_actions: ["submit_request_item"],
        version: 1,
        last_updated_at: "2026-07-18T00:00:00Z",
      },
      broker_next_action: {
        action_type: "wait_for_customer_item",
        status: "waiting_for_customer",
        request_id: "req_p26h_ui",
        version: 1,
      },
      open_request: {
        request_id: "req_p26h_ui",
        status: "open",
        active_item: {
          request_item_id: "item_ins_followup",
          request_id: "req_p26h_ui",
          item_type: "policy_or_insurance_card",
          label: "上传保险卡",
          instructions: "请补一张更清晰的保险卡",
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
      server_timestamp: "2026-07-18T00:00:00Z",
    },
    constitution_projection: {
      customer: {
        today: "上传保险卡",
        why: "请补一张更清晰的保险卡",
        after: "陈总会尽快联系您。",
        current_stage: "customer_action_needed",
        trust: { care_line: "陈总已收到资料", care_note: "如有需要，我们会联系您" },
        tasks: [
          {
            task_id: "accident_story",
            title: "事故经过",
            state: "completed",
            progress: { completed: 1, total: 1 },
            is_today: false,
            route: "story",
            actionable: false,
            primary_action: "",
            task_source: "system_default",
          },
          {
            task_id: "accident_photos",
            title: "事故照片",
            state: "pending",
            progress: { completed: 0, total: 1 },
            is_today: false,
            route: "photos",
            actionable: true,
            primary_action: "补充照片",
            task_source: "system_default",
          },
          {
            task_id: "insurance_card",
            title: "保险卡",
            state: "pending",
            progress: { completed: 0, total: 1 },
            is_today: true,
            route: "request_item",
            actionable: true,
            primary_action: "上传保险卡",
            task_source: "broker_requested",
            reason: "请补一张更清晰的保险卡",
          },
        ] as CustomerConstitutionTaskCard[],
      },
    },
  };
}

export function findCard(
  cards: CustomerTaskCardView[],
  taskId: string,
): CustomerTaskCardView | undefined {
  return cards.find((card) => card.taskId === taskId);
}

export function assertEmptyPageGate(
  report: UiJourneyReport,
  args: {
    task: string;
    source: string;
    expectedPage: string;
    data: Record<string, unknown>;
  },
): void {
  const { task, source, expectedPage, data } = args;
  const surface = resolveRequestItemWorkSurface(data as never);
  if (surface.rejectedWarning) {
    fail(report, {
      task,
      source,
      expectedPage,
      actualPage: "rejected / 当前任务无需此步骤",
      layer: "Page Bootstrap",
      detail: String((data.pageError as { message?: string } | undefined)?.message || ""),
    });
    return;
  }
  if (surface.emptyPage || !insuranceUploadPrimaryUiPresent(data as never)) {
    const hasNext = Boolean(data.nextAction);
    const mode = String(data.inputMode || "");
    fail(report, {
      task,
      source,
      expectedPage,
      actualPage: hasNext ? "request-item" : mode === "evidence" ? "request-item / blank" : "blank",
      layer: "Page Bootstrap",
      detail: `inputMode=${mode || "(empty)"} nextAction=${hasNext} showWorkSurface=${String(data.showWorkSurface)}`,
    });
    return;
  }
  pass(report, `${task}: primary UI rendered`);
}

export function formatUiReport(report: UiJourneyReport): string {
  if (report.ok) {
    return [
      "PASS",
      `Golden UI Journey: ${report.checks.length} assertions`,
      "Layers: Task Home, Mini Program Route, Page Bootstrap, Upload State Machine, Constitution Projection",
    ].join("\n");
  }
  const lines = ["FAIL"];
  for (const failure of report.failures) {
    lines.push("");
    lines.push(`Task: ${failure.task}`);
    lines.push(`Source: ${failure.source}`);
    lines.push(`Expected page: ${failure.expectedPage}`);
    lines.push(`Actual page: ${failure.actualPage}`);
    lines.push(`Owning layer: ${failure.layer}`);
    if (failure.detail) lines.push(`Detail: ${failure.detail}`);
  }
  return lines.join("\n");
}

export function evaluateTaskHomeTap(
  report: UiJourneyReport,
  task: CustomerTask,
  taskId: string,
  expectedRoute: string,
): CustomerTaskCardView | null {
  const cards = resolveCustomerTaskCardsFromTask(task);
  const card = findCard(cards, taskId);
  if (!card) {
    fail(report, {
      task: taskId,
      source: "system_default",
      expectedPage: expectedRoute,
      actualPage: "card missing",
      layer: "Task Home",
    });
    return null;
  }
  if (!card.actionable || !card.route) {
    fail(report, {
      task: taskId,
      source: String((card as { taskSource?: string }).taskSource || "system_default"),
      expectedPage: expectedRoute,
      actualPage: "card not clickable",
      layer: "Task Home",
    });
    return null;
  }
  if (card.route !== expectedRoute) {
    fail(report, {
      task: taskId,
      source: taskId === "insurance_card" ? "system_default" : "system_default",
      expectedPage: expectedRoute,
      actualPage: card.route,
      layer: "Mini Program Route",
    });
    return null;
  }
  pass(report, `${taskId}: tap → ${card.route}`);
  return card;
}

export { REQUEST_ITEM_ROUTE };
