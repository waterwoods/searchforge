/**
 * P19H-3a — Claim guided lane display helpers for Workbench document intake.
 */
import type { SavedCase } from '@/api/inboxTriage';

export const SERVICE_LANE_CLAIM = 'claim';

export type ClaimSummary = {
  accident_datetime?: string | null;
  accident_location?: string | null;
  accident_description?: string | null;
};

export function isClaimGuidedLane(lane?: string | null): boolean {
  return (lane || '').trim() === SERVICE_LANE_CLAIM;
}

export function isClaimGuidedCase(c: Pick<SavedCase, 'service_lane'>): boolean {
  return isClaimGuidedLane(c.service_lane);
}

export function claimLaneLabel(): string {
  return 'Claim';
}

export function resolveClaimSummary(c: SavedCase): ClaimSummary {
  const fromApi = c.claim_summary;
  if (fromApi && typeof fromApi === 'object') {
    return {
      accident_datetime: fromApi.accident_datetime ?? null,
      accident_location: fromApi.accident_location ?? null,
      accident_description: fromApi.accident_description ?? null,
    };
  }
  const facts = c.known_facts ?? {};
  return {
    accident_datetime: facts.accident_datetime ?? null,
    accident_location: facts.accident_location ?? null,
    accident_description: facts.accident_description ?? null,
  };
}

export function buildClaimListSummary(c: SavedCase): string {
  const summary = resolveClaimSummary(c);
  const parts = [
    summary.accident_datetime,
    summary.accident_location,
    summary.accident_description,
  ].filter((v): v is string => Boolean((v || '').trim()));
  if (parts.length) return parts.join(' · ');
  return (c.display_title || '').trim() || 'Claim intake';
}

export function claimDisplayStatus(c: SavedCase): string {
  const status = (c.display_status || '').trim();
  if (status) return status;
  return 'Claim Step 1 complete · Accident basics received';
}

export const CLAIM_INTAKE_SAFETY_NOTE =
  'This is intake only. Broker must confirm before any filing.';
