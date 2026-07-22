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
    | "request_not_sent"
    | "transport"
    | "config"
    | "timeout"
    | "auth_config"
    | "server_validation"
    | "server_error"
    | "unknown";
} {
  const normalized = String(code || "").trim();
  const lower = normalized.toLowerCase();
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
      message: "安全连接配置失败，请联系陈总办公室处理。",
      retryable: false,
    };
  }
  if (normalized === "dns_error") {
    return {
      kind: "config",
      message: "无法解析报案服务地址，请稍后重试。如仍失败，请联系陈总办公室。",
      retryable: true,
    };
  }
  if (normalized === "timeout") {
    return {
      kind: "timeout",
      message: "提交超时，结果暂时无法确认。请点一次重试查询提交结果。",
      retryable: true,
    };
  }
  if (normalized === "backend_unreachable") {
    return {
      kind: "request_not_sent",
      message: "报案服务连接检查未通过，本次尚未提交。请稍后重试。",
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
      kind: "auth_config",
      message: "报案服务尚未启用，请联系陈总办公室处理。",
      retryable: false,
    };
  }
  if (normalized === "durable_identity_required") {
    return {
      kind: "auth_config",
      message: "需要完成微信登录后才能开始报案。请重新打开小程序后再试。",
      retryable: true,
    };
  }
  if (
    lower === "unauthorized"
    || lower === "forbidden"
    || lower === "authentication_failed"
    || lower === "configuration_error"
    || lower === "http_401"
    || lower === "http_403"
  ) {
    return {
      kind: "auth_config",
      message: "当前报案服务配置或访问权限无效，请联系陈总办公室处理。",
      retryable: false,
    };
  }
  if (
    normalized === "validation_rejected"
    || normalized === "missing_required_fields"
    || normalized.startsWith("http_4")
  ) {
    return {
      kind: "server_validation",
      message: "提交内容未通过服务校验，请检查填写内容。如仍失败，请联系陈总办公室。",
      retryable: false,
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
