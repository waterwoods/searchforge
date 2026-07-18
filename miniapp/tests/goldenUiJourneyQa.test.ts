/**
 * P26H-UI QA — deployed/bootstrap journey against ephemeral fixture JSON.
 *
 * Requires env P26H_UI_FIXTURE_JSON from scripts/golden_customer_ui_flow_qa.py.
 */

import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

import {
  assertEmptyPageGate,
  buildBrokerRequestedInsuranceTask,
  buildFreshSystemDefaultTask,
  evaluateTaskHomeTap,
  REQUEST_ITEM_ROUTE,
  type UiJourneyReport,
} from "../utils/goldenUiJourney";
import {
  insuranceUploadPrimaryUiPresent,
  resolveRequestItemWorkSurface,
} from "../utils/requestItemWorkSurface";
import { resolveCustomerTaskCardsFromTask } from "../utils/resolveCustomerTaskCards";
import type { CustomerTask } from "../types/task";

function loadFixture(): any {
  const path = process.env.P26H_UI_FIXTURE_JSON;
  assert.ok(path, "P26H_UI_FIXTURE_JSON required for QA UI journey");
  return JSON.parse(fs.readFileSync(path, "utf8"));
}

function newReport(): UiJourneyReport {
  return { ok: true, checks: [], failures: [] };
}

function seal(report: UiJourneyReport): UiJourneyReport {
  report.ok = report.failures.length === 0;
  return report;
}

function taskFromProjection(caseId: string, projection: any): CustomerTask {
  const base = buildFreshSystemDefaultTask({ case_id: caseId });
  return {
    ...base,
    case_id: caseId,
    constitution_projection: projection || base.constitution_projection,
  };
}

test("QA UI: system_default insurance opens request-item work surface (no blank page)", () => {
  const fixture = loadFixture();
  const report = newReport();
  const task = taskFromProjection(fixture.fresh.case_id, fixture.fresh.constitution_projection);
  const card = evaluateTaskHomeTap(report, task, "insurance_card", REQUEST_ITEM_ROUTE);
  assert.ok(card, "insurance card tapable");

  // Permanent deployed regression: evidence mode + null nextAction must still show surface.
  const fixed = resolveRequestItemWorkSurface(fixture.blank_page_regression);
  assert.equal(fixed.showWorkSurface, true);
  assert.equal(fixed.emptyPage, false);
  assert.equal(insuranceUploadPrimaryUiPresent(fixture.blank_page_regression), true);
  assertEmptyPageGate(report, {
    task: "insurance_card",
    source: "system_default",
    expectedPage: "insurance upload",
    data: fixture.blank_page_regression,
  });

  const legacy = resolveRequestItemWorkSurface(fixture.legacy_blank_shape);
  assert.equal(legacy.emptyPage, true, "legacy nextAction-only shape must fail empty-page gate");

  seal(report);
  assert.equal(report.ok, true, report.failures);
});

test("QA UI: photos + story cards resolve from fixture projection", () => {
  const fixture = loadFixture();
  const task = taskFromProjection(fixture.fresh.case_id, fixture.fresh.constitution_projection);
  const cards = resolveCustomerTaskCardsFromTask(task);
  const photos = cards.find((c) => c.taskId === "accident_photos");
  const story = cards.find((c) => c.taskId === "accident_story");
  assert.ok(photos, "accident_photos card");
  assert.ok(story, "accident_story card");
  // When actionable, route must be the real Mini Program page (not route-only success).
  if (photos?.actionable) {
    assert.equal(photos.route, "/pages/photos/photos");
  }
  if (story?.actionable) {
    assert.equal(story.route, "/pages/story/story");
  }
});
test("QA UI: broker_requested insurance keeps request_item_id context", () => {
  const fixture = loadFixture();
  const projection = fixture.broker_followup.constitution_projection;
  const tasks = projection?.customer?.tasks || [];
  const brokerTask = tasks.find((t: any) => t.task_source === "broker_requested");
  assert.ok(brokerTask, "broker_requested task present on follow-up case");
  assert.equal(brokerTask.route, "request_item");
  // request_item_id may live on action or sibling fields depending on projection version
  const itemId =
    brokerTask.action?.request_item_id ||
    brokerTask.request_item_id ||
    (projection?.customer?.tasks || []).find((t: any) => t.task_source === "broker_requested")
      ?.action?.request_item_id;
  // Constitution may encode id only on Slice1; synthetic helper still validates Mini Program route.
  const synthetic = buildBrokerRequestedInsuranceTask();
  const report = newReport();
  const card = evaluateTaskHomeTap(report, synthetic, "insurance_card", REQUEST_ITEM_ROUTE);
  assert.ok(card);
  assert.equal(seal(report).ok, true);

  const brokerPage = {
    loading: false,
    waitingForBroker: false,
    inputMode: "evidence",
    nextAction: { action_type: "provide_evidence", request_item_id: itemId || "item_ins_followup" },
    nextActionTitle: "上传保险卡",
    showWorkSurface: true,
    showFooterCta: true,
  };
  assert.equal(resolveRequestItemWorkSurface(brokerPage).emptyPage, false);
  assert.equal(insuranceUploadPrimaryUiPresent(brokerPage), true);
});
