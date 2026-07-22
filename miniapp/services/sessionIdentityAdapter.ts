/**
 * Customer session identity for One Active Case.
 *
 * Production / durable path:
 *   wx.login → POST /api/h5/customer/session → opaque wx_* session_id
 *
 * Home Continue / Start Claim is server-authoritative:
 *   session.has_active_case decides UI; mp_prototype_resume_token is cache only.
 *
 * Prototype anon-* is isolated to non-Production API hosts when durable
 * login cannot be established (local DevTools / QA without MP credentials).
 * It must never be used against the Production API base URL.
 *
 * Failure strategy (session unavailable): see
 * docs/product/p0_home_server_authoritative_resume.md
 */

import { appConfig, PRODUCTION_API_BASE_URL } from "../utils/config";
import { ApiRequestError, requestJson } from "../utils/request";
import {
  clearCustomerSessionId,
  clearResumeToken,
  loadCustomerSessionId,
  loadResumeToken,
  saveCustomerSessionId,
  saveResumeToken,
} from "../utils/storage";

const PROTOTYPE_ANON_KEY = "mp_prototype_anon_session";
const SIMULATE_SEED_KEY = "mp_simulate_openid_seed";

export type CustomerSessionResult = {
  sessionId: string;
  hasActiveCase: boolean;
  resumeToken: string;
  resumeExpiresAt: string;
  identitySource: "durable" | "prototype_anon";
  /** How Active Case authority was decided for this call. */
  authoritySource: "customer_session" | "resume_reconcile" | "none";
};

type SessionApiBody = {
  ok?: boolean;
  session_id?: string;
  has_active_case?: boolean;
  resume_token?: string;
  resume_expires_at?: string;
};

type IntakeAuthorityBody = {
  case_closed_read_only?: boolean;
  case_status?: string | null;
  case_history_state?: string | null;
};

function normalizeApiBase(url: unknown): string {
  return String(url || "")
    .trim()
    .replace(/\/+$/, "");
}

/** True when the Mini Program is pointed at paid-pilot Production API. */
export function isProductionApiTarget(): boolean {
  return normalizeApiBase(appConfig.apiBaseUrl) === normalizeApiBase(PRODUCTION_API_BASE_URL);
}

/** Prototype anon fallback — never against Production API. */
export function allowPrototypeAnonFallback(): boolean {
  return Boolean(appConfig.prototypeMode) && !isProductionApiTarget();
}

export function getPrototypeSessionId(): string {
  try {
    const existing = String(wx.getStorageSync(PROTOTYPE_ANON_KEY) || "").trim();
    if (existing.startsWith("anon-")) return existing.slice(0, 80);
    const created = `anon-${Date.now().toString(36)}`;
    wx.setStorageSync(PROTOTYPE_ANON_KEY, created);
    return created.slice(0, 80);
  } catch {
    return `anon-${Date.now().toString(36)}`.slice(0, 80);
  }
}

function wxLoginCode(): Promise<string> {
  return new Promise((resolve, reject) => {
    if (typeof wx === "undefined" || typeof wx.login !== "function") {
      reject(new Error("wx_login_unavailable"));
      return;
    }
    wx.login({
      success: (res) => {
        const code = String((res && res.code) || "").trim();
        if (!code) {
          reject(new Error("wx_login_empty_code"));
          return;
        }
        resolve(code);
      },
      fail: () => reject(new Error("wx_login_failed")),
    });
  });
}

/**
 * Stable simulate code for local/QA when WECHAT_MP_ALLOW_SIMULATE=1.
 * Uses a durable device-local key so repeat creates share one identity.
 */
function simulateLoginCode(): string {
  try {
    let seed = String(wx.getStorageSync(SIMULATE_SEED_KEY) || "").trim();
    if (!seed) {
      seed = `simdev-${Date.now().toString(36)}`;
      wx.setStorageSync(SIMULATE_SEED_KEY, seed);
    }
    return `sim:${seed}`;
  } catch {
    return `sim:fallback-${Date.now().toString(36)}`;
  }
}

async function resolveLoginCode(): Promise<string> {
  if (allowPrototypeAnonFallback()) {
    try {
      return await wxLoginCode();
    } catch {
      return simulateLoginCode();
    }
  }
  return wxLoginCode();
}

/**
 * Apply /customer/session Active Case authority to local resume cache.
 * Server false → clear; server true + token → save. Never leave stale Continue.
 */
