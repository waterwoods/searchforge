/**
 * API Configuration
 *
 * Centralizes the backend API base URL configuration.
 *
 * In local development:
 * - If VITE_API_BASE_URL is not set, use "" so relative paths (/api, /healthz) hit Vite proxy
 * - Proxy target is configured in vite.config.ts (default 8001)
 *
 * On Vercel (P36 T5):
 * - Preview (Founder QA): VITE_API_BASE_URL = Cloud QA (fiqa-api-qa)
 * - Production: VITE_API_BASE_URL = Production (fiqa-api) — unchanged
 * - Build-time guard in vite.config.ts fails closed on cross-wiring / missing Preview URL
 *
 * Frozen URL constants: ./cloudBackendUrls.ts
 */

export {
    CLOUD_QA_API_BASE_URL,
    PRODUCTION_API_BASE_URL,
} from './cloudBackendUrls';

const viteEnv = import.meta.env ?? {};
const rawBaseUrl = viteEnv.VITE_API_BASE_URL;
const rawBasePath = viteEnv.VITE_API_BASE;

const preferredBase = viteEnv.DEV
    ? ""
    : rawBaseUrl && rawBaseUrl.trim().length > 0
        ? rawBaseUrl.trim()
        : rawBasePath && rawBasePath.trim().length > 0
            ? rawBasePath.trim()
            : "";

export const API_BASE_URL = preferredBase.replace(/\/+$/, ""); // strip trailing slashes

