/**
 * P36 — Frozen Cloud backend URLs for Founder QA client routing.
 *
 * SSOT companion: docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md
 * Never point QA clients at Production. Never point Production at Cloud QA.
 */

/** Isolated Cloud QA API (fiqa-api-qa). */
export const CLOUD_QA_API_BASE_URL =
  'https://fiqa-api-qa-g7zatxrycq-uw.a.run.app';

/** Production paid-pilot API (fiqa-api). Unchanged by P36 T5. */
export const PRODUCTION_API_BASE_URL =
  'https://fiqa-api-g7zatxrycq-uw.a.run.app';

export type VercelDeployTarget = 'production' | 'preview' | 'development' | 'unknown';

export function normalizeApiBaseUrl(raw: string | undefined | null): string {
  return String(raw || '')
    .trim()
    .replace(/\/+$/, '');
}

export function isLoopbackApiBaseUrl(raw: string | undefined | null): boolean {
  const value = normalizeApiBaseUrl(raw).toLowerCase();
  return (
    value.includes('127.0.0.1') ||
    value.includes('localhost') ||
    value.startsWith('http://0.0.0.0')
  );
}

export function resolveVercelDeployTarget(env: NodeJS.ProcessEnv = process.env): VercelDeployTarget {
  const vercelEnv = String(env.VERCEL_ENV || '')
    .trim()
    .toLowerCase();
  if (vercelEnv === 'production' || vercelEnv === 'preview' || vercelEnv === 'development') {
    return vercelEnv;
  }
  // Fallback when VERCEL=1 but VERCEL_ENV unset (older tooling).
  if (String(env.VERCEL || '').trim() === '1') {
    return 'unknown';
  }
  return 'unknown';
}

export type ApiBaseGuardResult = { ok: true; url: string } | { ok: false; error: string };

/**
 * Fail-closed URL policy for Vercel builds.
 * - Preview (Founder QA): must be Cloud QA URL; must not be Production / localhost / missing.
 * - Production: must be Production URL; must not be Cloud QA / localhost / missing.
 */
export function assertVercelApiBaseUrl(params: {
  vercel: boolean;
  mode: string;
  vercelEnv?: VercelDeployTarget;
  rawBaseUrl?: string | null;
}): ApiBaseGuardResult {
  const { vercel, mode } = params;
  if (!vercel || mode !== 'production') {
    // Non-Vercel or Vite non-production mode: no hard fail here (local DEV uses proxy).
    return { ok: true, url: normalizeApiBaseUrl(params.rawBaseUrl) };
  }

  const target = params.vercelEnv || 'unknown';
  const url = normalizeApiBaseUrl(params.rawBaseUrl);

  if (!url) {
    return {
      ok: false,
      error:
        target === 'preview'
          ? `VITE_API_BASE_URL is required for Vercel Preview (Founder QA). Set Preview env to ${CLOUD_QA_API_BASE_URL} (no trailing slash). Do not fall back to Production.`
          : `VITE_API_BASE_URL is required for Vercel ${target} builds. Set it to the correct Cloud Run URL (no trailing slash). See docs/runbooks/CLOUD_QA_RESOURCE_NAMES.md`,
    };
  }

  if (isLoopbackApiBaseUrl(url) || url.startsWith('http://')) {
    return {
      ok: false,
      error:
        'VITE_API_BASE_URL must be an https:// public Cloud Run URL on Vercel (not localhost / http).',
    };
  }

  if (!url.startsWith('https://')) {
    return {
      ok: false,
      error:
        'VITE_API_BASE_URL must be an https:// URL on Vercel so the deployed site can call the API without mixed-content blocking.',
    };
  }

  if (target === 'preview') {
    if (url === PRODUCTION_API_BASE_URL) {
      return {
        ok: false,
        error: `Vercel Preview must not use Production API (${PRODUCTION_API_BASE_URL}). Set VITE_API_BASE_URL (Preview) to ${CLOUD_QA_API_BASE_URL}.`,
      };
    }
    if (url !== CLOUD_QA_API_BASE_URL) {
      return {
        ok: false,
        error: `Vercel Preview VITE_API_BASE_URL must be exactly ${CLOUD_QA_API_BASE_URL} (got "${url}").`,
      };
    }
    return { ok: true, url };
  }

  if (target === 'production') {
    if (url === CLOUD_QA_API_BASE_URL) {
      return {
        ok: false,
        error: `Vercel Production must not use Cloud QA API (${CLOUD_QA_API_BASE_URL}). Keep VITE_API_BASE_URL (Production) at ${PRODUCTION_API_BASE_URL}.`,
      };
    }
    if (url !== PRODUCTION_API_BASE_URL) {
      return {
        ok: false,
        error: `Vercel Production VITE_API_BASE_URL must be exactly ${PRODUCTION_API_BASE_URL} (got "${url}").`,
      };
    }
    return { ok: true, url };
  }

  // VERCEL=1 but VERCEL_ENV unknown: still refuse cross-wiring and localhost.
  if (url === CLOUD_QA_API_BASE_URL) {
    return {
      ok: false,
      error:
        'VERCEL_ENV is unset/unknown; refusing Cloud QA URL without an explicit Preview target. Set VERCEL_ENV=preview or use Production URL for production.',
    };
  }
  if (url === PRODUCTION_API_BASE_URL) {
    return { ok: true, url };
  }
  return {
    ok: false,
    error: `Unrecognized VITE_API_BASE_URL on Vercel ("${url}"). Expected Production ${PRODUCTION_API_BASE_URL} or Preview ${CLOUD_QA_API_BASE_URL}.`,
  };
}
