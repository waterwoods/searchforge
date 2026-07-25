import test from "node:test";
import assert from "node:assert/strict";

import { resolveTaskViewModel, DEFAULT_SAFETY_COPY } from "../utils/resolveTaskViewModel";
import type { CustomerTask, TaskContractV0 } from "../types/task";

function buildTask(overrides?: Partial<CustomerTask>): CustomerTask {
  return {
    lane: "claim",
    flow: "claim_intake",
    case_id: "case_internal_1",
    title: "我的事故资料",
    safety_copy: "安全文案",
    steps: ["start", "injury", "time_location", "story", "vehicle_other_party", "review", "done"],
    current_step: "story",
    completed_count: 2,
    step_total: 5,
    submitted: false,
    phase: "accident_basics_in_progress",
    key_facts: {
      anyone_injured: "no",
      accident_location: "Irvine",
    },
    missing_info: [{ key: "accident_description", label: "事故经过" }],
    ...overrides,
  };
}

function buildContract(overrides?: Partial<TaskContractV0>): TaskContractV0 {
  return {
    contract_version: "0",
    task_id: "task_opaque_1",
    task_type: "claim_intake",
    task_status: "collecting",
    title: "合同标题",
    instruction: "合同指令",
    progress: { completed: 3, total: 6 },
    sections: [
      {
        key: "story",
        label: "事故经过",
        component_type: "long_text",
        required: true,
        status: "needed",
      },
    ],
    fields: {
      accident_description: "我在红灯前被追尾。",
      case_id: "should_not_leak",
    } as Record<string, string>,
    missing_items: [{ key: "customer_damage_photo", label: "车损照片" }],
    evidence_requirements: [{ slot: "customer_damage_photo", label: "车损照片", min: 1, received: 0 }],
    next_action: { type: "go_to_section", target: "photos", label: "继续填写" },
    review_ready: false,
    submit_ready: false,
    revision: 3,
    timestamps: { updated_at: "2026-07-12T00:00:00Z" },
    capabilities: { voice: false, scan: false },
    branding: { office_name: "陈总办公室", safety_copy: "合同安全文案" },
    error: null,
    ...overrides,
  };
}

test("uses contract path when contract present", () => {
  const task = buildTask();
  const contract = buildContract();
  const vm = resolveTaskViewModel(task, contract);

  assert.equal(vm.source, "contract");
  assert.equal(vm.title, "合同标题");
  assert.equal(vm.cta.label, "继续填写");
  assert.equal(vm.progress.completed, 3);
  assert.equal(vm.progress.total, 6);
});

test("falls back to legacy mapping without contract", () => {
  const task = buildTask({ current_step: "story", key_facts: {} });
  const vm = resolveTaskViewModel(task, undefined);

  assert.equal(vm.source, "legacy");
  assert.equal(vm.cta.target, "/pages/story/story");
  assert.equal(vm.statusLabel, "进行中");
});

test("contract takes precedence over legacy inference", () => {
  const task = buildTask({ current_step: "story", key_facts: {} });
  const contract = buildContract({
    next_action: { type: "go_to_section", target: "review", label: "去检查" },
  });
  const vm = resolveTaskViewModel(task, contract);
  assert.equal(vm.cta.target, "review");
  assert.equal(vm.cta.label, "去检查");
});

test("filters unsafe fields from contract projection", () => {
  const task = buildTask();
  const contract = buildContract();
  const vm = resolveTaskViewModel(task, contract);

  assert.equal(vm.source, "contract");
  assert.equal(vm.safetyCopy, "合同安全文案");
  const contractFields = contract.fields;
  assert.equal(contractFields.case_id, "should_not_leak");
  assert.ok(!Object.prototype.hasOwnProperty.call(vm, "case_id"));
});

test("normalizes progress and cta safely", () => {
  const task = buildTask();
  const contract = buildContract({
    progress: { completed: 100, total: 3 },
    next_action: { type: "submit", label: "提交", target: "review" },
  });
  const vm = resolveTaskViewModel(task, contract);

  assert.equal(vm.progress.completed, 3);
  assert.equal(vm.progress.total, 3);
  assert.equal(vm.progress.percent, 100);
  assert.equal(vm.cta.actionType, "submit");
});

