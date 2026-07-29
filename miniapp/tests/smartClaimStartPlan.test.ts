import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  buildSmartClaimUiState,
  emptySmartClaimUiState,
  planHasBannedIdentityLeak,
  resolveMockScenarioFromQuery,
  sanitizeChipValue,
  sanitizeChips,
} from "../utils/smartClaimStartPlan";
import type { SmartClaimStartPlan } from "../services/smartClaimStartApi";

const here = dirname(fileURLToPath(import.meta.url));
const miniappRoot = join(here, "..");

function matchedPlan(overrides?: Partial<SmartClaimStartPlan>): SmartClaimStartPlan {
  return {
    mode: "MATCHED_KNOWN",
    headline_zh: "今天发生了什么？",
    subtitle_zh: "办公室已了解您。只需告诉我们今天的事故。",
    confidence_signal: "办公室已了解您",
    known_chips: [
      { field_key: "customer_name", label_zh: "姓名", value: "陈明" },
      { field_key: "phone", label_zh: "电话", value: "尾号 1234" },
      { field_key: "vehicle", label_zh: "车辆", value: "2020 Toyota Camry" },
      { field_key: "policy", label_zh: "保单", value: "Mercury · 已关联" },
    ],
    confirm_steps: [],
    questions: [
      { field_key: "accident_story", visibility: "VISIBLE_REQUIRED", label_zh: "事故经过" },
    ],
    primary_cta_zh: "提交给陈总",
    secondary_cta_zh: "信息有误？联系陈总",
    ...overrides,
  };
}

test("flag-off empty UI keeps legacy accident form path", () => {
  const ui = emptySmartClaimUiState();
  assert.equal(ui.uiMode, "legacy");
  assert.equal(ui.showAccidentForm, true);
  assert.equal(ui.canShowAccidentBlock, true);
  assert.equal(ui.showKnownSection, false);
});

test("S3 matched path shows chips and accident block immediately (no quiz)", () => {
  const ui = buildSmartClaimUiState(matchedPlan());
  assert.equal(ui.uiMode, "matched");
  assert.equal(ui.showKnownSection, true);
  assert.equal(ui.knownChips.length, 4);
  assert.equal(ui.canShowAccidentBlock, true);
  // Chips label already says 办公室已了解您 — do not repeat in signal/subtitle.
  assert.equal(ui.confidenceSignal, "");
  assert.equal(ui.subtitleZh.includes("办公室已了解您"), false);
  assert.equal(ui.confirmSteps.length, 0);
  assert.equal(ui.whyAskTime, "");
});

test("S1 continue gate hides accident form and blocks duplicate create path", () => {
  const ui = buildSmartClaimUiState(
    matchedPlan({
      mode: "CONTINUE_ACTIVE",
      headline_zh: "您已有一个正在处理的报案",
      primary_cta_zh: "继续当前报案",
      known_chips: [],
    }),
  );
  assert.equal(ui.uiMode, "continue_active");
  assert.equal(ui.showAccidentForm, false);
  assert.equal(ui.canShowAccidentBlock, false);
});

test("S2 vehicle confirm blocks accident until selected", () => {
  const plan = matchedPlan({
    mode: "MATCHED_CONFIRM_VEHICLE",
    confirm_steps: [
      {
        step_id: "confirm_vehicle",
        prompt_zh: "哪辆车出险？",
        options: ["2020 Toyota Camry", "2019 Honda CR-V"],
        required_before_accident: true,
      },
    ],
    known_chips: [{ field_key: "customer_name", label_zh: "姓名", value: "李娜" }],
  });
  const before = buildSmartClaimUiState(plan, {});
  assert.equal(before.canShowAccidentBlock, false);
  assert.equal(before.showConfirmSection, true);
  const after = buildSmartClaimUiState(plan, {
    confirm_vehicle: "2020 Toyota Camry",
  });
  assert.equal(after.canShowAccidentBlock, true);
});

test("S4 stale soft notice never traps — accident available immediately", () => {
  const plan = matchedPlan({
    mode: "MATCHED_CONFIRM_POLICY",
    headline_zh: "今天发生了什么？",
    subtitle_zh: "保单我们会再核对。您可以先告诉我们今天发生了什么。",
    confirm_steps: [
      {
        step_id: "confirm_policy",
        prompt_zh: "保单信息可能需要办公室再核对——您仍可先报案。",
        options: ["知道了，继续报案"],
        required_before_accident: false,
      },
    ],
  });
  const ui = buildSmartClaimUiState(plan, {});
  assert.equal(ui.uiMode, "matched");
  assert.equal(ui.canShowAccidentBlock, true);
  assert.equal(ui.showAccidentForm, true);
  assert.equal(ui.confirmsComplete, true);
});

