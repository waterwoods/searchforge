import type { TaskLaunchContext } from "../types/task";
import { appConfig } from "../utils/config";
import { loadResumeToken, saveResumeToken } from "../utils/storage";

/**
 * Prototype task launch — token from query, dev config, or resume storage.
 * No production openid / WeCom card dependency.
 */
export function resolveTaskLaunchContext(
  options?: WechatMiniprogram.Page.IAnyObject,
): TaskLaunchContext | null {
  const queryToken = String(options?.token || "").trim();
  if (queryToken) {
    return { token: queryToken, source: "launch_query" };
  }

  const devToken = String(appConfig.devTaskToken || "").trim();
  if (devToken) {
    return { token: devToken, source: "dev_config" };
  }

  const resumeToken = loadResumeToken();
  if (resumeToken) {
    return { token: resumeToken, source: "resume_storage" };
  }

  return null;
}

export function persistLaunchToken(ctx: TaskLaunchContext): void {
  saveResumeToken(ctx.token);
}

export function tokenPreview(token: string): string {
  const t = (token || "").trim();
  if (t.length <= 10) return "…";
  return `${t.slice(0, 6)}…${t.slice(-4)}`;
}
