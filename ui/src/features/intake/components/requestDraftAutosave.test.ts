/**
 * Request-draft autosave lifecycle — focused unit tests.
 * Run: npx tsx --tsconfig ui/tsconfig.json ui/src/features/intake/components/requestDraftAutosave.test.ts
 */
import assert from 'node:assert/strict';
import type { CaseIntakeRequestDraftItem } from '@/api/inboxTriage';
import {
  RequestDraftAutosaveController,
  semanticDraftKey,
} from './requestDraftAutosave';
import {
  buildDraftItemsFromRows,
  rowsFromProjection,
} from './MissingInformationChecklistPanel';
import type { CaseIntakeProjection } from '@/api/inboxTriage';

function vinItem(overrides: Partial<CaseIntakeRequestDraftItem> = {}): CaseIntakeRequestDraftItem {
  return {
    field_key: 'vin',
    item_type: 'vin',
    label: 'VIN',
    instructions: 'Please provide VIN',
    required: true,
    position: 1,
    request_mode: 'request_missing',
    selected: true,
    ...overrides,
  };
}

function projectionWithDraft(
  items: CaseIntakeRequestDraftItem[],
  version = 2,
): CaseIntakeProjection {
  return {
    case_id: 'case_qa',
    aggregate_version: version,
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
      items,
    },
    customer_next_action: null,
  };
}

{
  // Normalized server response (extra draft_item_id / order) does not mark dirty.
  const local = [vinItem()];
  const server = [
    vinItem({
      draft_item_id: 'di_new_' + Math.random().toString(16).slice(2),
      position: 1,
      selected: true,
    }),
  ];
  assert.equal(semanticDraftKey(local), semanticDraftKey(server));
}

{
  // Initial hydration sends zero saves.
  const ctrl = new RequestDraftAutosaveController();
  const serverItems = [vinItem({ draft_item_id: 'di_1' })];
  ctrl.resetForCase('case_qa', serverItems);
  assert.equal(ctrl.phase, 'saved');
  assert.equal(ctrl.timerArmed, false);
  const rows = rowsFromProjection(projectionWithDraft(serverItems));
  const local = buildDraftItemsFromRows(rows);
  assert.equal(ctrl.isDirty(local), false);
  assert.equal(ctrl.beginSave(local), null);
  assert.equal(ctrl.phase, 'saved');
}

{
  // One user edit arms exactly one save; accepted baseline does not re-arm.
  const ctrl = new RequestDraftAutosaveController();
  ctrl.resetForCase('case_qa', [vinItem({ instructions: '' })]);
  const edited = [vinItem({ instructions: 'Send clear photo of VIN' })];
  const arm = ctrl.onUserEdit(edited);
  assert.equal(arm.armTimer, true);
  assert.equal(arm.phase, 'unsaved');
  const started = ctrl.beginSave(edited);
  assert.ok(started);
  assert.equal(started!.generation, ctrl.saveGeneration);
  assert.equal(ctrl.phase, 'saving');
  assert.equal(ctrl.inFlight, true);
  // Same content while in flight: queue follow-up, do not start another request.
  const second = ctrl.beginSave(edited);
  assert.equal(second, null);
  assert.equal(ctrl.inFlight, true);
  assert.equal(ctrl.queued, true);
  const accepted = ctrl.acceptSave(started!.generation, edited);
  assert.equal(accepted.accepted, true);
  assert.equal(accepted.runFollowUp, true);
  assert.equal(ctrl.phase, 'saved');
  assert.equal(ctrl.isDirty(edited), false);
  // After accept, content matches baseline → zero additional saves.
  assert.equal(ctrl.beginSave(edited), null);
  assert.equal(ctrl.timerArmed, false);
}

