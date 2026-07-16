/**
 * P20 Capability 2 — Missing Information Checklist / draft helpers.
 * Run: npx tsx ui/src/features/intake/components/MissingInformationChecklistPanel.test.ts
 */
import assert from 'node:assert/strict';
import { resolveCaseIntakeProjection } from './MissingInformationChecklistPanel';
import type { SavedCase } from '@/api/inboxTriage';

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

console.log('MissingInformationChecklistPanel.test: PASS');
