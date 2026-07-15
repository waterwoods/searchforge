/**
 * API Configuration
 *
 * Centralizes the backend API base URL configuration.
 *
 * In local development:
 * - If VITE_API_BASE_URL is not set, use "" so relative paths (/api, /healthz) hit Vite proxy
 * - Proxy target is configured in vite.config.ts (default 8001)
 *
 * In production:
 * - Set VITE_API_BASE_URL to your backend URL (e.g. Cloud Run)
 */

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

