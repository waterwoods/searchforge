/// <reference types="vite/client" />

declare const __APP_VERSION__: string;
declare const __BUILD_TIME_ISO__: string;
declare const __BUILD_ID__: string;

interface ImportMetaEnv {
    readonly VITE_API_BASE?: string;
    readonly VITE_API_BASE_URL?: string;
    /** production | preview | local — set in Vercel per env */
    readonly VITE_APP_ENV?: string;
    /** When 1/true: hide lab sidebar + simulation tab (paid-pilot Vercel UI). */
    readonly VITE_UNIFIED_INTAKE_PRODUCT_ONLY?: string;
    /** When 1/true with product_only: customer-first 3-tab preview; 我的办理 as secondary action in 客户报送. */
    readonly VITE_UNIFIED_INTAKE_SUPERVISED_DEMO?: string;
    readonly VITE_UNIFIED_INTAKE_INTAKE_API_KEY?: string;
}

interface ImportMeta {
    readonly env: ImportMetaEnv;
}