export function applyServerActiveCaseAuthority(body: {
  has_active_case?: boolean;
  resume_token?: string;
  resume_expires_at?: string;
}): { hasActiveCase: boolean; resumeToken: string; resumeExpiresAt: string } {
  const resumeToken = String(body.resume_token || "").trim();
  const resumeExpiresAt = String(body.resume_expires_at || "").trim();
  const hasActiveCase = Boolean(body.has_active_case) && Boolean(resumeToken);
  if (hasActiveCase) {
    saveResumeToken(resumeToken);
    return { hasActiveCase: true, resumeToken, resumeExpiresAt };
  }
  clearResumeToken();
  return { hasActiveCase: false, resumeToken: "", resumeExpiresAt: "" };
}

function intakeSaysClosedHistory(body: IntakeAuthorityBody | null | undefined): boolean {
  if (!body || typeof body !== "object") return false;
  if (Boolean(body.case_closed_read_only)) return true;
  if (String(body.case_history_state || "").trim().toLowerCase() === "history") return true;
  if (String(body.case_status || "").trim().toLowerCase() === "closed") return true;
  return false;
}

/**
 * When /customer/session cannot run, reconcile local resume against case terminal state.
 * Returns whether Home should show Continue.
 */
export async function reconcileLocalResumeAgainstCaseAuthority(): Promise<boolean> {
  const token = loadResumeToken();
  if (!token) return false;
  try {
    const body = await requestJson<IntakeAuthorityBody>(
      "GET",
      `/api/h5/tasks/${encodeURIComponent(token)}/intake`,
    );
    if (intakeSaysClosedHistory(body)) {
      clearResumeToken();
      return false;
    }
    return Boolean(loadResumeToken());
  } catch (err) {
    if (err instanceof ApiRequestError) {
      const code = String(err.code || "");
      if (
        err.status === 404
        || code === "case_not_found"
        || code === "invalid_or_expired_task_link"
        || code === "unsupported_flow"
      ) {
        clearResumeToken();
        return false;
      }
    }
    // Transient network: keep cache for this show; next successful session wins.
    return Boolean(loadResumeToken());
  }
}

async function exchangeCodeForSession(code: string): Promise<CustomerSessionResult> {
  const body = await requestJson<SessionApiBody>("POST", "/api/h5/customer/session", {
    code,
  });
  const sessionId = String(body.session_id || "").trim();
  if (!sessionId.startsWith("wx_")) {
    throw new Error("durable_session_missing");
  }
  saveCustomerSessionId(sessionId);
  const applied = applyServerActiveCaseAuthority(body);
  return {
    sessionId: sessionId.slice(0, 80),
    hasActiveCase: applied.hasActiveCase,
    resumeToken: applied.resumeToken,
    resumeExpiresAt: applied.resumeExpiresAt,
    identitySource: "durable",
    authoritySource: "customer_session",
  };
}

/**
 * Establish or refresh durable customer session.
 * Syncs server Active Case → local resume cache (Home must use returned hasActiveCase).
 */
export async function ensureCustomerSession(): Promise<CustomerSessionResult> {
  try {
    const code = await resolveLoginCode();
    return await exchangeCodeForSession(code);
  } catch {
    const hasActiveFromCase = await reconcileLocalResumeAgainstCaseAuthority();
    const cached = loadCustomerSessionId();
    if (cached.startsWith("wx_")) {
      return {
        sessionId: cached,
        hasActiveCase: hasActiveFromCase,
        resumeToken: hasActiveFromCase ? loadResumeToken() : "",
        resumeExpiresAt: "",
        identitySource: "durable",
        authoritySource: hasActiveFromCase ? "resume_reconcile" : "none",
      };
    }
    if (!allowPrototypeAnonFallback()) {
      clearResumeToken();
      throw new Error("durable_identity_required");
    }
    const anon = getPrototypeSessionId();
    saveCustomerSessionId(anon);
    return {
      sessionId: anon,
      hasActiveCase: hasActiveFromCase,
      resumeToken: hasActiveFromCase ? loadResumeToken() : "",
      resumeExpiresAt: "",
      identitySource: "prototype_anon",
      authoritySource: hasActiveFromCase ? "resume_reconcile" : "none",
    };
  }
}

/**
 * Session id for Start Claim — durable wx_* preferred; anon only as isolated fallback.
 */
export async function resolveStartClaimSessionId(): Promise<string> {
  const session = await ensureCustomerSession();
  return session.sessionId;
}

export function getSessionIdentityLabel(): string {
  const sid = loadCustomerSessionId();
  if (sid.startsWith("wx_")) return "微信身份已绑定（技术会话）";
  if (sid.startsWith("anon-")) return "原型访客（未绑定微信身份）";
  return "未建立客户会话";
}

/** Test/helper — clear durable + prototype identity markers (not customer UI). */
export function clearCustomerIdentityForTests(): void {
  try {
    wx.removeStorageSync(PROTOTYPE_ANON_KEY);
    wx.removeStorageSync(SIMULATE_SEED_KEY);
  } catch {
    // ignore
  }
  clearResumeToken();
  clearCustomerSessionId();
}
