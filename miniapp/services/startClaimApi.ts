/**
 * Customer Start Claim — thin Mini Program client over Cap2 CreateClaim facade.
 * Always sends a bindable session_id (durable wx_* preferred).
 */

import { requestJson } from "../utils/request";
import { resolveStartClaimSessionId } from "./sessionIdentityAdapter";
import { appConfig } from "../utils/config";

export type CustomerStartClaimCommand = {
  command_id: string;
  idempotency_key: string;
  accident_description?: string;
  accident_datetime?: string;
  accident_location?: string;
  injury_status?: string;
  correlation_id?: string;
};

export type CustomerStartClaimResult = {
  ok: boolean;
  outcome: "accepted" | "replayed" | "resumed" | string;
  error_code?: string;
  /** P26G — opaque signed resume token; persist for Task Home / return-later. */
  resume_token?: string;
  resume_expires_at?: string;
};

export function mintStartClaimCommandIds(): {
  command_id: string;
  idempotency_key: string;
} {
  const stamp = `${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
  return {
    command_id: `start_claim_${stamp}`,
    idempotency_key: `start_claim_idem_${stamp}`,
  };
}

export async function startClaim(
  command: CustomerStartClaimCommand,
): Promise<CustomerStartClaimResult> {
  const sessionId = await resolveStartClaimSessionId();
  return requestJson<CustomerStartClaimResult>("POST", "/api/h5/customer/start-claim", {
    command_id: command.command_id,
    idempotency_key: command.idempotency_key,
    correlation_id: command.correlation_id || command.command_id,
    session_id: sessionId,
    accident_description: (command.accident_description || "").trim() || undefined,
    accident_datetime: (command.accident_datetime || "").trim() || undefined,
    accident_location: (command.accident_location || "").trim() || undefined,
    injury_status: (command.injury_status || "").trim() || undefined,
    is_test: Boolean(appConfig.prototypeMode),
  });
}
