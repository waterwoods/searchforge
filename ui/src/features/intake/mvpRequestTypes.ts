/**
 * P20 MVP contract — broker send + customer submit support.
 * vin / vehicle_information = Claim Vehicle fact submit;
 * policy_or_insurance_card = evidence submit.
 * Keep in sync with backend MVP_SENDABLE_ITEM_TYPES.
 * P27-B2 — broker-facing messages use claim-pilot Chinese office copy.
 */

import { claimRequestMoreBlockedMessage } from '@/features/intake/utils/claimPilotCopy';

export const MVP_SENDABLE_ITEM_TYPES = new Set([
  'vin',
  'vehicle_information',
  'policy_or_insurance_card',
]);

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
  return claimRequestMoreBlockedMessage('unsupported_draft_item_type_for_send', labels);
}

export function brokerSendBlockedMessage(errorCode: string, unsupportedItems?: string[] | null): string {
  return claimRequestMoreBlockedMessage(errorCode, unsupportedItems);
}
