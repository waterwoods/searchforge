const RESUME_TOKEN_KEY = "mp_prototype_resume_token";
const SUBMIT_INTENT_KEY = "mp_prototype_submit_intent";
const CUSTOMER_SESSION_KEY = "mp_customer_session_id";

export function saveResumeToken(token: string): void {
  try {
    wx.setStorageSync(RESUME_TOKEN_KEY, token);
  } catch {
    // prototype — ignore storage failures
  }
}

export function loadResumeToken(): string {
  try {
    return String(wx.getStorageSync(RESUME_TOKEN_KEY) || "").trim();
  } catch {
    return "";
  }
}

export function clearResumeToken(): void {
  try {
    wx.removeStorageSync(RESUME_TOKEN_KEY);
  } catch {
    // ignore
  }
}

export function saveCustomerSessionId(sessionId: string): void {
  const sid = String(sessionId || "").trim().slice(0, 80);
  if (!sid) return;
  try {
    wx.setStorageSync(CUSTOMER_SESSION_KEY, sid);
  } catch {
    // ignore
  }
}

export function loadCustomerSessionId(): string {
  try {
    return String(wx.getStorageSync(CUSTOMER_SESSION_KEY) || "").trim();
  } catch {
    return "";
  }
}

export function clearCustomerSessionId(): void {
  try {
    wx.removeStorageSync(CUSTOMER_SESSION_KEY);
  } catch {
    // ignore
  }
}

export function saveSubmitIntentId(intentId: string): void {
  try {
    wx.setStorageSync(SUBMIT_INTENT_KEY, intentId);
  } catch {
    // ignore
  }
}

export function loadSubmitIntentId(): string {
  try {
    return String(wx.getStorageSync(SUBMIT_INTENT_KEY) || "").trim();
  } catch {
    return "";
  }
}

export function clearSubmitIntentId(): void {
  try {
    wx.removeStorageSync(SUBMIT_INTENT_KEY);
  } catch {
    // ignore
  }
}

/** Developer-only reset — not customer UI */
export function clearPrototypeSession(): void {
  clearResumeToken();
  clearSubmitIntentId();
  clearCustomerSessionId();
}
