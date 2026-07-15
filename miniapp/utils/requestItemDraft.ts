/**
 * Safe local draft storage for Slice 1 request-item resume.
 *
 * Policy: store only draft text/metadata keyed by case + request + item.
 * Never store workflow authority, tokens, or non-serializable upload handles.
 * Local file paths may be retained briefly for resume; they are never treated
 * as confirmed evidence.
 */
const DRAFT_PREFIX = "mp_slice1_request_item_draft_v1:";

export type RequestItemDraft = {
  version: 1;
  case_id: string;
  request_id: string;
  request_item_id: string;
  item_type: string;
  draft_value: string;
  client_draft_id: string;
  command_id?: string;
  idempotency_key?: string;
  expected_case_version?: number;
  attachment_id?: string;
  local_file_path?: string;
  updated_at: string;
};

function draftKey(caseId: string, requestId: string, requestItemId: string): string {
  return `${DRAFT_PREFIX}${caseId}:${requestId}:${requestItemId}`;
}

export function newClientDraftId(): string {
  const random = Math.random().toString(36).slice(2, 10);
  return `draft-${Date.now()}-${random}`;
}

export function newCommandIdentity(prefix = "cmd"): { command_id: string; idempotency_key: string } {
  const random = Math.random().toString(36).slice(2, 10);
  const stamp = `${Date.now()}-${random}`;
  return {
    command_id: `${prefix}_${stamp}`.slice(0, 128),
    idempotency_key: `idem_${stamp}`.slice(0, 128),
  };
}

export function saveRequestItemDraft(draft: RequestItemDraft): void {
  try {
    const key = draftKey(draft.case_id, draft.request_id, draft.request_item_id);
    wx.setStorageSync(key, {
      ...draft,
      version: 1,
      updated_at: draft.updated_at || new Date().toISOString(),
    });
  } catch {
    // ignore storage failures
  }
}

export function loadRequestItemDraft(
  caseId: string,
  requestId: string,
  requestItemId: string,
): RequestItemDraft | null {
  try {
    const raw = wx.getStorageSync(draftKey(caseId, requestId, requestItemId));
    if (!raw || typeof raw !== "object") return null;
    const draft = raw as RequestItemDraft;
    if (
      String(draft.case_id || "") !== caseId ||
      String(draft.request_id || "") !== requestId ||
      String(draft.request_item_id || "") !== requestItemId
    ) {
      return null;
    }
    return {
      version: 1,
      case_id: caseId,
      request_id: requestId,
      request_item_id: requestItemId,
      item_type: String(draft.item_type || ""),
      draft_value: String(draft.draft_value || ""),
      client_draft_id: String(draft.client_draft_id || newClientDraftId()),
      command_id: draft.command_id ? String(draft.command_id) : undefined,
      idempotency_key: draft.idempotency_key ? String(draft.idempotency_key) : undefined,
      expected_case_version:
        typeof draft.expected_case_version === "number" ? draft.expected_case_version : undefined,
      attachment_id: draft.attachment_id ? String(draft.attachment_id) : undefined,
      local_file_path: draft.local_file_path ? String(draft.local_file_path) : undefined,
      updated_at: String(draft.updated_at || ""),
    };
  } catch {
    return null;
  }
}

export function clearRequestItemDraft(caseId: string, requestId: string, requestItemId: string): void {
  try {
    wx.removeStorageSync(draftKey(caseId, requestId, requestItemId));
  } catch {
    // ignore
  }
}
