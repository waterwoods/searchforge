/**
 * WeChat privacy authorization gate (release hardening).
 *
 * Layers are separate:
 *   PRIVACY CONSENT (this module)
 *   → DEVICE/API PERMISSION (scope.record / chooseMedia)
 *   → RECORDING / CAPTURE
 *
 * Console「用户隐私保护指引」must still be configured by Founder —
 * code cannot replace that declaration.
 */

export type PrivacyPurpose = "record" | "chooseMedia";

export type PrivacyAuthorizeStatus =
  | "already_authorized"
  | "authorized"
  | "unsupported"
  | "denied"
  | "cancelled"
  | "busy";

export type PrivacyAuthorizeResult = {
  ok: boolean;
  status: PrivacyAuthorizeStatus;
};

export type MicrophoneReadyResult = {
  ok: boolean;
  /** Which layer stopped the flow when ok=false. */
  stage: "privacy" | "scope" | "ready";
  privacyStatus: PrivacyAuthorizeStatus | null;
  reason?: "privacy_denied" | "privacy_busy" | "scope_denied";
};

/** Short Chinese disclosure before WeChat privacy authorize (microphone). */
export const PRIVACY_DISCLOSURE_RECORD =
  "为了将您的事故描述转换成文字，需要使用麦克风。录音仅用于整理本次案件信息。";

/** Short Chinese disclosure before WeChat privacy authorize (camera/album). */
export const PRIVACY_DISCLOSURE_MEDIA =
  "为了上传事故照片资料，需要使用相机或相册。照片仅用于整理本次案件信息。";

export const PRIVACY_DISCLOSURE_TITLE = "隐私授权说明";

/** Calm copy when privacy consent is declined — keep text intake available. */
export const PRIVACY_DENIED_RECORD_HINT =
  "未同意隐私授权。不方便录音？请改用文字输入。";

export const PRIVACY_DENIED_MEDIA_HINT =
  "未同意隐私授权，无法打开相机或相册。您可稍后重试。";

type PrivacySettingResult = {
  needAuthorization?: boolean;
  privacyContractName?: string;
};

type WxPrivacy = {
  getPrivacySetting?: (opts: {
    success?: (res: PrivacySettingResult) => void;
    fail?: () => void;
  }) => void;
  requirePrivacyAuthorize?: (opts: {
    success?: () => void;
    fail?: () => void;
  }) => void;
  authorize?: (opts: {
    scope: string;
    success?: () => void;
    fail?: () => void;
  }) => void;
  showModal?: (opts: {
    title?: string;
    content?: string;
    confirmText?: string;
    cancelText?: string;
    success?: (res: { confirm?: boolean; cancel?: boolean }) => void;
    fail?: () => void;
  }) => void;
};

let inFlight: Promise<PrivacyAuthorizeResult> | null = null;

function wxApi(): WxPrivacy | null {
  if (typeof wx === "undefined") return null;
  return wx as unknown as WxPrivacy;
}

function getPrivacySetting(): Promise<PrivacySettingResult | null> {
  const api = wxApi();
  if (!api || typeof api.getPrivacySetting !== "function") {
    return Promise.resolve(null);
  }
  return new Promise((resolve) => {
    try {
      api.getPrivacySetting!({
        success: (res) => resolve(res || {}),
        fail: () => resolve(null),
      });
    } catch {
      resolve(null);
    }
  });
}

function requirePrivacyAuthorize(): Promise<"authorized" | "denied"> {
  const api = wxApi();
  if (!api || typeof api.requirePrivacyAuthorize !== "function") {
    // Older runtime after user saw our disclosure — allow device permission next.
    return Promise.resolve("authorized");
  }
  return new Promise((resolve) => {
    try {
      api.requirePrivacyAuthorize!({
        success: () => resolve("authorized"),
        fail: () => resolve("denied"),
      });
    } catch {
      resolve("denied");
    }
  });
}

function showDisclosureModal(purpose: PrivacyPurpose): Promise<boolean> {
  const api = wxApi();
  const content =
    purpose === "chooseMedia" ? PRIVACY_DISCLOSURE_MEDIA : PRIVACY_DISCLOSURE_RECORD;
  if (!api || typeof api.showModal !== "function") {
    // No modal available — continue to WeChat privacy API / device permission.
    return Promise.resolve(true);
  }
  return new Promise((resolve) => {
    try {
      api.showModal!({
        title: PRIVACY_DISCLOSURE_TITLE,
        content,
        confirmText: "同意",
        cancelText: "不同意",
        success: (res) => resolve(Boolean(res && res.confirm)),
        fail: () => resolve(false),
      });
    } catch {
      resolve(false);
    }
  });
}

function authorizeScopeRecord(): Promise<boolean> {
  const api = wxApi();
  if (!api || typeof api.authorize !== "function") {
    // DevTools / incomplete mock — do not block recording start.
    return Promise.resolve(true);
  }
  return new Promise((resolve) => {
    try {
      api.authorize!({
        scope: "scope.record",
        success: () => resolve(true),
        fail: () => resolve(false),
      });
    } catch {
      resolve(false);
    }
  });
}

async function runEnsurePrivacyAuthorized(
  purpose: PrivacyPurpose,
  opts?: { showDisclosure?: boolean },
): Promise<PrivacyAuthorizeResult> {
  const setting = await getPrivacySetting();

  // Older base library / missing API — privacy check not available; proceed.
  if (setting === null) {
    return { ok: true, status: "unsupported" };
  }

  if (!setting.needAuthorization) {
    return { ok: true, status: "already_authorized" };
  }

  const showDisclosure = opts?.showDisclosure !== false;
  if (showDisclosure) {
    const agreed = await showDisclosureModal(purpose);
    if (!agreed) {
      return { ok: false, status: "cancelled" };
    }
  }

  const outcome = await requirePrivacyAuthorize();
  if (outcome === "denied") {
    return { ok: false, status: "denied" };
  }
  return { ok: true, status: "authorized" };
}

/**
 * Ensure WeChat privacy consent for a privacy-sensitive purpose.
 * Does NOT request scope.record or open the camera — callers do that next.
 */
export function ensurePrivacyAuthorized(
  purpose: PrivacyPurpose,
  opts?: { showDisclosure?: boolean },
): Promise<PrivacyAuthorizeResult> {
  if (inFlight) {
    return Promise.resolve({ ok: false, status: "busy" });
  }
  inFlight = runEnsurePrivacyAuthorized(purpose, opts).finally(() => {
    inFlight = null;
  });
  return inFlight;
}

/** Test-only: clear in-flight lock between cases. */
export function resetPrivacyAuthorizeInFlightForTests(): void {
  inFlight = null;
}

/**
 * Privacy consent → scope.record. Recording start stays in the page.
 */
export async function ensureMicrophoneReady(opts?: {
  showDisclosure?: boolean;
}): Promise<MicrophoneReadyResult> {
  const privacy = await ensurePrivacyAuthorized("record", opts);
  if (!privacy.ok) {
    return {
      ok: false,
      stage: "privacy",
      privacyStatus: privacy.status,
      reason: privacy.status === "busy" ? "privacy_busy" : "privacy_denied",
    };
  }

  const scopeOk = await authorizeScopeRecord();
  if (!scopeOk) {
    return {
      ok: false,
      stage: "scope",
      privacyStatus: privacy.status,
      reason: "scope_denied",
    };
  }

  return {
    ok: true,
    stage: "ready",
    privacyStatus: privacy.status,
  };
}
