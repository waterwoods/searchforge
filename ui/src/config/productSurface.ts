/**
 * Paid-pilot UI surface — hide lab/simulation chrome when building for broker deploy.
 *
 * Set on Vercel (Production + Preview): VITE_UNIFIED_INTAKE_PRODUCT_ONLY=1
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
