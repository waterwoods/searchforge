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
