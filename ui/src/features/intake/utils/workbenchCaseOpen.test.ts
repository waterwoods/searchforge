/**
 * Workbench drawer open-path helpers — unit tests (node).
 * Run: npx tsx ui/src/features/intake/utils/workbenchCaseOpen.test.ts
 */
import assert from 'node:assert/strict';
import {
  FORMAL_CASE_OPEN_ERROR,
  INTAKE_ITEM_OPEN_ERROR,
  resolveCaseOpenErrorMessage,
  shouldFetchFormalCaseDetail,
  shouldShowCaseOpenFailureToast,
} from './workbenchCaseOpen.ts';

const wecomStub = { service_lane: 'wecom_media_intake' };
const claimStub = { service_lane: 'claim' };
const addCarStub = { service_lane: 'add_car' };

// WeCom / 待确认材料 — list payload is sufficient; no formal case detail fetch.
assert.equal(shouldFetchFormalCaseDetail(wecomStub), false);
assert.equal(shouldFetchFormalCaseDetail(claimStub), true);
assert.equal(shouldFetchFormalCaseDetail(addCarStub), true);
assert.equal(shouldFetchFormalCaseDetail(null), true);

// Failed detail fetch on holding row must not surface formal case toast.
assert.equal(shouldShowCaseOpenFailureToast(wecomStub, true), false);
assert.equal(shouldShowCaseOpenFailureToast(wecomStub, false), false);

// Formal lanes keep the existing error toast on detail fetch failure.
assert.equal(shouldShowCaseOpenFailureToast(claimStub, true), true);
assert.equal(shouldShowCaseOpenFailureToast(addCarStub, true), true);
assert.equal(shouldShowCaseOpenFailureToast(null, true), true);

assert.equal(resolveCaseOpenErrorMessage(wecomStub), INTAKE_ITEM_OPEN_ERROR);
assert.equal(resolveCaseOpenErrorMessage(claimStub), FORMAL_CASE_OPEN_ERROR);
assert.equal(resolveCaseOpenErrorMessage(null), FORMAL_CASE_OPEN_ERROR);

console.log('workbenchCaseOpen.test: PASS');
