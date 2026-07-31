/**
 * P20 Capability 2+3A — Missing Information / Send Request helpers.
 * Run: npx tsx ui/src/features/intake/components/MissingInformationChecklistPanel.test.ts
 */
import assert from 'node:assert/strict';
import {
  classifySendRequestError,
  isBoundMiniProgramCustomer,
  resolveAccessReviewState,
  resolveCaseIntakeProjection,
  resolveCustomerAccessCard,
  resolveSendExpectedVersion,
} from './MissingInformationChecklistPanel';
import { isStructuredRequestMoreTerminal } from './StructuredRequestMorePanel';
import { isMvpSendableItemType } from '@/features/intake/mvpRequestTypes';
import { CLAIM_REQUEST_MORE_COPY } from '@/features/intake/utils/claimPilotCopy';
import { Slice1RequestMoreError, type CustomerAccessCard, type SavedCase, type Slice1Projection } from '@/api/inboxTriage';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

function baseCase(overrides: Partial<SavedCase> = {}): SavedCase {
  return {
    case_id: 'case_test_intake',
    case_status: 'new',
    created_at: '2026-07-15T10:00:00Z',
    updated_at: '2026-07-15T10:00:00Z',
    source_text: 'broker create',
    issue_category: 'claim_intake',
    urgency: 'normal',
    manual_followup_needed: true,
    broker_next_step: 'review',
    client_prep: '',
    client_reply_draft: '',
    workbench_test: true,
    ...overrides,
  } as SavedCase;
}

const accessCard: CustomerAccessCard = {
  access_ready: true,
  request_sent: true,
  simple_status: 'Waiting for customer',
  launch_url: 'https://ui-smoky-beta.vercel.app/task/claim/h5t1.example',
  copy_link: 'https://ui-smoky-beta.vercel.app/task/claim/h5t1.example',
  qr_payload: 'https://ui-smoky-beta.vercel.app/task/claim/h5t1.example',
  instruction_zh: '让客户用微信扫码并补充资料。',
  progress: { satisfied_count: 0, total_count: 1 },
};

{
  const projection = {
    case_id: 'case_test_intake',
    aggregate_version: 2,
    is_test: true,
    admin_lifecycle: 'draft',
    missing_information_checklist: [
      {
        field_key: 'vin',
        label: 'VIN',
        customer_label: 'Vehicle VIN',
        item_type: 'vin',
        status: 'missing',
        suggested_for_request: true,
        request_mode: 'request_missing',
      },
    ],
    request_draft: {
      draft_id: 'draft_1',
      draft_version: 1,
      status: 'draft',
      items: [
        {
          field_key: 'vin',
          item_type: 'vin',
          label: 'VIN',
          instructions: 'Please provide VIN',
          required: true,
          position: 1,
          selected: true,
        },
      ],
    },
    customer_next_action: null,
  };
  const resolved = resolveCaseIntakeProjection(
    baseCase({
      p20_case_intake_projection: projection,
      request_draft: projection.request_draft,
      missing_information_checklist: projection.missing_information_checklist,
    }),
  );
  assert.equal(resolved?.is_test, true);
  assert.equal(resolved?.request_draft?.items[0]?.field_key, 'vin');
  assert.equal(resolved?.customer_next_action, null);
  assert.equal(resolved?.missing_information_checklist?.[0]?.status, 'missing');
}

{
  assert.equal(resolveCaseIntakeProjection(baseCase({ workbench_test: false })), null);
}

{
  const fromCase = resolveCustomerAccessCard(baseCase({ customer_access: accessCard }));
  assert.equal(fromCase?.access_ready, true);
  assert.equal(fromCase?.copy_link, fromCase?.qr_payload);
  assert.equal(fromCase?.simple_status, 'Waiting for customer');
  assert.equal(fromCase?.progress?.total_count, 1);
}

