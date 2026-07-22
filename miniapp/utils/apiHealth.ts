import { appConfig } from "./config";
import { qaPathLog } from "./qaPathLog";
import { ClassifiedTransportError, classifyWxRequestFail } from "./requestErrors";

type HealthCache = {
  ok: boolean;
  checkedAt: number;
};

const OK_TTL_MS = 60_000;
const FAIL_TTL_MS = 15_000;

let cache: HealthCache | null = null;

function baseUrl(): string {
  return (appConfig.apiBaseUrl || "").replace(/\/$/, "");
}

export class BackendUnreachableError extends Error {
  constructor() {
    super("backend_unreachable");
    this.name = "BackendUnreachableError";
  }
}

/** Clear cached probe result — call before a manual retry. */
export function resetApiHealthCache(): void {
  cache = null;
}

/**
 * Probe GET /health/live once per TTL window.
 * Fails fast with BackendUnreachableError when the API is down or misconfigured.
 */
export function ensureApiReachable(): Promise<void> {
  const now = Date.now();
  if (cache) {
    const ttl = cache.ok ? OK_TTL_MS : FAIL_TTL_MS;
    if (now - cache.checkedAt < ttl) {
      if (cache.ok) {
        qaPathLog("REQUEST_START", {
          kind: "health_cache_hit_ok",
          path: "/health/live",
        });
        return Promise.resolve();
      }
      qaPathLog("EARLY_EXIT", {
        reason: "health_cache_hit_fail",
        path: "/health/live",
        errorCode: "backend_unreachable",
      });
      return Promise.reject(new BackendUnreachableError());
    }
  }

  const url = `${baseUrl()}/health/live`;
  qaPathLog("REQUEST_START", {
    kind: "health_probe",
    path: "/health/live",
    host: baseUrl(),
  });

  return new Promise((resolve, reject) => {
    qaPathLog("REQUEST_SENT", {
      kind: "health_probe",
      path: "/health/live",
      method: "GET",
    });
    wx.request({
      url,
      method: "GET",
      timeout: 5000,
      success(res) {
        const status = res.statusCode || 0;
        if (status >= 200 && status < 300) {
          cache = { ok: true, checkedAt: Date.now() };
          qaPathLog("REQUEST_SUCCESS", {
            kind: "health_probe",
            path: "/health/live",
            httpStatus: status,
          });
          resolve();
          return;
        }
        cache = { ok: false, checkedAt: Date.now() };
        qaPathLog("REQUEST_FAIL", {
          kind: "health_probe",
          path: "/health/live",
          httpStatus: status,
          errorCode: "backend_unreachable",
        });
        reject(new BackendUnreachableError());
      },
      fail(err) {
        cache = { ok: false, checkedAt: Date.now() };
        const classified = classifyWxRequestFail(err);
        qaPathLog("REQUEST_FAIL", {
          kind: "health_probe",
          path: "/health/live",
          errorCode: classified.code,
          errMsg: classified.errMsg.slice(0, 120),
        });
        if (
          classified.code === "domain_not_allowed"
          || classified.code === "tls_error"
          || classified.code === "timeout"
        ) {
          reject(new ClassifiedTransportError(classified.code, classified.errMsg, classified.errno));
          return;
        }
        reject(new BackendUnreachableError());
      },
    });
  });
}
