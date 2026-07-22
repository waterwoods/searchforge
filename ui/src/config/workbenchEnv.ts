/**
 * Broker Workbench URL + environment SSOT (Founder QA alignment).
 *
 * Canonical Founder QA surface: document-intake on the QA Vercel Preview alias.
 * Production keeps document-intake on the Production alias (separate API).
 * Do not use ui-smoky-beta for Golden / Cloud QA cases.
 */

import {
  CLOUD_QA_API_BASE_URL,
  PRODUCTION_API_BASE_URL,
  normalizeApiBaseUrl,
} from '../api/cloudBackendUrls';
import { API_BASE_URL } from '../api/config';

/** Stable QA Preview host (baked to Cloud QA API). */
export const WORKBENCH_QA_HOST = 'https://ui-waterwoods-andys-projects-1f411b73.vercel.app';

/** Production alias (baked to Production API). */
export const WORKBENCH_PRODUCTION_HOST = 'https://ui-smoky-beta.vercel.app';

export const DOCUMENT_INTAKE_PATH = '/workbench/document-intake';

/** Canonical Founder QA Broker Workbench — Phone + Golden share Cloud QA with this UI. */
export const WORKBENCH_QA_DOCUMENT_INTAKE_URL = `${WORKBENCH_QA_HOST}${DOCUMENT_INTAKE_PATH}`;

/** Production Broker Workbench (paid pilot / live office). */
export const WORKBENCH_PRODUCTION_DOCUMENT_INTAKE_URL = `${WORKBENCH_PRODUCTION_HOST}${DOCUMENT_INTAKE_PATH}`;

export type WorkbenchClientEnv = 'qa' | 'production' | 'local' | 'unknown';

export function resolveWorkbenchClientEnv(
  apiBaseUrl: string = API_BASE_URL,
): WorkbenchClientEnv {
  const url = normalizeApiBaseUrl(apiBaseUrl);
  if (!url) return 'local';
  if (url === CLOUD_QA_API_BASE_URL) return 'qa';
  if (url === PRODUCTION_API_BASE_URL) return 'production';
  // Legacy Production Cloud Run hostname still seen on some Production aliases.
  if (url.includes('fiqa-api-') && url.includes('.run.app') && !url.includes('fiqa-api-qa')) {
    return 'production';
  }
  return 'unknown';
}

export function isCloudQaWorkbenchClient(apiBaseUrl: string = API_BASE_URL): boolean {
  return resolveWorkbenchClientEnv(apiBaseUrl) === 'qa';
}

/** Short API profile label for QA header (never a full secrets dump). */
export function workbenchApiProfileLabel(apiBaseUrl: string = API_BASE_URL): string {
  const env = resolveWorkbenchClientEnv(apiBaseUrl);
  if (env === 'qa') return 'fiqa-api-qa';
  if (env === 'production') return 'fiqa-api';
  if (env === 'local') return 'local';
  const host = normalizeApiBaseUrl(apiBaseUrl).replace(/^https?:\/\//, '').split('/')[0];
  return host || 'unknown';
}
