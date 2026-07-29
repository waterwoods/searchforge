/**
 * Chen Demo Invite — Mini Program redeem client (T4).
 *
 * Reads launch query `dit=` and redeems once per opaque token per runtime.
 * Never persists the raw token. Never logs the raw token.
 */

import { requestJson } from "../utils/request";
import { resolveStartClaimSessionId } from "./sessionIdentityAdapter";
import { CHEN_DEMO_OFFICE_ID } from "../utils/demoInviteLaunch";

export type DemoInviteRedeemResult = {
  ok: boolean;
  status?: string;
  error_code?: string | null;
  fallback?: string;
  requires_support_reset?: boolean;
  active_case_id?: string | null;
  active_case_preserved?: boolean;
  customer_display_name?: string;
  vehicle_summary?: string;
  is_demo?: boolean;
  demo_name?: string;
  overlay?: {
    scenario_id?: string;
    mock_scenario?: string;
    office_id?: string;
    expires_at?: number;
  } | null;
};

/** In-process: opaque tokens already redeemed this JS runtime. */
const _redeemedTokens = new Set<string>();

export function resetDemoInviteRedeemCacheForTests(): void {
  _redeemedTokens.clear();
}

export function resolveDemoInviteTokenFromQuery(
  options?: Record<string, string | undefined> | null,
): string {
  const raw = String(options?.dit || "").trim();
  if (!raw || !raw.startsWith("di_")) return "";
  return raw.slice(0, 256);
}

export async function redeemDemoInviteToken(
  token: string,
  options?: { officeId?: string; sessionId?: string; force?: boolean },
): Promise<DemoInviteRedeemResult> {
  const dit = String(token || "").trim();
  if (!dit || !dit.startsWith("di_")) {
    return {
      ok: false,
      status: "invalid",
      error_code: "invalid_token",
      fallback: "blank_claim",
    };
  }

  if (!options?.force && _redeemedTokens.has(dit)) {
    return {
      ok: true,
      status: "redeemed_cached",
      error_code: null,
      is_demo: true,
    };
  }

  const sessionId =
    String(options?.sessionId || "").trim() || (await resolveStartClaimSessionId());
  const officeId = String(options?.officeId || CHEN_DEMO_OFFICE_ID).trim() || CHEN_DEMO_OFFICE_ID;

  const body: Record<string, string> = {
    token: dit,
    session_id: sessionId,
    office_id: officeId,
  };

  try {
    const res = await requestJson<DemoInviteRedeemResult>(
      "POST",
      "/api/h5/demo-invite/redeem",
      body,
    );
    if (res && res.ok) {
      _redeemedTokens.add(dit);
    }
    return res || {
      ok: false,
      status: "invalid",
      error_code: "redeem_empty",
      fallback: "blank_claim",
    };
  } catch {
    return {
      ok: false,
      status: "invalid",
      error_code: "redeem_failed",
      fallback: "blank_claim",
    };
  }
}
