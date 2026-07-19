import test from "node:test";
import assert from "node:assert/strict";

import {
  resolveCustomerConstitution,
  type ConstitutionProjection,
} from "../utils/resolveCustomerConstitution";

const LOCAL = {
  today: "确认驾驶员",
  why: "避免后续再次联系你补资料。",
  after: "案件资料即可完整。",
  careLine: "陈总已收到资料",
  careNote: "如有需要，我们会联系您",
  currentStage: "customer_action_needed",
};

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
    },
  };
}

test("complete server Constitution overrides local mock logic", () => {
  const resolved = resolveCustomerConstitution({
    serverProjection: camryBeforeServer(),
    local: LOCAL,
  });
  assert.equal(resolved.today, "上传保险卡");
  assert.equal(resolved.why, "事故经过和现场照片已经完成。");
  assert.equal(resolved.after, "陈总开始审核。");
  assert.equal(resolved.careLine, "陈总已收到资料");
  assert.equal(resolved.careNote, "如有需要，我们会联系您");
  assert.equal(resolved.currentStage, "customer_action_needed");
  assert.equal(resolved.fieldAuthority.today, "server");
  assert.equal(resolved.fieldAuthority.why, "server");
});

test("partial server Constitution uses per-field fallback", () => {
  const resolved = resolveCustomerConstitution({
    serverProjection: {
      projection_version: 1,
      case_id: "case-x",
      current_stage: "customer_action_needed",
      customer: {
        today: "上传保险卡",
        why: null,
        after: "",
        trust: { care_line: "下一步由陈总审核", care_note: null },
        current_stage: null,
      },
    },
    local: LOCAL,
  });
  assert.equal(resolved.today, "上传保险卡");
  assert.equal(resolved.fieldAuthority.today, "server");
  assert.equal(resolved.why, LOCAL.why);
  assert.equal(resolved.fieldAuthority.why, "local");
  assert.equal(resolved.after, LOCAL.after);
  assert.equal(resolved.fieldAuthority.after, "local");
  assert.equal(resolved.careLine, "下一步由陈总审核");
  assert.equal(resolved.fieldAuthority.careLine, "server");
  assert.equal(resolved.careNote, LOCAL.careNote);
  assert.equal(resolved.fieldAuthority.careNote, "local");
  // Falls back to root current_stage then local
  assert.equal(resolved.currentStage, "customer_action_needed");
  assert.equal(resolved.fieldAuthority.currentStage, "server");
});

test("missing Constitution preserves existing local behavior", () => {
  const resolved = resolveCustomerConstitution({
    serverProjection: null,
    local: LOCAL,
  });
  assert.deepEqual(
    {
      today: resolved.today,
      why: resolved.why,
      after: resolved.after,
      careLine: resolved.careLine,
      careNote: resolved.careNote,
      currentStage: resolved.currentStage,
    },
    LOCAL,
  );
  assert.equal(resolved.fieldAuthority.today, "local");
});

test("blank server strings are treated as missing", () => {
  const resolved = resolveCustomerConstitution({
    serverProjection: {
      customer: {
        today: "   ",
        why: "\n",
        after: "",
        trust: { care_line: "  ", care_note: "" },
        current_stage: "   ",
      },
    },
    local: LOCAL,
  });
  assert.equal(resolved.today, LOCAL.today);
  assert.equal(resolved.why, LOCAL.why);
  assert.equal(resolved.after, LOCAL.after);
  assert.equal(resolved.careLine, LOCAL.careLine);
  assert.equal(resolved.careNote, LOCAL.careNote);
  assert.equal(resolved.currentStage, LOCAL.currentStage);
});

test("server current_stage overrides local stage", () => {
  const resolved = resolveCustomerConstitution({
    serverProjection: {
      customer: {
        today: "先不用操作",
        current_stage: "waiting_broker",
      },
    },
    local: LOCAL,
  });
  assert.equal(resolved.currentStage, "waiting_broker");
  assert.equal(resolved.fieldAuthority.currentStage, "server");
  assert.equal(resolved.today, "先不用操作");
  assert.equal(resolved.why, LOCAL.why);
});

test("trust fields fall back independently", () => {
  const resolved = resolveCustomerConstitution({
    serverProjection: {
      customer: {
        trust: { care_line: "陈总正在跟进" },
      },
    },
    local: LOCAL,
  });
  assert.equal(resolved.careLine, "陈总正在跟进");
  assert.equal(resolved.careNote, LOCAL.careNote);
  assert.equal(resolved.fieldAuthority.careLine, "server");
  assert.equal(resolved.fieldAuthority.careNote, "local");
});

// Prototype-coupled Camry Home/Active Claim view assertions live in
// productionCustomerConstitution.test.ts (production path). Dev prototype
// helpers are not part of the P27 closeout surface.
