/**
 * Paid-pilot UI surface — hide lab/simulation chrome when building for broker deploy.
 *
 * Set on Vercel (Production + Preview): VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1
 * Supervised demo (Preview only): VITE_UNIFIED_INTAKE_SUPERVISED_DEMO=1
 *   → Customer-first preview: 客户报送 + 办公室工作台 + 场景仿真 (default 客户报送).
 *   → 我的办理 is a secondary action inside 客户报送, not a primary tab.
 * Mirrors backend UNIFIED_INTAKE_PRODUCT_ONLY; does not remove routes from the bundle.
 */

function truthy(raw: string | undefined): boolean {
    const v = (raw ?? '').trim().toLowerCase();
    return v === '1' || v === 'true' || v === 'yes' || v === 'on';
}

/** When true, sidebar and intake UI omit lab/simulation surfaces (routes may still exist). */
export function isUnifiedIntakeProductOnlyUi(): boolean {
    return truthy(import.meta.env.VITE_UNIFIED_INTAKE_PRODUCT_ONLY);
}

/** Preview/supervised demo: customer-first 3-tab preview (客户报送 · 办公室工作台 · 场景仿真). */
export function isUnifiedIntakeSupervisedDemoUi(): boolean {
    return truthy(import.meta.env.VITE_UNIFIED_INTAKE_SUPERVISED_DEMO);
}

/**
 * P25 — Internal QA Tools (Launch Golden QA).
 * Visible in Vite DEV by default, or when VITE_ENABLE_QA_TOOLS=1.
 * Never enable for customer-facing production builds unless explicitly set.
 */
export function isQaToolsEnabled(): boolean {
    if (truthy(import.meta.env.VITE_ENABLE_QA_TOOLS)) return true;
    if (truthy(import.meta.env.VITE_DISABLE_QA_TOOLS)) return false;
    return Boolean(import.meta.env.DEV);
}

/**
 * Chen Demo Invite launcher (陈总演示工具).
 * QA / Preview only — never on Production workbench API profile.
 */
export function isChenDemoInviteUiEnabled(): boolean {
    if (truthy(import.meta.env.VITE_DISABLE_CHEN_DEMO_INVITE)) return false;
    if (!isQaToolsEnabled()) return false;

    const api = String(import.meta.env.VITE_API_BASE_URL || '').trim().toLowerCase();
    const isProductionApi =
        (api.includes('fiqa-api-') && api.includes('.run.app') && !api.includes('fiqa-api-qa')) ||
        api.includes('fiqa-api-g7zatxrycq'); // known Production hostname

    // Hard-off when UI is baked against Production API — even if QA tools flag leaked.
    if (isProductionApi) return false;

    // Preview / local with QA tools: show panel (API still gated by CHEN_DEMO_INVITE_ENABLED).
    return true;
}
