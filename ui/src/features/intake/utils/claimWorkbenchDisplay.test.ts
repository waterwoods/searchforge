/**
 * P19H-3a / P19H-3c-3B claim workbench display helpers — unit tests (node).
 * Run: npx tsx ui/src/features/intake/utils/claimWorkbenchDisplay.test.ts
 */
import assert from 'node:assert/strict';
import type { ClaimEvidenceSlot, ClaimEvidenceSummary, SavedCase } from '@/api/inboxTriage';
import {
  CLAIM_EVIDENCE_FORBIDDEN_PHRASES,
  buildClaimListSummary,
  claimDisplayStatus,
  claimEvidenceCopyIsBrokerSafe,
  claimLaneLabel,
  formatClaimEvidenceRequiredLevel,
  formatClaimEvidenceSkipReason,
  formatClaimEvidenceSlotDetail,
  formatClaimEvidenceSlotLine,
  formatClaimEvidenceSource,
  formatClaimEvidenceStatusIcon,
  formatClaimEvidenceStatusLabel,
  isClaimGuidedCase,
  isClaimGuidedLane,
  policyContextEvidenceLabel,
  resolveClaimEvidenceSummary,
  resolveClaimSummary,
} from './claimWorkbenchDisplay.ts';

const claimCase = {
  service_lane: 'claim',
  display_status: '事故基本信息已收到',
  claim_summary: {
    accident_datetime: '今天上午10点',
    accident_location: 'Irvine Blvd 和 Culver 附近',
    accident_description: '对方变道刮到我左前门',
  },
} as SavedCase;

assert.equal(isClaimGuidedLane('claim'), true);
assert.equal(isClaimGuidedLane('claim_lite'), false);
assert.equal(isClaimGuidedLane('add_car'), false);
assert.equal(isClaimGuidedCase(claimCase), true);
assert.equal(claimLaneLabel(), '理赔 · 处理中');

const summary = resolveClaimSummary(claimCase);
assert.equal(summary.accident_datetime, '今天上午10点');
assert.equal(summary.accident_location, 'Irvine Blvd 和 Culver 附近');
assert.equal(summary.accident_description, '对方变道刮到我左前门');

assert.equal(
  buildClaimListSummary(claimCase),
  '今天上午10点 · Irvine Blvd 和 Culver 附近 · 对方变道刮到我左前门',
);
assert.equal(claimDisplayStatus(claimCase), '事故基本信息已收到');
assert.ok(!claimDisplayStatus(claimCase).toLowerCase().includes('claim filed'));
assert.equal(
  claimDisplayStatus({ service_lane: 'claim', display_status: 'Claim · Request More' } as SavedCase),
  '等待客户',
);
assert.equal(
  claimDisplayStatus({ service_lane: 'claim', display_status: 'Claim · Broker Review' } as SavedCase),
  '等待经纪人',
);

const addCar = { service_lane: 'add_car', primary_vehicle_summary: '2024 Tesla Model 3' } as SavedCase;
assert.equal(isClaimGuidedCase(addCar), false);

function slot(partial: Partial<ClaimEvidenceSlot> & Pick<ClaimEvidenceSlot, 'slot_key' | 'label'>): ClaimEvidenceSlot {
  return {
    required_level: 'required',
    status: 'missing',
    source_channel: 'none',
    attachment_count: 0,
    latest_attachment: null,
    skip_reason: null,
    needs_broker_review: false,
    ...partial,
  };
}

// 7.1 received H5 slot
const receivedDamage = slot({
  slot_key: 'customer_damage_photo',
  label: '自己车损照片',
  status: 'received',
  required_level: 'required',
  source_channel: 'h5_task',
  attachment_count: 1,
  needs_broker_review: true,
});
const receivedLine = formatClaimEvidenceSlotLine(receivedDamage);
assert.equal(receivedLine.label, '自己车损照片');
assert.equal(receivedLine.statusLabel, '已收到');
assert.equal(formatClaimEvidenceSource('h5_task'), 'H5 上传');
assert.equal(receivedLine.detail, '已收到 · H5 上传 · 1 张');
assert.equal(formatClaimEvidenceStatusIcon('received'), '✅');

// 7.2 missing soft-required slot
const missingOtherParty = slot({
  slot_key: 'other_party_vehicle_photo',
  label: '对方车辆 / 车牌照片',
  status: 'missing',
  required_level: 'soft_required',
});
const otherPartyLine = formatClaimEvidenceSlotLine(missingOtherParty);
assert.equal(otherPartyLine.label, '对方车辆 / 车牌照片');
assert.equal(otherPartyLine.statusLabel, '还缺');
assert.equal(otherPartyLine.detail, '还缺 · 可补充，或记录无法提供原因');
assert.equal(formatClaimEvidenceRequiredLevel('soft_required'), '建议补充');

