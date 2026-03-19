/// <reference types="vite/client" />

declare const __APP_VERSION__: string;
declare const __BUILD_TIME_ISO__: string;
declare const __BUILD_ID__: string;

interface ImportMetaEnv {
    readonly VITE_API_BASE?: string;
    readonly VITE_API_BASE_URL?: string;
    /** production | preview | local — set in Vercel per env */
    readonly VITE_APP_ENV?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}

