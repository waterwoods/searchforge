/**
 * P4 Integration 01 — fetch Cap 01→02→03 Smart Claim Start plan.
 * READ ONLY. Does not create claims. Submit still uses startClaimApi.
 */

import { requestJson } from "../utils/request";
import { resolveStartClaimSessionId } from "./sessionIdentityAdapter";

export type SmartClaimKnownChip = {
  field_key: string;
  label_zh: string;
  value: string;
  editability?: string;
};

export type SmartClaimConfirmStep = {
  step_id: string;
  prompt_zh: string;
  options: string[];
  required_before_accident?: boolean;
  reason_code?: string;
};

export type SmartClaimStartPlan = {
  mode: string;
  headline_zh: string;
  subtitle_zh: string;
  confidence_signal: string;
  known_chips: SmartClaimKnownChip[];
  confirm_steps: SmartClaimConfirmStep[];
  questions: Array<{
    field_key: string;
    visibility: string;
    label_zh: string;
    blocks_submit?: boolean;
  }>;
  primary_cta_zh: string;
  secondary_cta_zh?: string | null;
  estimated_customer_inputs?: number;
  photos_placement?: string;
  never_ask_again?: string[];
  failure_profile?: string;
};

export type SmartClaimStartResponse = {
  ok: boolean;
  lookup_enabled?: boolean;
  identity_source?: string;
  plan: SmartClaimStartPlan;
  lookup_match_status?: string;
  prefill_source?: string;
};

export async function fetchSmartClaimStartPlan(options?: {
  mockScenario?: string;
  sessionId?: string;
}): Promise<SmartClaimStartResponse> {
  const sessionId =
    String(options?.sessionId || "").trim() || (await resolveStartClaimSessionId());
  const mockScenario = String(options?.mockScenario || "").trim();
  const body: Record<string, string> = { session_id: sessionId };
  if (mockScenario) body.mock_scenario = mockScenario;
  return requestJson<SmartClaimStartResponse>(
    "POST",
    "/api/h5/customer/smart-claim-start",
    body,
  );
}
