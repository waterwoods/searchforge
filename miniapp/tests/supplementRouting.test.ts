import test from "node:test";
import assert from "node:assert/strict";

import {
  buildSupplementRows,
  resolveNextAction,
  resolveSupplementAction,
} from "../utils/taskMapping";
import { resolveTaskViewModel, resolveSubmitDisabledReason } from "../utils/resolveTaskViewModel";
import type { CustomerTask, TaskContractV0 } from "../types/task";

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_supplement_1",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "injury", "time_location", "story", "vehicle_other_party", "review", "done"],
    current_step: "done",
    completed_count: 5,
    step_total: 5,
    submitted: true,
    phase: "broker_review",
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "no",
      police_involved: "no",
      accident_datetime: "2026-07-13 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    photo_count: 2,
    missing_info: [],
    dashboard_summary: {
      title: "我的事故资料",
      subtitle: "已提交",
      status: "已提交",
      received: [],
      missing: [],
      next_action: "等待陈总查看；如有新资料可继续补充",
      primary_cta: "继续补充资料",
      secondary_cta: "返回微信",
      submitted_supplement_allowed: true,
      warning: "",
    },
    ...overrides,
  };
}

function buildContract(overrides?: Partial<TaskContractV0>): TaskContractV0 {
  return {
    contract_version: "0",
    task_id: "task_opaque_1",
    task_type: "claim_intake",
    task_status: "submitted",
    title: "我的事故资料",
    instruction: "等待陈总查看；如有新资料可继续补充",
    progress: { completed: 5, total: 5 },
    sections: [],
    fields: {},
    missing_items: [],
    evidence_requirements: [],
    // Backend still points post-submit CTA at Review — client must not follow that for supplement.
    next_action: { type: "go_to_section", target: "review", label: "继续补充资料" },
    review_ready: true,
    submit_ready: false,
    revision: 3,
    timestamps: { updated_at: "2026-07-13T00:00:00Z" },
    capabilities: { voice: false, scan: false },
    branding: { office_name: "陈总办公室", safety_copy: "安全文案" },
    error: null,
    ...overrides,
  };
}

const idleBusy = {
  loading: false,
  saving: false,
  uploading: false,
  submitting: false,
  navigating: false,
  retrying: false,
};

test("submitted + missing Basics → 继续补充资料 opens Basics", () => {
  const task = buildTask({
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "",
      police_involved: "",
      accident_datetime: "2026-07-13 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    missing_info: [
      { key: "anyone_injured", label: "是否有人受伤" },
      { key: "police_reported", label: "是否报警" },
    ],
  });
  const contract = buildContract({
    missing_items: [
      { key: "anyone_injured", label: "是否有人受伤" },
      { key: "police_reported", label: "是否报警" },
    ],
  });
  const vm = resolveTaskViewModel(task, contract, {
    route: "/pages/task-home/task-home",
    busy: idleBusy,
  });
  assert.equal(vm.cta.label, "继续补充资料");
  assert.equal(vm.cta.target, "/pages/basics/basics");
  assert.notEqual(vm.cta.target, "review");
});

