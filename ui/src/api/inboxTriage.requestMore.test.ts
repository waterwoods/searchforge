/**
 * P20 Slice 1 Workbench API client tests.
 * Run: npx tsx ui/src/api/inboxTriage.requestMore.test.ts
 */
import assert from 'node:assert/strict';
import request from './request.ts';
import {
  Slice1RequestMoreError,
  createCaseRequestMore,
  type CreateRequestMoreCommand,
} from './inboxTriage.ts';

type PostMock = (url: string, payload?: unknown) => Promise<{ data: unknown }>;

const originalPost = request.post.bind(request);

function setPostMock(mock: PostMock) {
  (request as unknown as { post: PostMock }).post = mock;
}

function restorePost() {
  (request as unknown as { post: typeof originalPost }).post = originalPost;
}

const command: CreateRequestMoreCommand = {
  command_id: 'cmd-ui-request-0001',
  idempotency_key: 'idem-ui-request-0001',
  expected_case_version: 3,
  reason: 'Please provide the requested claim information.',
  requested_items: [
    {
      item_type: 'vin',
      label: ' VIN ',
      instructions: ' Please provide VIN. ',
      required: true,
      position: 1,
    },
  ],
};

async function main() {
  let capturedUrl = '';
  let capturedPayload: any = null;
  setPostMock(async (url, payload) => {
    capturedUrl = url;
    capturedPayload = payload;
    return {
      data: {
        outcome: 'accepted',
        command_id: command.command_id,
        idempotency_key: command.idempotency_key,
        event_ids: ['evt_1'],
        aggregate_version: 4,
        broker_projection: {
          case_id: 'case_api_client',
          workflow_state: 'broker_more_requested',
          aggregate_version: 4,
          open_request: { request_id: 'req_1', status: 'open', items: [] },
        },
      },
    };
  });

  const accepted = await createCaseRequestMore('case api/client', command);
  assert.equal(capturedUrl, '/api/inbox/cases/case%20api%2Fclient/request-more');
  assert.equal(capturedPayload.command_id, 'cmd-ui-request-0001');
  assert.equal(capturedPayload.idempotency_key, 'idem-ui-request-0001');
  assert.equal(capturedPayload.expected_case_version, 3);
  assert.equal(capturedPayload.requested_items[0].label, 'VIN');
  assert.equal(capturedPayload.requested_items[0].instructions, 'Please provide VIN.');
  assert.equal(accepted.aggregate_version, 4);
  assert.equal(accepted.broker_projection?.workflow_state, 'broker_more_requested');

  const sameIdentityRetry = { ...command };
  setPostMock(async (_url, payload: any) => {
    assert.equal(payload.command_id, command.command_id);
    assert.equal(payload.idempotency_key, command.idempotency_key);
    return {
      data: {
        outcome: 'replayed',
        original_outcome: 'accepted',
        command_id: payload.command_id,
        idempotency_key: payload.idempotency_key,
        event_ids: ['evt_1'],
      },
    };
  });
  const replayed = await createCaseRequestMore('case_api_client', sameIdentityRetry);
  assert.equal(replayed.outcome, 'replayed');

  async function expectKind(errorLike: unknown, kind: Slice1RequestMoreError['kind']) {
    setPostMock(async () => {
      throw errorLike;
    });
    await assert.rejects(
      () => createCaseRequestMore('case_api_client', command),
      (error: unknown) => error instanceof Slice1RequestMoreError && error.kind === kind,
    );
  }

  await expectKind(
    {
      response: {
        status: 409,
        data: { detail: { outcome: 'conflict', error_code: 'version_conflict', command_id: 'cmd', idempotency_key: 'idem', event_ids: [] } },
      },
    },
    'version_conflict',
  );
  await expectKind({ response: { status: 422, data: { detail: { error: 'requested_items_required' } } } }, 'validation');
  await expectKind(
    {
      response: {
        status: 422,
        data: { detail: { outcome: 'rejected', error_code: 'slice1_not_enabled', command_id: 'cmd', idempotency_key: 'idem', event_ids: [] } },
      },
    },
    'feature_disabled',
  );
  await expectKind({ response: { status: 403, data: { detail: 'case_office_access_denied_v1' } } }, 'authorization');
  await expectKind({ code: 'ECONNABORTED', request: {} }, 'timeout');
  await expectKind({ response: { status: 503, data: { detail: 'no service record database URL configured' } } }, 'server');
}

main()
  .then(() => {
    console.log('inboxTriage.requestMore.test: PASS');
  })
  .finally(() => {
    restorePost();
  });
