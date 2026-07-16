/**
 * Classify wx.request / transport failures for customer-safe messaging.
 * Pure helpers — no secrets, no full response bodies.
 */

export type TransportFailureKind =
  | "domain_not_allowed"
  | "tls_error"
  | "timeout"
  | "backend_unreachable"
  | "network_error";

export type WxRequestFailLike = {
  errMsg?: string;
  errno?: number | string;
};

/** Thrown by health/request probes before ApiRequestError wrapping (avoids import cycles). */
export class ClassifiedTransportError extends Error {
  code: TransportFailureKind;
  errMsg: string;
  errno: string;

  constructor(code: TransportFailureKind, errMsg = "", errno = "") {
    super(code);
    this.name = "ClassifiedTransportError";
    this.code = code;
    this.errMsg = errMsg;
    this.errno = errno;
  }
}

export function classifyWxRequestFail(err: WxRequestFailLike | undefined | null): {
  code: TransportFailureKind;
  errMsg: string;
  errno: string;
} {
  const errMsg = String(err?.errMsg || "").trim();
  const errno = err?.errno == null ? "" : String(err.errno);
  const lower = errMsg.toLowerCase();

  if (
    lower.includes("url not in domain list")
    || lower.includes("not in domain list")
    || lower.includes("domain list")
    || lower.includes("合法域名")
  ) {
    return { code: "domain_not_allowed", errMsg, errno };
  }
  if (
    lower.includes("ssl")
    || lower.includes("tls")
    || lower.includes("certificate")
    || lower.includes("cert")
  ) {
    return { code: "tls_error", errMsg, errno };
  }
  if (lower.includes("timeout") || lower.includes("timed out")) {
    return { code: "timeout", errMsg, errno };
  }
  return { code: "network_error", errMsg, errno };
}

/** Safe diagnostic snapshot for Remote Debug / Founder evidence (no tokens). */
export function buildRequestDiagnostic(input: {
  method: string;
  path: string;
  apiHost: string;
  startedAt: number;
  endedAt: number;
  httpStatus?: number;
  errorCode?: string;
  errMsg?: string;
  errno?: string;
  commandId?: string;
  idempotencyKey?: string;
}): Record<string, string | number> {
  return {
    method: input.method,
    path: input.path,
    apiHost: input.apiHost,
    durationMs: Math.max(0, input.endedAt - input.startedAt),
    httpStatus: input.httpStatus ?? 0,
    errorCode: input.errorCode || "",
    errMsg: input.errMsg || "",
    errno: input.errno || "",
    commandId: input.commandId || "",
    idempotencyKey: input.idempotencyKey || "",
  };
}