test("Ambiguous offers Contact + blank escape; escape shows accident form", () => {
  const plan = matchedPlan({
    mode: "CONTACT_BROKER",
    headline_zh: "需要陈总协助确认",
    primary_cta_zh: "联系陈总",
    secondary_cta_zh: "仍要先报案",
    known_chips: [],
    confirm_steps: [],
  });
  const gate = buildSmartClaimUiState(plan);
  assert.equal(gate.uiMode, "contact_broker");
  assert.equal(gate.secondaryCtaZh, "仍要先报案");
  assert.equal(gate.showAccidentForm, false);
  const escaped = buildSmartClaimUiState(plan, {}, { blankEscapeActive: true });
  assert.equal(escaped.uiMode, "blank_degrade");
  assert.equal(escaped.showAccidentForm, true);
  assert.equal(escaped.canShowAccidentBlock, true);
  assert.equal(escaped.blankEscapeActive, true);
});

test("S5/S6 blank degrade has no identity chips", () => {
  const ui = buildSmartClaimUiState(
    matchedPlan({
      mode: "BLANK_DEGRADE",
      known_chips: [],
      confidence_signal: "我们会先记下事故情况",
    }),
  );
  assert.equal(ui.uiMode, "blank_degrade");
  assert.equal(ui.showKnownSection, false);
  assert.equal(ui.canShowAccidentBlock, true);
});

test("never displays OpenID / internal keys in chips", () => {
  assert.equal(sanitizeChipValue("openid_abc"), "");
  assert.equal(sanitizeChipValue("wx_mock_cap01_s3"), "");
  assert.equal(sanitizeChipValue("POL-MOCK-CAMRY-001"), "");
  assert.equal(sanitizeChipValue("尾号 1234"), "尾号 1234");
  const chips = sanitizeChips([
    { field_key: "customer_name", label_zh: "姓名", value: "陈明" },
    { field_key: "bad", label_zh: "隐藏", value: "person_link_key_x" },
  ]);
  assert.equal(chips.length, 1);
  assert.equal(
    planHasBannedIdentityLeak(
      matchedPlan({
        known_chips: [{ field_key: "x", label_zh: "x", value: "ok" }],
      }) as SmartClaimStartPlan & { openid?: string },
    ),
    false,
  );
});

test("mock scenario query helper", () => {
  assert.equal(resolveMockScenarioFromQuery({ scs: "S3" }), "S3");
  assert.equal(resolveMockScenarioFromQuery({ mock_scenario: "S1" }), "S1");
  assert.equal(resolveMockScenarioFromQuery({}), "");
});

test("smart-claim-start-panel has four component gate files", () => {
  const base = join(miniappRoot, "components/smart-claim-start-panel");
  for (const name of ["index.ts", "index.json", "index.wxml", "index.wxss"]) {
    assert.equal(existsSync(join(base, name)), true, name);
  }
  const json = JSON.parse(readFileSync(join(base, "index.json"), "utf8"));
  assert.equal(json.component, true);
});

test("start-claim panel uses trust copy and blank escape CTA", () => {
  const json = JSON.parse(
    readFileSync(join(miniappRoot, "pages/start-claim/start-claim.json"), "utf8"),
  );
  assert.equal(
    json.usingComponents["smart-claim-start-panel"],
    "/components/smart-claim-start-panel/index",
  );
  const wxml = readFileSync(join(miniappRoot, "pages/start-claim/start-claim.wxml"), "utf8");
  assert.match(wxml, /smart-claim-start-panel/);
  assert.match(wxml, /事故经过/);
  assert.match(wxml, /事故时间/);
  assert.match(wxml, /事故地点/);
  assert.match(wxml, /是否有人受伤/);
  const panelWxml = readFileSync(
    join(miniappRoot, "components/smart-claim-start-panel/index.wxml"),
    "utf8",
  );
  assert.match(panelWxml, /办公室已了解您/);
  assert.match(panelWxml, /secondaryCtaZh/);
  assert.equal(panelWxml.includes("请确认以下信息"), false);
  assert.equal(wxml.includes("openid"), false);
  assert.equal(wxml.includes("person_link_key"), false);
  assert.equal(wxml.includes("case_id"), false);
});

test("config defaults keep smartClaimStartEnabled OFF for rollback", () => {
  const defaults = readFileSync(join(miniappRoot, "config.defaults.ts"), "utf8");
  assert.match(defaults, /smartClaimStartEnabled:\s*false/);
});
