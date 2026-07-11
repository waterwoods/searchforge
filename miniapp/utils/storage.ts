const RESUME_TOKEN_KEY = "mp_prototype_resume_token";
const SUBMIT_INTENT_KEY = "mp_prototype_submit_intent";

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
}
