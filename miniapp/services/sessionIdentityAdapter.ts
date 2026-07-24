/**
 * Customer session identity for One Active Case.
 *
 * Production / durable path:
 *   wx.login → POST /api/h5/customer/session → opaque wx_* session_id
 *
 * Customer Context is server-authoritative:
 *   context.next_action decides navigation; mp_prototype_resume_token is cache only.
 *
 * Prototype anon-* is isolated to non-Production API hosts when durable
 * login cannot be established (local DevTools / QA without MP credentials).
 * It must never be used against the Production API base URL.
 *
 * Failure strategy (session unavailable): see
 * docs/product/p0_home_server_authoritative_resume.md
 */

import { appConfig, PRODUCTION_API_BASE_URL } from "../utils/config";
import { requestJson } from "../utils/request";
import {
  clearCustomerSessionId,
  clearResumeToken,
  loadCustomerSessionId,
  saveCustomerSessionId,
  saveResumeToken,
} from "../utils/storage";

const PROTOTYPE_ANON_KEY = "mp_prototype_anon_session";
const SIMULATE_SEED_KEY = "mp_simulate_openid_seed";

export type CustomerSessionResult = {
  sessionId: string;
  identitySource: "durable" | "prototype_anon";
};

type SessionApiBody = {
  ok?: boolean;
  session_id?: string;
};

export type CustomerNextAction =
  | "START_NEW_CLAIM"
  | "CONTINUE_ACTIVE_CASE"
  | "UPLOAD_REQUEST_ITEM"
  | "BROKER_REVIEW"
  | "CASE_CLOSED";

export type CustomerContextResult = {
  hasActiveCase: boolean;
  resumeToken: string;
  resumeExpiresAt: string;
  nextAction: CustomerNextAction;
};

type CustomerContextApiBody = {
  has_active_case?: boolean;
  resume_token?: string;
  resume_expires_at?: string;
  next_action?: CustomerNextAction;
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

async function exchangeCodeForSession(code: string): Promise<CustomerSessionResult> {
  const body = await requestJson<SessionApiBody>("POST", "/api/h5/customer/session", {
    code,
  });
  const sessionId = String(body.session_id || "").trim();
  if (!sessionId.startsWith("wx_")) {
    throw new Error("durable_session_missing");
  }
  saveCustomerSessionId(sessionId);
  return {
    sessionId: sessionId.slice(0, 80),
    identitySource: "durable",
  };
}

/**
 * Establish or refresh durable customer session identity.
 * This intentionally makes no Active Case or navigation decision.
 */
export async function ensureCustomerSession(): Promise<CustomerSessionResult> {
  try {
    const code = await resolveLoginCode();
    return await exchangeCodeForSession(code);
  } catch {
    const cached = loadCustomerSessionId();
    if (cached.startsWith("wx_")) {
      return {
        sessionId: cached,
        identitySource: "durable",
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
      identitySource: "prototype_anon",
    };
  }
}

/**
 * The only Mini Program authority for Active Case, resume token, and navigation.
 * Local token storage is updated only from this server read and is never consulted
 * to decide the customer's route.
 */
export async function resolveCustomerContext(options?: {
  session?: CustomerSessionResult;
  launchToken?: string;
}): Promise<CustomerContextResult> {
  const session = options?.session || (await ensureCustomerSession());
  const body = await requestJson<CustomerContextApiBody>("POST", "/api/h5/customer/context", {
    session_id: session.sessionId,
    launch_token: String(options?.launchToken || "").trim() || undefined,
  });
  const applied = applyServerActiveCaseAuthority(body);
  const nextAction = String(body.next_action || "").trim() as CustomerNextAction;
  if (!nextAction) {
    clearResumeToken();
    throw new Error("customer_context_missing_next_action");
  }
  return {
    ...applied,
    nextAction,
  };
}

/**
 * Session id for Start Claim — durable wx_* preferred; anon only as isolated fallback.
 */
export async function resolveStartClaimSessionId(): Promise<string> {
  const session = await ensureCustomerSession();
  return session.sessionId;
}

/** Synchronous session id for lightweight hooks (e.g. Start Claim STT upload). */
export function getCustomerSessionId(): string {
  return loadCustomerSessionId() || getPrototypeSessionId();
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