test("submitted + missing Story → opens Story", () => {
  const task = buildTask({
    key_facts: {
      accident_description: "",
      anyone_injured: "no",
      police_involved: "no",
      accident_datetime: "2026-07-13 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    missing_info: [{ key: "accident_description", label: "事故经过" }],
  });
  const contract = buildContract({
    missing_items: [{ key: "accident_description", label: "事故经过" }],
  });
  const vm = resolveTaskViewModel(task, contract, {
    route: "/pages/task-home/task-home",
    busy: idleBusy,
  });
  assert.equal(vm.cta.target, "/pages/story/story");
});

test("submitted + missing Photos → opens Photos", () => {
  const task = buildTask({
    photo_count: 0,
    missing_info: [{ key: "customer_damage_photo", label: "车损照片" }],
  });
  const contract = buildContract({
    missing_items: [{ key: "customer_damage_photo", label: "车损照片" }],
  });
  const vm = resolveTaskViewModel(task, contract, {
    route: "/pages/task-home/task-home",
    busy: idleBusy,
  });
  assert.equal(vm.cta.target, "/pages/photos/photos");
});

test("multiple missing items → deterministic first actionable route (Story before Basics/Photos)", () => {
  const action = resolveSupplementAction([
    {
      actionable: true,
      route: "/pages/photos/photos",
    },
    {
      actionable: true,
      route: "/pages/basics/basics",
    },
    {
      actionable: true,
      route: "/pages/story/story",
    },
  ]);
  assert.equal(action?.route, "/pages/story/story");
  assert.equal(action?.label, "去填写事故经过");
});

test("no missing items → safe fallback to receipt (not inert Review)", () => {
  const task = buildTask();
  const next = resolveNextAction(task);
  assert.equal(next.kind, "receipt");
  assert.equal(next.route, "/pages/receipt/receipt");

  const vm = resolveTaskViewModel(task, buildContract(), {
    route: "/pages/task-home/task-home",
    busy: idleBusy,
  });
  assert.equal(vm.cta.target, "/pages/receipt/receipt");
  assert.notEqual(vm.cta.target, "review");
});

test("submitted status does not strip non-photo supplement rows", () => {
  const task = buildTask({
    key_facts: {
      accident_description: "",
      anyone_injured: "",
      police_involved: "no",
      accident_datetime: "2026-07-13 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
    photo_count: 2,
  });
  const rows = buildSupplementRows(task);
  assert.ok(rows.some((row) => row.key === "accident_description" && row.actionable));
  assert.ok(rows.some((row) => row.key === "injury_status" && row.actionable));
});

test("supplement save refresh clears resolved missing items from ViewModel", () => {
  const incomplete = buildTask({
    key_facts: {
      accident_description: "我在红灯前被追尾，对方已离开现场。",
      anyone_injured: "",
      police_involved: "no",
      accident_datetime: "2026-07-13 09:00",
      accident_location: "Irvine Blvd",
      own_vehicle_info: "2020 Toyota Camry",
    },
  });
  const contractIncomplete = buildContract({
    missing_items: [{ key: "anyone_injured", label: "是否有人受伤" }],
  });
  const before = resolveTaskViewModel(incomplete, contractIncomplete, {
    route: "/pages/task-home/task-home",
    busy: idleBusy,
  });
  assert.equal(before.cta.target, "/pages/basics/basics");
  assert.ok(before.missingItems.some((item) => item.key === "anyone_injured"));

  const complete = buildTask({
    key_facts: {
      ...incomplete.key_facts,
      anyone_injured: "no",
    },
  });
  const after = resolveTaskViewModel(complete, buildContract({ missing_items: [] }), {
    route: "/pages/task-home/task-home",
    busy: idleBusy,
  });
  assert.equal(after.missingItems.length, 0);
  assert.equal(after.cta.target, "/pages/receipt/receipt");
});

test("no duplicate formal submit after already submitted", () => {
  const task = buildTask();
  const reason = resolveSubmitDisabledReason(task, false, idleBusy, null);
  assert.match(reason, /已提交|无需重复提交/);

  const vm = resolveTaskViewModel(task, buildContract(), {
    route: "/pages/review/review",
    busy: idleBusy,
  });
  assert.equal(vm.cta.actionType, "submit");
  assert.equal(vm.cta.disabled, true);
  assert.match(vm.cta.disabledReason, /已提交|无需重复提交/);
});

test("no dead end: submitted + missing never targets Review from Task Home", () => {
  const task = buildTask({
    photo_count: 0,
    missing_info: [{ key: "photos", label: "事故照片" }],
  });
  const next = resolveNextAction(task);
  assert.equal(next.kind, "supplement");
  assert.equal(next.route, "/pages/photos/photos");

  const vm = resolveTaskViewModel(
    task,
    buildContract({
      missing_items: [{ key: "photos", label: "事故照片" }],
    }),
    { route: "/pages/task-home/task-home", busy: idleBusy },
  );
  assert.equal(vm.cta.label, "继续补充资料");
  assert.equal(vm.cta.target, "/pages/photos/photos");
  assert.ok(!String(vm.cta.target).includes("review"));
});

test("live DevTools fixture: unknown injury/police still show Basics CTA when server lists missing", () => {
  // Mirrors current config.local.ts case: client treats unknown as complete,
  // backend still lists anyone_injured / police_involved as missing.
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
      { field: "anyone_injured", label: "是否有人受伤", kind: "text" } as any,
      { field: "police_involved", label: "是否报警", kind: "text" } as any,
    ],
  });
  const contract = buildContract({
    missing_items: [
      { key: "anyone_injured", label: "是否有人受伤" },
      { key: "police_involved", label: "是否报警" },
    ],
    next_action: { type: "go_to_section", target: "review", label: "继续补充资料" },
    review_ready: true,
    submit_ready: false,
  });

  const vmHome = resolveTaskViewModel(task, contract, {
    route: "/pages/task-home/task-home",
    busy: idleBusy,
  });
  assert.ok(vmHome.missingItems.length >= 2);
  assert.ok(vmHome.missingItems.every((item) => item.actionable));
  assert.equal(vmHome.cta.target, "/pages/basics/basics");
  assert.equal(vmHome.cta.label, "继续补充资料");

  const action = resolveSupplementAction(vmHome.missingItems);
  assert.equal(action?.label, "去补充基本资料");
  assert.equal(action?.route, "/pages/basics/basics");
});
