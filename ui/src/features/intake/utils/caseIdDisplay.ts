/**
 * Lightweight Case ID display helpers for Founder QA / Workbench identification.
 * Not customer-facing branding.
 */

/** Short readable suffix for queue rows, e.g. case_92da6e0bcfce → 92da6e0b */
export function shortCaseId(caseId: string | null | undefined): string {
  const raw = String(caseId || '').trim();
  if (!raw) return '';
  const bare = raw.startsWith('case_') ? raw.slice(5) : raw;
  return bare.slice(0, 8);
}

export function fullCaseId(caseId: string | null | undefined): string {
  return String(caseId || '').trim();
}
