/**
 * Customer Start Claim — thin Mini Program client over Cap2 CreateClaim facade.
 */

import { requestJson } from "../utils/request";
import { getPrototypeSessionId } from "./sessionIdentityAdapter";
import { appConfig } from "../utils/config";

export type CustomerStartClaimCommand = {
  command_id: string;
  idempotency_key: string;
  accident_description?: string;
  correlation_id?: string;
};

export type CustomerStartClaimResult = {
  ok: boolean;
  outcome: "accepted" | "replayed" | string;
  error_code?: string;
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
  return requestJson<CustomerStartClaimResult>("POST", "/api/h5/customer/start-claim", {
    command_id: command.command_id,
    idempotency_key: command.idempotency_key,
    correlation_id: command.correlation_id || command.command_id,
    session_id: getPrototypeSessionId(),
    accident_description: (command.accident_description || "").trim() || undefined,
    is_test: Boolean(appConfig.prototypeMode),
  });
}
