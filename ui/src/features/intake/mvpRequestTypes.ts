/**
 * P20 MVP contract — broker send + customer submit support.
 * VIN = fact submit; policy_or_insurance_card = evidence submit.
 */

export const MVP_SENDABLE_ITEM_TYPES = new Set(['vin', 'policy_or_insurance_card']);

export function isMvpSendableItemType(itemType: string | null | undefined): boolean {
  return MVP_SENDABLE_ITEM_TYPES.has(String(itemType || '').trim().toLowerCase());
}

export function isMvpSendableChecklistRow(row: {
  item_type?: string;
  mvp_sendable?: boolean;
}): boolean {
  if (typeof row.mvp_sendable === 'boolean') return row.mvp_sendable;
  return isMvpSendableItemType(row.item_type);
}

export function formatUnsupportedSendItems(labels: string[]): string {
  const unique = [...new Set(labels.map((l) => String(l || '').trim()).filter(Boolean))];
  if (!unique.length) return 'One or more requested items are not supported yet.';
  if (unique.length === 1) return `"${unique[0]}" is not supported for customer submit yet.`;
  return `These items are not supported for customer submit yet: ${unique.join(', ')}.`;
}

export function brokerSendBlockedMessage(errorCode: string, unsupportedItems?: string[] | null): string {
  if (errorCode === 'unsupported_draft_item_type_for_send') {
    return formatUnsupportedSendItems(unsupportedItems || []);
  }
  if (errorCode === 'request_draft_empty') {
    return 'Select at least one supported Request More item (VIN or insurance card) before sending.';
  }
  if (errorCode === 'illegal_state') {
    return 'This case is not ready for Request More yet. Refresh the case, then try VIN again.';
  }
  if (errorCode === 'open_request_exists') {
    return 'A customer Request More is already open. Wait for the customer or refresh status.';
  }
  if (errorCode === 'lane_mismatch') {
    return 'Request More is only available on Claim cases.';
  }
  return errorCode;
}
