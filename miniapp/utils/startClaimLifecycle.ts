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
  kind:
    | "transport"
    | "config"
    | "timeout"
    | "server_validation"
    | "server_error"
    | "unknown";
} {
  const normalized = String(code || "").trim();
  if (normalized === "domain_not_allowed") {
    return {
      kind: "config",
      message:
        "当前预览环境无法连接报案服务（域名未授权）。请联系陈总办公室配置后再试。",
      retryable: false,
    };
  }
  if (normalized === "tls_error") {
    return {
      kind: "config",
      message: "安全连接失败，请稍后重试。如仍失败，请联系陈总办公室。",
      retryable: true,
    };
  }
  if (normalized === "timeout") {
    return {
      kind: "timeout",
      message: "提交超时，请重试。如已提交成功，不会重复创建。",
      retryable: true,
    };
  }
  if (normalized === "backend_unreachable") {
    return {
      kind: "transport",
      message: "暂时无法连接报案服务，请稍后重试。",
      retryable: true,
    };
  }
  if (normalized === "network_error") {
    return {
      kind: "transport",
      message: "网络请求失败，请检查网络后重试。",
      retryable: true,
    };
  }
  if (normalized === "p20_case_intake_disabled") {
    return {
      kind: "server_validation",
      message: "报案功能暂时不可用，请稍后再试或联系陈总。",
      retryable: true,
    };
  }
  if (
    normalized === "validation_rejected"
    || normalized === "missing_required_fields"
    || normalized.startsWith("http_4")
  ) {
    return {
      kind: "server_validation",
      message: "提交内容未通过校验，请检查后重试。如仍失败，请联系陈总办公室。",
      retryable: true,
    };
  }
  if (normalized.startsWith("http_5") || normalized === "create_claim_failed") {
    return {
      kind: "server_error",
      message: "服务暂时繁忙，请重试。如仍失败，请联系陈总办公室。",
      retryable: true,
    };
  }
  return {
    kind: "unknown",
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
