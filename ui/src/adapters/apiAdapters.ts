/**
 * API Adapters - Convert backend responses to safe frontend types
 * Handles missing/malformed fields with safe defaults
 */

import type { LabMiniReportResponse } from './types.generated'

export interface SafeMiniReport {
    ok: boolean;
    deltaP95Pct: number;
    deltaQpsPct: number;
    errorRatePct: number;
    message: string;
    generatedAt: string;
}

export interface SafeLabOpsReport {
    ok: boolean;
    verdict: string | null;
    deltaP95Pct: number;
    deltaQpsPct: number;
    errorRatePct: number;
    faissSharePct: number;
    applied: boolean;
    applyCommand: string | null;
    message: string;
    generatedAt: string;
}

/**
 * Convert any value to safe string representation
 * Prevents React "Objects are not valid as a React child" errors
 */
export function toStringSafe(value: unknown): string {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'string') return value;
    if (typeof value === 'number') return value.toString();
    if (typeof value === 'boolean') return value ? 'true' : 'false';
    if (typeof value === 'object') {
        try {
            return JSON.stringify(value);
        } catch {
            return '[Object]';
        }
    }
    return String(value);
}

/**
 * Safely convert value to number with fallback
 */
function toNumberSafe(value: unknown, defaultValue: number = 0): number {
    if (typeof value === 'number' && !isNaN(value)) return value;
    if (typeof value === 'string') {
        const parsed = parseFloat(value);
        return isNaN(parsed) ? defaultValue : parsed;
    }
    return defaultValue;
}

/**
 * Adapt mini report response to safe frontend format
 */
export function adaptMiniReport(raw: unknown): SafeMiniReport {
    // Handle completely invalid input
    if (!raw || typeof raw !== 'object') {
        return {
            ok: false,
            deltaP95Pct: 0,
            deltaQpsPct: 0,
            errorRatePct: 0,
            message: 'No report yet',
            generatedAt: '-'
        };
    }

    const data = raw as Partial<LabMiniReportResponse>;

    return {
        ok: Boolean(data.ok),
        deltaP95Pct: toNumberSafe(data.delta_p95_pct, 0),
        deltaQpsPct: toNumberSafe(data.delta_qps_pct, 0),
        errorRatePct: toNumberSafe(data.error_rate_pct, 0),
        message: toStringSafe(data.message || 'No report yet'),
        generatedAt: toStringSafe(data.generated_at || '-')
    };
}

/**
 * Fetch mini report from backend
 */
export async function fetchMiniReport(baseUrl?: string): Promise<SafeMiniReport> {
    // Use empty string to use same origin (proxy)
    const apiBase = baseUrl || '';

    try {
        const response = await fetch(`${apiBase}/api/lab/report?mini=1`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            // Even on error, try to parse response
            try {
                const errorData = await response.json();
                return adaptMiniReport(errorData);
            } catch {
                return adaptMiniReport(null);
            }
        }

        const data = await response.json();
        return adaptMiniReport(data);
    } catch (error) {
        console.error('Failed to fetch mini report:', error);
        return {
            ok: false,
            deltaP95Pct: 0,
            deltaQpsPct: 0,
            errorRatePct: 0,
            message: `Error: ${toStringSafe(error)}`,
            generatedAt: '-'
        };
    }
}

/**
 * Adapt LabOps agent report response to safe frontend format
 */
export function adaptLabOpsReport(raw: unknown): SafeLabOpsReport {
    // Handle completely invalid input
    if (!raw || typeof raw !== 'object') {
        return {
            ok: false,
            verdict: null,
            deltaP95Pct: 0,
            deltaQpsPct: 0,
            errorRatePct: 0,
            faissSharePct: 0,
            applied: false,
            applyCommand: null,
            message: 'No agent report yet',
            generatedAt: '-'
        };
    }

    const data = raw as any;

    return {
        ok: Boolean(data.ok),
        verdict: data.verdict ? toStringSafe(data.verdict) : null,
        deltaP95Pct: toNumberSafe(data.delta_p95_pct, 0),
        deltaQpsPct: toNumberSafe(data.delta_qps_pct, 0),
        errorRatePct: toNumberSafe(data.error_rate_pct, 0),
        faissSharePct: toNumberSafe(data.faiss_share_pct, 0),
        applied: Boolean(data.applied),
        applyCommand: data.apply_command ? toStringSafe(data.apply_command) : null,
        message: toStringSafe(data.message || 'No agent report yet'),
        generatedAt: data.generated_at ? toStringSafe(new Date(data.generated_at * 1000).toLocaleString()) : '-'
    };
}

/**
 * Fetch LabOps agent last report from backend
 */
export async function fetchLabOpsReport(baseUrl?: string): Promise<SafeLabOpsReport> {
    // Use empty string to use same origin (proxy)
    const apiBase = baseUrl || '';

    try {
        const response = await fetch(`${apiBase}/api/labops/last`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
        });

        if (!response.ok) {
            // Even on error, try to parse response
            try {
                const errorData = await response.json();
                return adaptLabOpsReport(errorData);
            } catch {
                return adaptLabOpsReport(null);
            }
        }

        const data = await response.json();
        return adaptLabOpsReport(data);
    } catch (error) {
        console.error('Failed to fetch LabOps report:', error);
        return {
            ok: false,
            verdict: null,
            deltaP95Pct: 0,
            deltaQpsPct: 0,
            errorRatePct: 0,
            faissSharePct: 0,
            applied: false,
            applyCommand: null,
            message: `Error: ${toStringSafe(error)}`,
            generatedAt: '-'
        };
    }
}


