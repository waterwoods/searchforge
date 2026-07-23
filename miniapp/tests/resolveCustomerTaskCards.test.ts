/**
 * P26A — Constitution Task Cards are server-authoritative; no hard-coded list.
 */
import test from "node:test";
import assert from "node:assert/strict";

import {
  mapConstitutionTaskCard,
  resolveCustomerTaskCardsFromTask,
  resolveTaskHomePrimaryRoute,
} from "../utils/resolveCustomerTaskCards";
import type { CustomerTask, ConstitutionProjection } from "../types/task";

function camryBeforeServer(): ConstitutionProjection {
  return {
    projection_version: 1,
    case_id: "case-chen-camry",
    current_stage: "customer_action_needed",
    customer: {
      today: "上传保险卡",
      why: "事故经过和现场照片已经完成。",
      after: "陈总开始审核。",
      trust: {
        care_line: "陈总已收到资料",
        care_note: "如有需要，我们会联系您",
      },
      current_stage: "customer_action_needed",
      tasks: [
        {
          task_id: "insurance_card",
          title: "保险卡",
          state: "in_progress",
          progress: { completed: 0, total: 1 },
          is_today: true,
          route: "request_item",
          actionable: true,
          primary_action: "上传保险卡",
        },
        {
          task_id: "accident_photos",
          title: "事故照片",
          state: "completed",
          progress: { completed: 1, total: 1 },
          is_today: false,
          route: null,
          actionable: false,
          primary_action: null,
        },
        {
          task_id: "accident_story",
          title: "事故经过",
          state: "completed",
          progress: { completed: 1, total: 1 },
          is_today: false,
          route: null,
          actionable: false,
          primary_action: null,
        },
        {
          task_id: "driver_license",
          title: "驾驶证",
          state: "blocked",
          progress: { completed: 0, total: 1 },
          is_today: false,
          route: null,
          actionable: false,
          primary_action: null,
        },
      ],
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

test("resolveCustomerTaskCardsFromTask uses Constitution tasks only", () => {
  const task = {
    ...baseTask(),
    constitution_projection: camryBeforeServer(),
  };
  const cards = resolveCustomerTaskCardsFromTask(task);
  assert.equal(cards.length, 4);
  assert.equal(cards[0].taskId, "insurance_card");
  assert.equal(cards[0].isToday, true);
  assert.equal(cards[0].actionable, true);
  assert.equal(cards[0].route, "/pages/request-item/request-item");
  // P26D: Today card omits duplicate primaryAction (Focus + footer CTA own it).
  assert.equal(cards[0].primaryAction, "");
  assert.equal(cards[3].taskId, "driver_license");
  assert.equal(cards[3].actionable, false);
});

test("without Constitution tasks, resolver does not invent a hard-coded list", () => {
  const task = {
    ...baseTask(),
    constitution_projection: {
      projection_version: 1,
      case_id: "case-chen-camry",
      customer: {
        today: "上传保险卡",
        why: "why",
        after: "after",
        current_stage: "customer_action_needed",
      },
    },
  };
  assert.deepEqual(resolveCustomerTaskCardsFromTask(task), []);
});

test("primary route prefers today's actionable Constitution card", () => {
  const task = {
    ...baseTask(),
    constitution_projection: camryBeforeServer(),
  };
  assert.equal(resolveTaskHomePrimaryRoute(task), "/pages/request-item/request-item");
});

test("P26G-Q1 system_default insurance route maps to upload page (not label-based)", () => {
  const card = mapConstitutionTaskCard({
    task_id: "insurance_card",
    title: "保险卡",
    state: "in_progress",
    progress: { completed: 0, total: 1 },
    is_today: true,
    route: "insurance",
    actionable: true,
    primary_action: "上传保险卡",
  });
  assert.ok(card);
  assert.equal(card!.route, "/pages/request-item/request-item");
  assert.equal(card!.actionable, true);

  const photos = mapConstitutionTaskCard({
    task_id: "accident_photos",
    title: "事故照片",
    state: "pending",
    progress: { completed: 0, total: 1 },
    is_today: false,
    route: "photos",
    actionable: true,
    primary_action: "补充照片",
  });
  assert.equal(photos!.route, "/pages/photos/photos");

  const story = mapConstitutionTaskCard({
    task_id: "accident_story",
    title: "事故经过",
    state: "pending",
    progress: { completed: 0, total: 1 },
    is_today: false,
    route: "story",
    actionable: true,
    primary_action: "填写事故经过",
  });
  assert.equal(story!.route, "/pages/story/story");
});

test("mapConstitutionTaskCard normalizes shared state model", () => {
  const card = mapConstitutionTaskCard({
    task_id: "accident_photos",
    title: "事故照片",
    state: "in_progress",
    progress: { completed: 1, total: 2 },
    is_today: false,
    route: "photos",
    actionable: true,
    primary_action: "补充照片",
  });
  assert.ok(card);
  assert.equal(card!.stateLabel, "进行中");
  assert.equal(card!.progressText, "1/2");
  assert.equal(card!.route, "/pages/photos/photos");
  assert.equal(card!.completionMark, "○");
});

test("P1 Request More — exact broker tasks; no unrelated Vehicle VIN card", () => {
  const task = {
    ...baseTask(),
    constitution_projection: {
      projection_version: 1,
      case_id: "case-request-exact",
      current_stage: "customer_action_needed",
      customer: {
        today: "保险卡",
        why: "请上传清晰的保险卡照片",
        after: "完成后我们会继续处理。",
        current_stage: "customer_action_needed",
        tasks: [
          {
            task_id: "insurance_card",
            title: "保险卡",
            state: "in_progress",
            progress: { completed: 0, total: 1 },
            is_today: true,
            route: "request_item",
            actionable: true,
            primary_action: "上传保险卡",
            task_source: "broker_requested",
          },
          {
            task_id: "accident_photos",
            title: "事故照片",
            state: "blocked",
            progress: { completed: 0, total: 1 },
            is_today: false,
            route: null,
            actionable: false,
            task_source: "broker_requested",
          },
        ],
      },
    } as ConstitutionProjection,
  };
  const cards = resolveCustomerTaskCardsFromTask(task);
  assert.deepEqual(
    cards.map((c) => c.taskId),
    ["insurance_card", "accident_photos"],
  );
  assert.equal(cards.some((c) => /VIN|vin/i.test(c.title) || c.taskId === "vehicle_vin"), false);
  assert.equal(cards[0].isToday, true);
});
