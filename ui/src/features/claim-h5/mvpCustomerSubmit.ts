/**
 * P20 Cap 3B MVP — customer-submittable request item types on H5 / Mini Program Slice1.
 * Keep in sync with backend MVP_SENDABLE_ITEM_TYPES.
 */

export const MVP_CUSTOMER_SUBMITTABLE_TYPES = new Set(['vin', 'policy_or_insurance_card']);

export function isCustomerSubmittableItemType(itemType: string | null | undefined): boolean {
  return MVP_CUSTOMER_SUBMITTABLE_TYPES.has(String(itemType || '').trim().toLowerCase());
}

export const CUSTOMER_SUBMIT_NOT_SUPPORTED_ZH =
  '该项资料暂时无法在此填写，请回微信联系陈总办公室。';
