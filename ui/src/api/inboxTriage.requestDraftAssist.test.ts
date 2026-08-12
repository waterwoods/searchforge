/**
 * AI Request More drafting client contract.
 * Run: npx tsx ui/src/api/inboxTriage.requestDraftAssist.test.ts
 */
import assert from 'node:assert/strict';
import request from './request.ts';
import { requestMoreAiDraft } from './inboxTriage.ts';

type PostMock = (url: string, payload?: unknown) => Promise<{ data: unknown }>;

const originalPost = request.post.bind(request);

function setPostMock(mock: PostMock) {
  (request as unknown as { post: PostMock }).post = mock;
}

function restorePost() {
  (request as unknown as { post: typeof originalPost }).post = originalPost;
}

async function main() {
  const calls: Array<{ url: string; payload: any }> = [];
  setPostMock(async (url, payload) => {
    calls.push({ url, payload });
    return {
      data: {
        ok: true,
        drafting_available: true,
        missing_item_count: 1,
        draft_text: '您好，为了继续处理您的案件，目前还需要：\n1. 车辆 VIN\n请方便时在这里补充上传，谢谢。',
        items: [
          {
            field_key: 'vin',
            item_type: 'vin',
            label: '车辆 VIN',
            instructions: 'VIN 共 17 位。',
            request_mode: 'request_missing',
            position: 1,
          },
        ],
        authority: 'ai_draft',
        draft_used_ai: true,
        used_fallback: false,
        lifecycle_mutated: false,
      },
    };
  });

  const drafted = await requestMoreAiDraft('case api/client');
  assert.equal(calls[0].url, '/api/inbox/cases/case%20api%2Fclient/request-draft-assist');
  assert.equal(calls[0].payload.prefer_template, false);
  assert.equal(drafted.items?.length, 1);
  assert.equal(drafted.items?.[0].field_key, 'vin');
  // Drafting must never look like a command: no ids, no version, no send.
  assert.equal(calls[0].payload.command_id, undefined);
  assert.equal(calls[0].payload.expected_case_version, undefined);
  assert.equal(drafted.lifecycle_mutated, false);

  await requestMoreAiDraft('case_api_client', 'corr-1', true);
  assert.equal(calls[1].payload.prefer_template, true);
  assert.equal(calls[1].payload.correlation_id, 'corr-1');
}

main()
  .then(() => {
    console.log('inboxTriage.requestDraftAssist.test: PASS');
  })
  .finally(() => {
    restorePost();
  });
