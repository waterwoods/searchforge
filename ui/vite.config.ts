// [vitals-lan] inspected - Vite dev server configuration for LAN access
import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig, loadEnv } from 'vite';

const __dirname = fileURLToPath(new URL('.', import.meta.url));
import react from '@vitejs/plugin-react';
import { goldenQaPreviewPlugin } from './vite.goldenQaPlugin';
import {
    assertVercelApiBaseUrl,
    resolveVercelDeployTarget,
} from './src/api/cloudBackendUrls';

/**
 * Vercel hosts the UI on HTTPS; API must be an absolute HTTPS origin.
 * P36 T5: Preview (Founder QA) → fiqa-api-qa only; Production → fiqa-api only.
 * Missing Preview URL fails closed — never silently falls back to Production.
 */
function assertVercelProductionApiBase(mode: string) {
    const result = assertVercelApiBaseUrl({
        vercel: process.env.VERCEL === '1',
        mode,
        vercelEnv: resolveVercelDeployTarget(process.env),
        rawBaseUrl: process.env.VITE_API_BASE_URL,
    });
    if (!result.ok) {
        throw new Error(result.error);
    }
}

// Build-time identity for release clarity (LA time, version, commit)
function getBuildId(): string {
    if (process.env.VERCEL_GIT_COMMIT_SHA) return process.env.VERCEL_GIT_COMMIT_SHA.slice(0, 7);
    try {
        return execSync('git rev-parse --short HEAD', { encoding: 'utf-8' }).trim();
    } catch {
        return 'dev';
    }
}
function getAppVersion(): string {
    try {
        const pkg = JSON.parse(readFileSync(new URL('./package.json', import.meta.url), 'utf-8'));
        return pkg.version || '0.1.0';
    } catch {
        return '0.1.0';
    }
}

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
    assertVercelProductionApiBase(mode);

    return {
    resolve: {
        alias: {
            '@': path.resolve(__dirname, 'src'),
        },
    },
    plugins: [
        react(),
        // DEV-only: local Preview inject for Launch Golden QA (never in production bundle logic)
        ...(mode === 'development' ? [goldenQaPreviewPlugin(path.resolve(__dirname, '..'))] : []),
    ],
    define: {
        __APP_VERSION__: JSON.stringify(getAppVersion()),
        __BUILD_TIME_ISO__: JSON.stringify(new Date().toISOString()),
        __BUILD_ID__: JSON.stringify(getBuildId()),
    },

    server: {
        port: 5173,
        host: "0.0.0.0", // [vitals-lan] allow lan access - listen on all network interfaces
        open: true,
        proxy: {
            // Proxy /api requests to backend (for local dev)
            // When VITE_API_BASE_URL is not set, UI can use relative /api paths
            // Proxy /api to backend. Default 8001 for demo. Set VITE_API_PROXY_TARGET for 8000.
            '/api': {
                target: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8001',
                changeOrigin: true,
                secure: false,
            },
            // Lightweight health check for demo status bar (avoids CORS in dev)
            '/healthz': {
                target: process.env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8001',
                changeOrigin: true,
                secure: false,
            },
            // Orchestration service proxy
            '/orchestrate': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false,
                rewrite: (path) => path.replace(/^\/orchestrate\b/, '/api/experiment'),
            },
        },
    },
};
});