{
  // Rerender / applyServerBaseline with normalized ids → zero additional saves.
  const ctrl = new RequestDraftAutosaveController();
  const items = [vinItem({ draft_item_id: 'di_a' })];
  ctrl.resetForCase('case_qa', items);
  ctrl.applyServerBaseline([vinItem({ draft_item_id: 'di_b' })]);
  assert.equal(ctrl.phase, 'saved');
  assert.equal(ctrl.beginSave([vinItem({ draft_item_id: 'di_c' })]), null);
}

{
  // Polling refresh does not overwrite unsaved edits.
  const ctrl = new RequestDraftAutosaveController();
  ctrl.resetForCase('case_qa', [vinItem({ instructions: 'A' })]);
  const local = [vinItem({ instructions: 'B' })];
  ctrl.onUserEdit(local);
  assert.equal(ctrl.shouldApplyPoll([vinItem({ instructions: 'A' })], local), false);
  // After save, poll may apply.
  const started = ctrl.beginSave(local);
  ctrl.acceptSave(started!.generation, local);
  assert.equal(ctrl.shouldApplyPoll([vinItem({ instructions: 'B' })], local), true);
}

{
  // Edit during in-flight → at most one follow-up.
  const ctrl = new RequestDraftAutosaveController();
  ctrl.resetForCase('case_qa', [vinItem({ instructions: 'A' })]);
  const first = [vinItem({ instructions: 'B' })];
  const started = ctrl.beginSave(first);
  assert.ok(started);
  const second = [vinItem({ instructions: 'C' })];
  ctrl.onUserEdit(second);
  assert.equal(ctrl.beginSave(second), null);
  assert.equal(ctrl.queued, true);
  const { runFollowUp } = ctrl.acceptSave(started!.generation, first);
  assert.equal(runFollowUp, true);
  const follow = ctrl.beginSave(second);
  assert.ok(follow);
  const done = ctrl.acceptSave(follow!.generation, second);
  assert.equal(done.runFollowUp, false);
  assert.equal(ctrl.beginSave(second), null);
}

{
  // Stale response ignored.
  const ctrl = new RequestDraftAutosaveController();
  ctrl.resetForCase('case_qa', [vinItem()]);
  const started = ctrl.beginSave([vinItem({ instructions: 'x' })]);
  assert.ok(started);
  const gen = started!.generation;
  // Simulate newer save generation (e.g. case remount / newer command).
  ctrl.saveGeneration = gen + 1;
  assert.equal(ctrl.isStale(gen), true);
  const stale = ctrl.acceptSave(gen, [vinItem({ instructions: 'x' })]);
  assert.equal(stale.accepted, false);
  assert.equal(ctrl.failSave(gen), false);
}

{
  // Unmount clears timer intent.
  const ctrl = new RequestDraftAutosaveController();
  ctrl.resetForCase('case_qa', []);
  ctrl.onUserEdit([vinItem()]);
  assert.equal(ctrl.timerArmed, true);
  ctrl.clearTimer();
  assert.equal(ctrl.timerArmed, false);
}

{
  // Send Request flush starts one save for latest draft when dirty.
  const ctrl = new RequestDraftAutosaveController();
  ctrl.resetForCase('case_qa', [vinItem({ instructions: '' })]);
  const latest = [vinItem({ instructions: 'latest' })];
  ctrl.onUserEdit(latest);
  const flushed = ctrl.flush(latest);
  assert.ok(flushed);
  assert.equal(flushed!.items[0]?.instructions, 'latest');
  assert.equal(ctrl.timerArmed, false);
}

{
  // Version conflict stops loop (failSave → no auto retry / no timer).
  const ctrl = new RequestDraftAutosaveController();
  ctrl.resetForCase('case_qa', [vinItem()]);
  const started = ctrl.beginSave([vinItem({ instructions: 'conflict' })]);
  assert.ok(started);
  assert.equal(ctrl.failSave(started!.generation), true);
  assert.equal(ctrl.phase, 'failed');
  assert.equal(ctrl.timerArmed, false);
  assert.equal(ctrl.queued, false);
  assert.equal(ctrl.inFlight, false);
}

console.log('requestDraftAutosave.test: PASS');