// 7.3 optional scene slot
const missingScene = slot({
  slot_key: 'scene_photo',
  label: '现场照片',
  status: 'missing',
  required_level: 'optional',
});
const sceneLine = formatClaimEvidenceSlotLine(missingScene);
assert.equal(sceneLine.label, '现场照片');
assert.equal(sceneLine.detail, '可选 · 有的话可以补充');
assert.equal(formatClaimEvidenceRequiredLevel('optional'), '可选');

// 7.4 skipped slot
const skippedOtherParty = slot({
  slot_key: 'other_party_vehicle_photo',
  label: '对方车辆 / 车牌照片',
  status: 'skipped',
  required_level: 'soft_required',
  skip_reason: 'not_available',
});
const skippedDetail = formatClaimEvidenceSlotDetail(skippedOtherParty);
assert.ok(skippedDetail.includes('已跳过'));
assert.equal(formatClaimEvidenceSkipReason('not_available'), '当时无法拍摄');
assert.ok(skippedDetail.includes('当时无法拍摄'));
assert.equal(formatClaimEvidenceStatusIcon('skipped'), '—');

// 7.5 needs_retake
const retakeSlot = slot({
  slot_key: 'customer_damage_photo',
  label: '自己车损照片',
  status: 'needs_retake',
  required_level: 'required',
});
assert.equal(formatClaimEvidenceStatusLabel('needs_retake'), '需重传');
assert.equal(
  formatClaimEvidenceSlotDetail(retakeSlot),
  '需重传 · 请陈总确认后联系客户补充',
);
assert.equal(formatClaimEvidenceStatusIcon('needs_retake'), '↻');

// 7.6 broker_next_action visible in summary payload
const evidenceSummary: ClaimEvidenceSummary = {
  slots: [receivedDamage, missingOtherParty, missingScene],
  missing_required_slots: [],
  missing_soft_required_slots: ['other_party_vehicle_photo'],
  received_slots: ['customer_damage_photo'],
  skipped_slots: [],
  completion_level: 'required_complete',
  broker_next_action: '请客户补充对方车辆/车牌照片，或记录无法提供原因。',
  summary_text: '已收到自己车损照片；对方车辆/车牌照片还缺。',
};
assert.equal(evidenceSummary.broker_next_action, '请客户补充对方车辆/车牌照片，或记录无法提供原因。');
assert.ok(evidenceSummary.broker_next_action.length > 0);

// 7.7 missing summary fallback
assert.equal(resolveClaimEvidenceSummary(claimCase), null);
assert.equal(resolveClaimEvidenceSummary({ claim_evidence_summary: undefined }), null);
assert.equal(resolveClaimEvidenceSummary({ claim_evidence_summary: { slots: 'bad' } as unknown as ClaimEvidenceSummary }), null);
assert.equal(isClaimGuidedCase(claimCase), true);

// 7.8 forbidden copy absent from format helpers
const sampleOutputs = [
  receivedLine.detail,
  otherPartyLine.detail,
  sceneLine.detail,
  skippedDetail,
  formatClaimEvidenceSlotDetail(retakeSlot),
  evidenceSummary.broker_next_action,
  evidenceSummary.summary_text,
  formatClaimEvidenceSource('wecom'),
  formatClaimEvidenceSource('broker_upload'),
];
assert.equal(formatClaimEvidenceSource('broker_upload'), '经纪人上传');
for (const text of sampleOutputs) {
  assert.ok(claimEvidenceCopyIsBrokerSafe(text), `forbidden phrase in: ${text}`);
}
for (const phrase of CLAIM_EVIDENCE_FORBIDDEN_PHRASES) {
  assert.equal(claimEvidenceCopyIsBrokerSafe(`test ${phrase}`), false);
}

assert.equal(
  policyContextEvidenceLabel({
    policy_context: { status: 'confirmed', customer_choice: 'correct' },
    claim_attachment_slots: {},
    case_attachments: [],
  }),
  '已有保单资料，客户已确认',
);
assert.equal(
  policyContextEvidenceLabel({
    policy_context: null,
    claim_attachment_slots: { policy_or_insurance_card: { status: 'received' } },
    case_attachments: [],
  }),
  '客户上传了保险卡',
);

console.log('claimWorkbenchDisplay.test: PASS');
