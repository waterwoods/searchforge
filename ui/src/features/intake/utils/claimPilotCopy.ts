/**
 * P27-B2 — Claim Pilot frozen display vocabulary (presentation only).
 * Chinese-first office language. Do not invent parallel status phrases.
 */

/** Frozen status chips — use exactly these four strings in claim pilot UI. */
export const CLAIM_PILOT_STATUS = {
  waitingCustomer: '等待客户',
  waitingBroker: '等待经纪人',
  completed: '已完成',
  needMaterials: '需补充材料',
} as const;

export type ClaimPilotStatus = (typeof CLAIM_PILOT_STATUS)[keyof typeof CLAIM_PILOT_STATUS];

const WAITING_CUSTOMER_MARKERS = [
  'waiting for customer',
  'waiting customer',
  'waiting_customer',
  'customer is working',
  'broker_more_requested',
  'request more',
  '等待客户',
];

const WAITING_BROKER_MARKERS = [
  'waiting broker',
  'waiting for broker',
  'waiting_broker',
  'ready for review',
  'broker review',
  'your turn',
  'customer replied',
  'broker_review_ready',
  '等待经纪人',
  '等待审核',
];

const COMPLETED_MARKERS = [
  'case complete',
  'case_complete',
  'completed',
  '已完成',
  '已确认',
  '已交接',
];

const NEED_MATERIALS_MARKERS = [
  'need materials',
  'needs materials',
  'need info',
  'needs info',
  'missing',
  '需补充材料',
  '需补充',
  '还缺',
];

/**
 * Normalize any status-ish string into one frozen claim-pilot chip.
 * Unknown / empty → null (caller keeps domain-specific fallback).
 */
export function normalizeClaimPilotStatus(raw?: string | null): ClaimPilotStatus | null {
  const text = String(raw || '').trim();
  if (!text) return null;
  const lower = text.toLowerCase();

  if (WAITING_BROKER_MARKERS.some((m) => lower.includes(m.toLowerCase()) || text.includes(m))) {
    return CLAIM_PILOT_STATUS.waitingBroker;
  }
  if (WAITING_CUSTOMER_MARKERS.some((m) => lower.includes(m.toLowerCase()) || text.includes(m))) {
    return CLAIM_PILOT_STATUS.waitingCustomer;
  }
  if (COMPLETED_MARKERS.some((m) => lower.includes(m.toLowerCase()) || text.includes(m))) {
    return CLAIM_PILOT_STATUS.completed;
  }
  if (NEED_MATERIALS_MARKERS.some((m) => lower.includes(m.toLowerCase()) || text.includes(m))) {
    return CLAIM_PILOT_STATUS.needMaterials;
  }
  return null;
}

