import { appConfig } from "./config";

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
 * Probe GET /healthz once per TTL window.
 * Fails fast with BackendUnreachableError when the API is down or misconfigured.
 */
export function ensureApiReachable(): Promise<void> {
  const now = Date.now();
  if (cache) {
    const ttl = cache.ok ? OK_TTL_MS : FAIL_TTL_MS;
    if (now - cache.checkedAt < ttl) {
      return cache.ok
        ? Promise.resolve()
        : Promise.reject(new BackendUnreachableError());
    }
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseUrl()}/healthz`,
      method: "GET",
      timeout: 5000,
      success(res) {
        const status = res.statusCode || 0;
        if (status >= 200 && status < 300) {
          cache = { ok: true, checkedAt: Date.now() };
          resolve();
          return;
        }
        cache = { ok: false, checkedAt: Date.now() };
        reject(new BackendUnreachableError());
      },
      fail() {
        cache = { ok: false, checkedAt: Date.now() };
        reject(new BackendUnreachableError());
      },
    });
  });
}
