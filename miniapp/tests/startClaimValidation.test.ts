import test from "node:test";
import assert from "node:assert/strict";

import {
  START_CLAIM_NON_BLOCKING_FIELDS,
  buildStartClaimPayload,
  normalizeAccidentDatetime,
  normalizeInjuryStatus,
  validateStartClaimForm,
} from "../utils/startClaimValidation";

test("founder live values enable submit (short Chinese Must Have)", () => {
  const result = validateStartClaimForm({
    description: "被车后装",
    accidentDatetime: "Today 9 am",
    accidentLocation: "路口",
    injuryStatus: "no",
    reachabilityKnown: true,
  });
  assert.equal(result.ok, true);
  assert.equal(result.canSubmit, true);
  assert.equal(result.normalizedDatetime, "Today 9 am");
  assert.equal(result.normalizedInjury, "no");
  assert.equal(result.missingHint, "");
});

test("没有受伤 maps to canonical no", () => {
  assert.equal(normalizeInjuryStatus("没有受伤"), "no");
  assert.equal(normalizeInjuryStatus("no"), "no");
  assert.equal(normalizeInjuryStatus("unsure"), "unknown");
  assert.equal(normalizeInjuryStatus(""), "");
});

test("no injury selected → visible validation", () => {
  const result = validateStartClaimForm({
    description: "被车后装",
    accidentDatetime: "Today 9 am",
    accidentLocation: "路口",
    injuryStatus: "",
    reachabilityKnown: true,
  });
  assert.equal(result.ok, false);
  assert.equal(result.canSubmit, false);
  assert.match(result.errors.injuryStatus || "", /是否有人受伤/);
  assert.equal(result.firstInvalid, "injuryStatus");
});

test("valid free-text date/time enables submit", () => {
  for (const value of ["Today 9 am", "今天上午 9 点", "2026-07-16 09:00"]) {
    const result = validateStartClaimForm({
      description: "追尾",
      accidentDatetime: value,
      accidentLocation: "路口",
      injuryStatus: "no",
      reachabilityKnown: true,
    });
    assert.equal(result.ok, true, value);
    assert.equal(result.normalizedDatetime, normalizeAccidentDatetime(value));
  }
});

test("empty/unparsed time shows friendly error", () => {
  const empty = validateStartClaimForm({
    description: "追尾",
    accidentDatetime: "",
    accidentLocation: "路口",
    injuryStatus: "no",
    reachabilityKnown: true,
  });
  assert.equal(empty.ok, false);
  assert.match(empty.errors.accidentDatetime || "", /事故时间/);
  assert.match(empty.errors.accidentDatetime || "", /Today 9 am/);

  const junk = validateStartClaimForm({
    description: "追尾",
    accidentDatetime: "...",
    accidentLocation: "路口",
    injuryStatus: "no",
    reachabilityKnown: true,
  });
  assert.equal(junk.ok, false);
  assert.ok(junk.errors.accidentDatetime);
});

test("contact required only when reachability is absent", () => {
  const known = validateStartClaimForm({
    description: "追尾",
    accidentDatetime: "Today 9 am",
    accidentLocation: "路口",
    injuryStatus: "no",
    reachabilityKnown: true,
    contact: "",
  });
  assert.equal(known.ok, true);
  assert.equal(known.errors.contact, undefined);

  const unknown = validateStartClaimForm({
    description: "追尾",
    accidentDatetime: "Today 9 am",
    accidentLocation: "路口",
    injuryStatus: "no",
    reachabilityKnown: false,
    contact: "",
  });
  assert.equal(unknown.ok, false);
  assert.match(unknown.errors.contact || "", /联系方式/);
});

test("VIN/photos/vehicle/card never appear in Start Claim validation", () => {
  const blob = JSON.stringify(validateStartClaimForm({
    description: "追尾",
    accidentDatetime: "Today 9 am",
    accidentLocation: "路口",
    injuryStatus: "yes",
    reachabilityKnown: true,
  }));
  for (const field of START_CLAIM_NON_BLOCKING_FIELDS) {
    assert.equal(blob.includes(field), false, field);
  }
});

test("submit payload uses normalized Must Have only", () => {
  const payload = buildStartClaimPayload({
    description: " 被车后装 ",
    accidentDatetime: "  Today   9 am ",
    accidentLocation: " 路口 ",
    injuryStatus: "no",
    reachabilityKnown: true,
  });
  assert.deepEqual(payload, {
    accident_description: "被车后装",
    accident_datetime: "Today 9 am",
    accident_location: "路口",
    injury_status: "no",
  });
});

test("incomplete form returns null payload", () => {
  assert.equal(
    buildStartClaimPayload({
      description: "",
      accidentDatetime: "Today 9 am",
      accidentLocation: "路口",
      injuryStatus: "no",
    }),
    null,
  );
});
