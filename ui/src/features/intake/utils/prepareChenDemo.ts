/**
 * QA Fast Lane V1 — one-click Prepare Demo orchestration (pure + injectable I/O).
 *
 * Safe order: Cloud QA gate → session → P35 Fresh → office reset → issue → validate.
 * Never issues an invite before Fresh completes. Never PASSes on failed validation.
 */
import {
  CLOUD_QA_API_BASE_URL,
  PRODUCTION_API_BASE_URL,
  normalizeApiBaseUrl,
} from '@/api/cloudBackendUrls';
import type { DemoInviteEntryPayload, DemoInviteIssued, DemoInviteValidateResult } from '@/api/demoInvite';
import { buildDemoInviteEntryPayload } from '@/api/demoInvite';
import {
  resolveWorkbenchClientEnv,
  type WorkbenchClientEnv,
} from '@/config/workbenchEnv';

export type PrepareDemoStep =
  | 'gate_api'
  | 'require_session'
  | 'clear_previous'
  | 'p35_fresh'
  | 'office_reset'
  | 'issue'
  | 'validate'
  | 'done';

export type PrepareDemoVerdict = 'PASS' | 'FAIL';

export type PrepareDemoResult = {
  ok: boolean;
  verdict: PrepareDemoVerdict;
  steps: PrepareDemoStep[];
  error?: string;
  issued?: DemoInviteIssued;
  validation?: DemoInviteValidateResult;
  entry?: DemoInviteEntryPayload;
  /** Controls that must stay locked while this active invite is displayed. */
  lockResetAndReprepare: boolean;
};

export type PrepareDemoDeps = {
  runFresh: (sessionId: string) => Promise<{ ok?: boolean } | void>;
  resetOffice: (officeId: string) => Promise<unknown>;
  resetOverlay?: (sessionId: string) => Promise<unknown>;
  issueInvite: (body: {
    office_id: string;
    scenario_id: string;
  }) => Promise<DemoInviteIssued>;
  validateInvite: (body: {
    token: string;
    office_id?: string;
  }) => Promise<DemoInviteValidateResult>;
  nowSec?: () => number;
};

export type PrepareDemoInput = {
  apiBaseUrl: string;
  sessionId: string;
  scenarioId: string;
  officeId: string;
  /** In-flight lock — duplicate clicks must not start a competing run. */
  busy?: boolean;
};

const WX_SESSION_RE = /^wx_[A-Za-z0-9_-]{8,}$/;

export function resolvePrepareDemoApiEnv(apiBaseUrl: string): WorkbenchClientEnv {
  return resolveWorkbenchClientEnv(apiBaseUrl);
}

/** Hard-block Prepare Demo unless the UI is wired to Cloud QA exactly. */
export function assertPrepareDemoCloudQa(apiBaseUrl: string): string | null {
  const env = resolvePrepareDemoApiEnv(apiBaseUrl);
  const url = normalizeApiBaseUrl(apiBaseUrl);
  if (env === 'production' || url === PRODUCTION_API_BASE_URL) {
    return 'Production API 已硬阻断 — 一键准备演示仅允许 Cloud QA (fiqa-api-qa)。';
  }
  if (env !== 'qa' || url !== CLOUD_QA_API_BASE_URL) {
    return `当前 API 不是 Cloud QA。需要 ${CLOUD_QA_API_BASE_URL}（当前：${url || 'unknown'}）。`;
  }
  return null;
}

export function normalizeApprovedQaSessionId(raw: string | null | undefined): string | null {
  const sid = String(raw || '').trim();
  if (!sid) return null;
  if (!WX_SESSION_RE.test(sid)) return null;
  return sid;
}

export function evaluateInvitePreparePass(params: {
  issued: DemoInviteIssued;
  validation: DemoInviteValidateResult;
  expectedScenarioId: string;
  nowSec: number;
}): { pass: boolean; reason?: string } {
  const { issued, validation, expectedScenarioId, nowSec } = params;
  if (!validation || validation.ok !== true) {
    return { pass: false, reason: 'validation_not_ok' };
  }
  if (String(validation.status || '') !== 'active') {
    return { pass: false, reason: `status_${validation.status || 'unknown'}` };
  }
  const inviteScenario =
    String((validation.invite as { scenario_id?: string } | undefined)?.scenario_id || '') ||
    String(issued.scenario_id || '');
  if (inviteScenario !== expectedScenarioId || issued.scenario_id !== expectedScenarioId) {
    return { pass: false, reason: 'scenario_mismatch' };
  }
  const useCount = Number(
    (validation.invite as { use_count?: number } | undefined)?.use_count ??
      issued.use_count ??
      0,
  );
  if (useCount !== 0) {
    return { pass: false, reason: 'use_count_not_zero' };
  }
  const expiresAt = Number(
    (validation.invite as { expires_at?: number } | undefined)?.expires_at ??
      issued.expires_at ??
      0,
  );
  if (!(expiresAt > nowSec)) {
    return { pass: false, reason: 'expiration_invalid' };
  }
  return { pass: true };
}

