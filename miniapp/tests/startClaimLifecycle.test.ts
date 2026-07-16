import test from "node:test";
import assert from "node:assert/strict";

import {
  beginStartClaimSubmit,
  createStartClaimSubmitState,
  endStartClaimSubmit,
  mapStartClaimError,
  START_CLAIM_SUCCESS_COPY,
} from "../utils/startClaimLifecycle";
import { mintStartClaimCommandIds } from "../services/startClaimApi";

test("mintStartClaimCommandIds returns distinct command and idempotency keys", () => {
  const ids = mintStartClaimCommandIds();
  assert.match(ids.command_id, /^start_claim_/);
  assert.match(ids.idempotency_key, /^start_claim_idem_/);
  assert.notEqual(ids.command_id, ids.idempotency_key);
});

test("single-flight blocks duplicate taps until end", () => {
  const state = createStartClaimSubmitState();
  const first = beginStartClaimSubmit(state);
  assert.equal(first.started, true);
  const second = beginStartClaimSubmit(state);
  assert.equal(second.started, false);
  assert.equal(second.command_id, first.command_id);
  endStartClaimSubmit(state, false);
  const retry = beginStartClaimSubmit(state, { reuseIdentity: true });
  assert.equal(retry.started, true);
  assert.equal(retry.command_id, first.command_id);
  assert.equal(retry.idempotency_key, first.idempotency_key);
});

test("successful submit clears identity for a fresh next claim", () => {
  const state = createStartClaimSubmitState();
  const first = beginStartClaimSubmit(state);
  endStartClaimSubmit(state, true);
  const next = beginStartClaimSubmit(state);
  assert.equal(next.started, true);
  assert.notEqual(next.command_id, first.command_id);
});

test("network errors are retryable with stable copy", () => {
  const mapped = mapStartClaimError("network_error");
  assert.equal(mapped.retryable, true);
  assert.match(mapped.message, /重试/);
});

test("success copy hides internals", () => {
  const blob = JSON.stringify(START_CLAIM_SUCCESS_COPY);
  assert.equal(blob.includes("case_id"), false);
  assert.equal(blob.includes("aggregate_version"), false);
  assert.equal(blob.includes("command_id"), false);
  assert.equal(START_CLAIM_SUCCESS_COPY.title, "已收到您的报案");
});
