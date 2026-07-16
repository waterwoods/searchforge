/**
 * Pure helpers for Customer Start Claim submit / retry (testable).
 */

import {
  beginLogicalSubmit,
  endLogicalSubmit,
  type SubmitGateState,
} from "./slice1Lifecycle";
import { mintStartClaimCommandIds } from "../services/startClaimApi";

export type StartClaimSubmitState = SubmitGateState & {
  accidentDescription: string;
};

export function createStartClaimSubmitState(): StartClaimSubmitState {
  return {
    submitInFlight: false,
    commandId: "",
    idempotencyKey: "",
    accidentDescription: "",
  };
}

export function beginStartClaimSubmit(
  state: StartClaimSubmitState,
  options?: { reuseIdentity?: boolean },
): { started: boolean; command_id: string; idempotency_key: string } {
  return beginLogicalSubmit(state, mintStartClaimCommandIds, options);
}

export function endStartClaimSubmit(state: StartClaimSubmitState, clearIdentity = false): void {
  endLogicalSubmit(state, clearIdentity);
}

export function mapStartClaimError(code: string): {
  message: string;
  retryable: boolean;
} {
  const normalized = String(code || "").trim();
  if (normalized === "backend_unreachable" || normalized === "network_error") {
    return {
      message: "网络不稳定，请稍后重试。您的提交不会重复创建。",
      retryable: true,
    };
  }
  if (normalized === "p20_case_intake_disabled") {
    return {
      message: "报案功能暂时不可用，请稍后再试或联系陈总。",
      retryable: true,
    };
  }
  if (normalized.startsWith("http_5") || normalized === "create_claim_failed") {
    return {
      message: "提交失败，请重试。如仍失败，请联系陈总办公室。",
      retryable: true,
    };
  }
  return {
    message: "提交失败，请重试。如仍失败，请联系陈总办公室。",
    retryable: true,
  };
}

export const START_CLAIM_SUCCESS_COPY = {
  title: "已收到您的事故说明",
  bodyLines: [
    "陈总会先了解事故情况。",
    "如需 VIN、保险卡或照片，",
    "我们会再通知您补充。",
  ],
} as const;