export function formatExpiryCountdown(expiresAtSec: number, nowSec: number): string {
  const left = Math.floor(expiresAtSec - nowSec);
  if (left <= 0) return '已过期';
  const h = Math.floor(left / 3600);
  const m = Math.floor((left % 3600) / 60);
  const s = left % 60;
  if (h > 0) return `${h}小时${m}分${s}秒`;
  if (m > 0) return `${m}分${s}秒`;
  return `${s}秒`;
}

/**
 * Ordered Prepare Demo. Throws never — returns FAIL with error.
 * Callers must clear previous invite UI before invoking (or rely on clear_previous step marker).
 */
export async function prepareChenDemo(
  input: PrepareDemoInput,
  deps: PrepareDemoDeps,
): Promise<PrepareDemoResult> {
  const steps: PrepareDemoStep[] = [];

  if (input.busy) {
    return {
      ok: false,
      verdict: 'FAIL',
      steps,
      error: 'prepare_already_running',
      lockResetAndReprepare: false,
    };
  }

  steps.push('gate_api');
  const gateErr = assertPrepareDemoCloudQa(input.apiBaseUrl);
  if (gateErr) {
    return {
      ok: false,
      verdict: 'FAIL',
      steps,
      error: gateErr,
      lockResetAndReprepare: false,
    };
  }

  steps.push('require_session');
  const sessionId = normalizeApprovedQaSessionId(input.sessionId);
  if (!sessionId) {
    return {
      ok: false,
      verdict: 'FAIL',
      steps,
      error: '需要已批准的 QA session_id（精确 wx_*）。请先在 Engineering QA Console 选择身份，或粘贴手机 session。',
      lockResetAndReprepare: false,
    };
  }

  const scenarioId = String(input.scenarioId || '').trim();
  const officeId = String(input.officeId || '').trim();
  if (!scenarioId || !officeId) {
    return {
      ok: false,
      verdict: 'FAIL',
      steps,
      error: 'scenario_or_office_missing',
      lockResetAndReprepare: false,
    };
  }

  steps.push('clear_previous');

  try {
    steps.push('p35_fresh');
    const freshRes = await deps.runFresh(sessionId);
    if (freshRes && typeof freshRes === 'object' && freshRes.ok === false) {
      return {
        ok: false,
        verdict: 'FAIL',
        steps,
        error: 'p35_fresh_failed',
        lockResetAndReprepare: false,
      };
    }

    // Office reset ONLY after Fresh and BEFORE issuing a new invite.
    steps.push('office_reset');
    await deps.resetOffice(officeId);
    if (deps.resetOverlay) {
      await deps.resetOverlay(sessionId);
    }

    steps.push('issue');
    const issued = await deps.issueInvite({
      office_id: officeId,
      scenario_id: scenarioId,
    });

    steps.push('validate');
    const validation = await deps.validateInvite({
      token: issued.token,
      office_id: officeId,
    });

    const nowSec = (deps.nowSec || (() => Math.floor(Date.now() / 1000)))();
    const evalPass = evaluateInvitePreparePass({
      issued,
      validation,
      expectedScenarioId: scenarioId,
      nowSec,
    });

    steps.push('done');
    if (!evalPass.pass) {
      return {
        ok: false,
        verdict: 'FAIL',
        steps,
        error: `invite_validation_failed:${evalPass.reason || 'unknown'}`,
        issued,
        validation,
        entry: buildDemoInviteEntryPayload(issued),
        lockResetAndReprepare: false,
      };
    }

    return {
      ok: true,
      verdict: 'PASS',
      steps,
      issued,
      validation,
      entry: buildDemoInviteEntryPayload(issued),
      lockResetAndReprepare: true,
    };
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e || 'prepare_failed');
    return {
      ok: false,
      verdict: 'FAIL',
      steps,
      error: msg,
      lockResetAndReprepare: false,
    };
  }
}
