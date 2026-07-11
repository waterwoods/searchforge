/**
 * Prototype session identity — mock/dev only.
 * Does NOT implement production openid / unionid binding.
 */
export function getPrototypeSessionId(): string {
  const key = "mp_prototype_anon_session";
  try {
    const existing = String(wx.getStorageSync(key) || "").trim();
    if (existing) return existing;
    const created = `anon-${Date.now().toString(36)}`;
    wx.setStorageSync(key, created);
    return created;
  } catch {
    return `anon-${Date.now().toString(36)}`;
  }
}

export function getSessionIdentityLabel(): string {
  return "原型访客（未绑定微信身份）";
}