test("normalizes safe error with blocking mode", () => {
  const task = buildTask();
  const vm = resolveTaskViewModel(task, undefined, undefined, {
    code: "task_unavailable",
    message: "暂时不可用",
    retryable: false,
    blocking: true,
  });
  assert.equal(vm.shellMode, "blocking_error");
  assert.equal(vm.error?.blocking, true);
});

test("normalizes nullable cta and safety strings", () => {
  const task = buildTask({ safety_copy: "" });
  const contract = buildContract({
    next_action: { type: "go_to_section", label: "", target: "" },
    branding: { office_name: "", safety_copy: "" },
  });
  const vm = resolveTaskViewModel(task, contract);

  assert.equal(vm.cta.label, "继续");
  assert.equal(vm.cta.target, "");
  assert.equal(vm.cta.disabledReason, "");
  assert.equal(vm.safetyCopy, DEFAULT_SAFETY_COPY);
});

test("normalizes disabledReason when blocking error is present", () => {
  const task = buildTask();
  const vm = resolveTaskViewModel(task, buildContract(), undefined, {
    code: "network_error",
    message: "网络错误",
    retryable: false,
    blocking: true,
  });

  assert.equal(vm.cta.disabledReason, "请先处理当前错误");
  assert.equal(typeof vm.cta.disabledReason, "string");
});

test("handles empty optional contract fields", () => {
  const task = buildTask();
  const contract = buildContract({
    instruction: "",
    missing_items: [],
    evidence_requirements: [],
    branding: { office_name: "", safety_copy: "" },
  });
  const vm = resolveTaskViewModel(task, contract);
  assert.equal(vm.instruction, "");
  assert.equal(vm.missingItems.length, 0);
  assert.equal(vm.safetyCopy, "安全文案");
});

test("does not mutate input task and contract", () => {
  const task = buildTask();
  const contract = buildContract();
  const taskSnapshot = JSON.stringify(task);
  const contractSnapshot = JSON.stringify(contract);

  resolveTaskViewModel(task, contract);

  assert.equal(JSON.stringify(task), taskSnapshot);
  assert.equal(JSON.stringify(contract), contractSnapshot);
});

const idleBusy = {
  loading: false,
  saving: false,
  uploading: false,
  submitting: false,
  navigating: false,
  retrying: false,
};

test("page loading does not set cta loading spinner", () => {
  const vm = resolveTaskViewModel(buildTask(), buildContract(), {
    busy: { ...idleBusy, loading: true },
  });
  assert.equal(vm.cta.loading, false);
});

test("saving does not set cta loading spinner", () => {
  const vm = resolveTaskViewModel(buildTask(), buildContract(), {
    busy: { ...idleBusy, saving: true },
  });
  assert.equal(vm.cta.loading, false);
});

test("submitting sets cta loading spinner", () => {
  const vm = resolveTaskViewModel(buildTask(), buildContract(), {
    busy: { ...idleBusy, submitting: true },
  });
  assert.equal(vm.cta.loading, true);
});

test("review route CTA uses submit label and disabled reason", () => {
  const vm = resolveTaskViewModel(
    buildTask({ current_step: "review" }),
    buildContract({ submit_ready: false, review_ready: false }),
    { route: "/pages/review/review", busy: idleBusy },
  );
  assert.equal(vm.cta.label, "确认并交给陈总");
  assert.equal(vm.cta.actionType, "submit");
  assert.equal(vm.cta.disabled, true);
  assert.ok(String(vm.cta.disabledReason).length > 0);
});

test("receipt route CTA returns to task home", () => {
  const vm = resolveTaskViewModel(
    buildTask({ submitted: true, current_step: "done" }),
    buildContract({ task_status: "submitted", submit_ready: false }),
    { route: "/pages/receipt/receipt", busy: idleBusy },
  );
  assert.equal(vm.cta.label, "返回我的报案");
  assert.equal(vm.cta.actionType, "view_status");
  assert.equal(vm.statusTone, "done");
});

test("legacy hub title 我的事故资料 remaps to 我的报案", () => {
  const vm = resolveTaskViewModel(
    buildTask({ title: "我的事故资料" }),
    buildContract({ title: "我的事故资料" }),
    { busy: idleBusy },
  );
  assert.equal(vm.title, "我的报案");
});
