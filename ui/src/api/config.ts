/**
 * API Configuration
 * 
 * Centralizes the backend API base URL configuration.
 * 
 * In local development:
 * - If VITE_API_BASE_URL is not set, defaults to http://localhost:8000
 * - The Vite dev server proxy can still be used for /api routes
 * 
 * In production (Vercel):
 * - Set VITE_API_BASE_URL to your Cloud Run backend URL
 * - Example: https://mortgage-agent-api-xxxx.us-west1.run.app
 */

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL;

// Default for local dev if env var is not set
const DEFAULT_BASE_URL = "http://localhost:8000";

export const API_BASE_URL =
    (rawBaseUrl && rawBaseUrl.trim().length > 0 ? rawBaseUrl.trim() : DEFAULT_BASE_URL)
        .replace(/\/+$/, ""); // strip trailing slashes

