/**
 * One-shot flag: Entry resume → destination page shows a brief confirmation toast.
 * Avoids silently restoring prior draft (TurboTax / Lemonade continuity cue).
 */

const RESUME_RESTORED_KEY = "__mp_resume_restored_hint";

type HintHost = WechatMiniprogram.IAnyObject & {
  [RESUME_RESTORED_KEY]?: boolean;
};

function appHost(): HintHost | null {
  try {
    return getApp<IAppOption>() as HintHost;
  } catch {
    return null;
  }
}

export function markResumeRestoredHint(): void {
  const app = appHost();
  if (app) app[RESUME_RESTORED_KEY] = true;
}

/** Returns true once, then clears. */
export function consumeResumeRestoredHint(): boolean {
  const app = appHost();
  if (!app || !app[RESUME_RESTORED_KEY]) return false;
  app[RESUME_RESTORED_KEY] = false;
  return true;
}