/** Request More — broker-facing Chinese office copy (labels / chips / toasts). */
export const CLAIM_REQUEST_MORE_COPY = {
  panelTitle: '请客户补充',
  panelSubtitle: '先看清理赔结论，再向客户发出一项补充请求。',
  sendButton: '发出补充请求',
  copyLink: '复制链接',
  refreshStatus: '刷新进度',
  requestDetails: '补充详情',
  editMessage: '编辑给客户的说明',
  customerLabelPlaceholder: '客户看到的标题',
  customerInstructionPlaceholder: '给客户的说明（可选）',
  linkCopied: '链接已复制',
  copyFailed: '未能复制链接',
  sentSuccess: '已向客户发出补充请求。',
  alreadySent: '补充请求已发出，正在显示客户进度。',
  statusRefreshed: '客户进度已更新。',
  statusRefreshFailed: '暂时无法刷新客户进度。',
  waitingCustomerTitle: CLAIM_PILOT_STATUS.waitingCustomer,
  waitingCustomerBody: '已请客户补充资料，等待客户完成。',
  waitingCustomerBodyBound: '已发送到客户小程序。客户重新打开小程序即可看到补充任务，无需再扫码。',
  sentToMiniProgram: '已发送到客户小程序',
  optionalQrFallback: '未绑定客户可用链接（备用）',
  waitingBrokerTitle: CLAIM_PILOT_STATUS.waitingBroker,
  waitingBrokerBody: '客户已补充，请核对后再决定下一步。',
  chipWaitingCustomer: CLAIM_PILOT_STATUS.waitingCustomer,
  chipWaitingBroker: CLAIM_PILOT_STATUS.waitingBroker,
  progressLine: (satisfied: number, total: number) =>
    `已完成 ${satisfied} / ${total}`,
  requestedLine: (labels: string) => `已请求：${labels}`,
  instructionDefault: '请客户用微信扫码并补充资料。',
  instructionBoundDefault: '客户可在小程序中直接完成补充任务。',
  candidatesHint: (labels: string) => `可请客户补充：${labels}`,
  accidentGapsTitle: '事故信息仍缺',
  accidentReadyTitle: '事故信息已齐 — 可按需请客户补充',
  vinOnlyHint: '当前仅支持发送车辆 VIN。请只勾选 VIN，保存后再发出。',
  selectVinBeforeSend: '请先勾选 VIN，再向客户发出补充请求。',
  saveFailedBeforeSend: '保存未成功 — 请先重试保存，再发出。',
  waitingDraftSave: '正在保存草稿。请勾选 VIN 后稍候再试。',
  draftNotReady: '草稿尚未就绪。请等待保存完成后再发出。',
  caseUpdatedReview: '案件有更新。请核对刷新后的内容，再发出一次。',
  caseUpdatedToast: '案件已更新，请核对后再次发出。',
  networkUncertain: '网络结果不确定。请再点一次「发出补充请求」，可安全重试。',
  networkUncertainToast: '网络结果不确定 — 请再点一次，可安全重试。',
  sendRejected: '补充请求未能发出。请刷新后核对再试。',
  sendFailedRetry: '补充请求未能发出。请再点一次重试。',
  saving: '保存中…',
  saved: '已保存',
  saveFailed: '保存失败 — 重试',
  unsaved: '有未保存更改',
  retry: '重试',
  saveDraftNow: '立即保存草稿',
  customerVin: '客户提供的 VIN',
  codePreparing: '补充请求已发出，二维码仍在准备中。',
  structuredPanelTitle: '补充材料请求',
  structuredCreate: '请客户补充',
  structuredReady: '可以请客户补充材料。',
  structuredEmpty: '当前没有进行中的补充请求。',
  structuredCreateHint: '向客户发出一组有序的补充请求。',
  structuredRefreshHint: '请先刷新案件，再发出新的补充请求。',
  structuredSent: '已向客户发出补充请求。',
  structuredAlreadySaved: '补充请求已保存，进度已刷新。',
  structuredConflict: '编辑期间案件有更新。已刷新最新进度，请核对后再发出。',
  structuredTimeout: '网络结果不确定。再次发出将使用同一请求，可安全重试。',
  structuredNotEnabled: '本案件暂不可发出补充请求。',
  structuredUnauthorized: '您没有权限在本案件上请客户补充。',
  structuredValidation: '请核对补充项目后再发出。',
  structuredFailed: '补充请求未能发出。请刷新案件后重试。',
  activeItem: '客户正在处理',
  queuedItems: '稍后还需补充',
  satisfiedItems: '客户已提交',
  reviewReady: CLAIM_PILOT_STATUS.waitingBroker,
  reviewReadyBody: '客户已补充的内容见上方，请核对后决定下一步。',
  lastUpdated: '最近更新',
  modalTitle: '请客户补充材料',
  modalOk: '发出补充请求',
  modalRetry: '安全重试',
  groupInstructions: '给客户的总体说明',
  addPreset: '添加常用补充项',
  addBlank: '添加空白项',
  required: '必需',
  optional: '可选',
  submittedValue: '客户提交',
  submittedAt: '提交时间',
  source: '来源',
  loading: '正在加载补充进度…',
  loadFailed: '未能加载补充进度。',
  retryLoad: '重试',
  brokerNextReview: '核对客户补充内容',
  brokerNextCreate: '请客户补充',
  customerNext: '客户下一步',
  brokerNext: '办公室下一步',
} as const;

export function claimRequestMoreBlockedMessage(
  errorCode: string,
  unsupportedItems?: string[] | null,
): string {
  if (errorCode === 'unsupported_draft_item_type_for_send') {
    const unique = [...new Set((unsupportedItems || []).map((l) => String(l || '').trim()).filter(Boolean))];
    if (!unique.length) return '有些补充项暂不支持客户在线提交。';
    if (unique.length === 1) return `「${unique[0]}」暂不支持客户在线提交。`;
    return `以下项目暂不支持客户在线提交：${unique.join('、')}。`;
  }
  if (errorCode === 'request_draft_empty') {
    return '请至少勾选一项可发送的补充项（VIN 或保险卡）后再发出。';
  }
  if (errorCode === 'illegal_state') {
    return '本案件暂时还不能发出补充请求。请刷新后再试。';
  }
  if (errorCode === 'open_request_exists') {
    return '已有进行中的补充请求。请等待客户完成，或先刷新进度。';
  }
  if (errorCode === 'lane_mismatch') {
    return '补充材料请求仅适用于理赔案件。';
  }
  return errorCode;
}