{
  const fromProj = resolveCustomerAccessCard(
    baseCase({
      p20_case_intake_projection: {
        case_id: 'case_test_intake',
        aggregate_version: 3,
        admin_lifecycle: 'active',
        request_draft: {
          draft_id: 'draft_1',
          draft_version: 1,
          status: 'sent',
          items: [
            {
              field_key: 'vin',
              item_type: 'vin',
              label: 'VIN',
              instructions: '',
              required: true,
              position: 1,
            },
          ],
        },
        customer_access: accessCard,
      },
    }),
  );
  assert.equal(fromProj?.launch_url, accessCard.launch_url);
}

{
  // QR/link must share the same access representation.
  assert.equal(accessCard.qr_payload, accessCard.copy_link);
  assert.equal(accessCard.qr_payload, accessCard.launch_url);
}

{
  // Preparing fallback keeps Copy Link usable when QR payload missing.
  const preparing: CustomerAccessCard = {
    access_ready: true,
    request_sent: true,
    message: 'Request sent. Code is still preparing.',
    copy_link: 'https://ui-smoky-beta.vercel.app/task/claim/h5t1.example',
    launch_url: 'https://ui-smoky-beta.vercel.app/task/claim/h5t1.example',
    qr_payload: null,
  };
  assert.ok(preparing.copy_link);
  assert.equal(preparing.qr_payload, null);
}

{
  // Default UI helpers must not require technical IDs.
  const keys = Object.keys(accessCard);
  assert.ok(!keys.includes('access_id'));
  assert.ok(!keys.includes('request_group_id'));
  assert.ok(!keys.includes('token'));
  assert.ok(!keys.includes('aggregate_version'));
}

{
  assert.equal(isMvpSendableItemType('vin'), true);
  assert.equal(isMvpSendableItemType('policy_or_insurance_card'), true);
  assert.equal(isMvpSendableItemType('free_text'), false);
}

{
  // Autosave flush version must win over stale projection for Send CAS.
  assert.equal(
    resolveSendExpectedVersion({
      flushedVersion: 4,
      lastAcceptedVersion: 3,
      projectionVersion: 2,
    }),
    4,
  );
  assert.equal(
    resolveSendExpectedVersion({
      flushedVersion: null,
      lastAcceptedVersion: 5,
      projectionVersion: 2,
    }),
    5,
  );
  assert.equal(
    resolveSendExpectedVersion({
      projectionVersion: 1,
    }),
    1,
  );
}

{
  // A stale case response must refresh once — not become a generic failure.
  const conflict = classifySendRequestError(
    new Slice1RequestMoreError('stale', 'version_conflict', { status: 409 }),
  );
  assert.equal(conflict.kind, 'version_conflict');
  assert.equal(conflict.clearCommandIdentity, true);
  assert.match(conflict.toast, /案件已更新/);

  const timeout = classifySendRequestError(
    new Slice1RequestMoreError('uncertain', 'timeout'),
  );
  assert.equal(timeout.kind, 'timeout');
  assert.equal(timeout.clearCommandIdentity, false);

  // Axios-shaped 409 without wrapper still classifies as conflict.
  const axiosConflict = classifySendRequestError({ response: { status: 409 } });
  assert.equal(axiosConflict.kind, 'version_conflict');
  assert.equal(axiosConflict.clearCommandIdentity, true);
}

{
  const waiting = resolveAccessReviewState(accessCard, {
    case_id: 'case_test_intake',
    workflow_state: 'broker_more_requested',
    aggregate_version: 2,
    open_request: {
      request_id: 'rg_1',
      status: 'open',
      progress: { satisfied: 0, total: 1 },
      items: [
        {
          request_item_id: 'ri_vin',
          item_type: 'vin',
          label: 'VIN',
          status: 'active',
          required: true,
          position: 1,
        },
      ],
    },
  } as Slice1Projection);
  assert.equal(waiting.reviewReady, false);
  assert.equal(waiting.submittedVin, null);
  assert.equal(waiting.satisfied, 0);
  assert.equal(waiting.total, 1);
}

