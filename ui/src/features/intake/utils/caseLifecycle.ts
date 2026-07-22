/**
 * P0 Lifecycle — Broker Close → History helpers (UI mirrors server truth).
 * Soft archive (workbench_archived) is NOT Close.
 */

export type CaseLifecycleFields = {
  case_status?: string | null;
  admin_lifecycle?: string | null;
  case_history_state?: string | null;
  closed_at?: string | null;
  closed_by?: string | null;
  workbench_archived?: boolean | null;
};

export function isCaseClosedHistory(caseRecord: CaseLifecycleFields | null | undefined): boolean {
  if (!caseRecord) return false;
  if (String(caseRecord.case_history_state || '').trim().toLowerCase() === 'history') return true;
  if (String(caseRecord.closed_at || '').trim()) return true;
  if (String(caseRecord.case_status || '').trim().toLowerCase() === 'closed') return true;
  const lifecycle = String(caseRecord.admin_lifecycle || '').trim().toLowerCase();
  if (lifecycle === 'closed' || lifecycle === 'history') return true;
  return false;
}