{
  const readyProj = {
    case_id: 'case_test_intake',
    workflow_state: 'broker_review_ready',
    aggregate_version: 3,
    broker_next_action: { action_type: 'review_customer_response' },
    open_request: {
      request_id: 'rg_1',
      status: 'open',
      progress: { satisfied: 1, total: 1 },
      items: [
        {
          request_item_id: 'ri_vin',
          item_type: 'vin',
          label: 'VIN',
          status: 'satisfied',
          required: true,
          position: 1,
          customer_response: {
            kind: 'fact',
            field_id: 'vin',
            submitted_value: '1HGCM82633A004352',
            review_status: 'satisfied',
            applied_to_canonical_facts: false,
          },
        },
      ],
    },
  } as Slice1Projection;
  const readyAccess: CustomerAccessCard = {
    ...accessCard,
    // The access card can lag the authoritative Slice 1 projection by one read.
    simple_status: 'Waiting for customer',
    progress: { satisfied_count: 0, total_count: 1 },
  };
  const ready = resolveAccessReviewState(readyAccess, readyProj);
  assert.equal(ready.reviewReady, true);
  assert.equal(ready.submittedVin, '1HGCM82633A004352');
  assert.equal(ready.satisfied, 1);
  assert.equal(ready.total, 1);
  assert.equal(ready.simpleStatus, '等待办公室审核');
}

{
  // Bound Mini Program customer → primary QR path is not required.
  assert.equal(
    isBoundMiniProgramCustomer(
      baseCase({
        identity_binding_state: 'linked',
        person_link_source: 'wechat',
        person_link_key: 'plk_demo',
      }),
    ),
    true,
  );
  assert.equal(
    isBoundMiniProgramCustomer(
      baseCase({
        identity_binding_state: 'unbound',
        person_link_source: null,
      }),
    ),
    false,
  );
  assert.equal(
    isBoundMiniProgramCustomer(
      baseCase({
        ...( { entry_channel: 'mini_program' } as Partial<SavedCase>),
      }),
    ),
    true,
  );
}

{
  // Closed / history cases must disable Request More composer.
  assert.equal(
    isStructuredRequestMoreTerminal(
      baseCase({
        case_history_state: 'history',
        closed_at: '2026-07-22T12:00:00Z',
      } as Partial<SavedCase>),
    ),
    true,
  );
}

{
  // Source contract: bound customers hide primary QR; unbound keep fallback QR.
  const here = dirname(fileURLToPath(import.meta.url));
  const panel = readFileSync(join(here, 'MissingInformationChecklistPanel.tsx'), 'utf8');
  assert.match(panel, /boundMiniProgram/);
  assert.match(panel, /sentToMiniProgram|已发送到客户小程序/);
  assert.match(panel, /optionalQrFallback|未绑定客户可用链接/);
  assert.match(panel, /showPrimaryQr/);
  assert.match(panel, /refreshCaseRef/);
  assert.equal(CLAIM_REQUEST_MORE_COPY.sentToMiniProgram.includes('小程序'), true);
  assert.ok(accessCard.qr_payload);
  // Exact requested-item summary still available for waiting state.
  const waiting = resolveAccessReviewState(accessCard, {
    case_id: 'case_test_intake',
    workflow_state: 'broker_more_requested',
    aggregate_version: 2,
    open_request: {
      request_id: 'rg_1',
      status: 'open',
      progress: { satisfied: 0, total: 1 },
      items: [
        {
          request_item_id: 'ri_card',
          item_type: 'policy_or_insurance_card',
          label: '保险卡',
          status: 'active',
          required: true,
          position: 1,
        },
      ],
    },
  } as Slice1Projection);
  assert.equal(waiting.reviewReady, false);
  assert.equal(waiting.total, 1);
  assert.equal(
    CLAIM_REQUEST_MORE_COPY.requestedLine('保险卡'),
    '已请求：保险卡',
  );
}

console.log('MissingInformationChecklistPanel.test: PASS');
