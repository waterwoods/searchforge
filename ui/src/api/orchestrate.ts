/**
 * Orchestrate API helpers for chat presets.
 *
 * Provides minimal utilities to submit runs and poll their status via the
 * dev proxy (`/orchestrate` → `/api/experiment`).
 */

export interface OrchestrateRunPayload {
    preset?: unknown;
    prompt?: unknown;
    overrides?: unknown;
    [key: string]: unknown;
}

export interface PostRunResponse {
    job_id: string;
    poll?: string;
}

const normalizeBase = (value: string): string => {
    if (!value) {
        return '/orchestrate';
    }
    const trimmed = value.trim();
    if (!trimmed) {
        return '/orchestrate';
    }

    const withoutTrailing = trimmed.replace(/\/+$/, '');
    if (withoutTrailing.startsWith('http')) {
        // Leave absolute URLs untouched except trailing slash removal.
        return withoutTrailing;
    }

    // Ensure leading slash for relative paths.
    return withoutTrailing.startsWith('/') ? withoutTrailing : `/${withoutTrailing}`;
};

export const resolveBase = (): string => {
    const raw = (import.meta as any)?.env?.VITE_ORCH_BASE;
    return normalizeBase(typeof raw === 'string' ? raw : '/orchestrate');
};

const serializeValue = (value: unknown, seen: WeakSet<object>): unknown => {
    if (value == null) {
        return value;
    }
    if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        return value;
    }
    if (Array.isArray(value)) {
        return value.map((item) => serializeValue(item, seen));
    }
    if (typeof value === 'object') {
        if (seen.has(value as object)) {
            return '[Circular]';
        }
        seen.add(value as object);
        const entries = Object.entries(value as Record<string, unknown>).map(([key, val]) => {
            return [key, serializeValue(val, seen)];
        });
        seen.delete(value as object);
        return Object.fromEntries(entries);
    }
    try {
        return String(value);
    } catch {
        return Object.prototype.toString.call(value);
    }
};

const sanitizePayload = (payload: OrchestrateRunPayload): Record<string, unknown> => {
    const allowedKeys = ['preset', 'prompt', 'overrides'] as const;
    const seen = new WeakSet<object>();
    const result: Record<string, unknown> = {};

    for (const key of allowedKeys) {
        if (Object.prototype.hasOwnProperty.call(payload, key) && payload[key] !== undefined) {
            result[key] = serializeValue(payload[key], seen);
        }
    }

    return result;
};

const jsonHeaders = {
    'Content-Type': 'application/json',
};

export async function safeError(error: unknown): Promise<string> {
    if (error instanceof Response) {
        try {
            const cloned = error.clone();
            const contentType = cloned.headers.get('content-type') || '';
            if (contentType.includes('application/json')) {
                const data = await cloned.json();
                if (data) {
                    const detail = data.detail ?? data.error ?? data.message ?? data.msg;
                    if (typeof detail === 'string' && detail.trim()) {
                        return detail;
                    }
                    return JSON.stringify(data);
                }
            }
            const text = await cloned.text();
            if (text.trim()) {
                return text.trim();
            }
        } catch {
            // Fall through to generic message below.
        }
        return `HTTP ${error.status || 'error'}`;
    }

    if (typeof error === 'string') {
        return error;
    }

    if (error && typeof error === 'object') {
        const maybeMessage = (error as { message?: unknown }).message;
        if (typeof maybeMessage === 'string' && maybeMessage.trim()) {
            return maybeMessage;
        }
        try {
            return JSON.stringify(error);
        } catch {
            /* noop */
        }
    }

    try {
        return String(error);
    } catch {
        return 'Unknown error';
    }
}

export async function postRun(rawPayload: OrchestrateRunPayload): Promise<PostRunResponse> {
    const base = resolveBase();
    const body = JSON.stringify(sanitizePayload(rawPayload));
    const url = `${base}/run?commit=true`;

    let response: Response;
    try {
        response = await fetch(url, {
            method: 'POST',
            headers: jsonHeaders,
            body,
        });
    } catch (error) {
        throw new Error(await safeError(error));
    }

    if (!response.ok) {
        throw new Error(await safeError(response));
    }

    let data: any = {};
    try {
        data = await response.json();
    } catch {
        // Ignore – we'll validate below.
    }

    const jobId = data?.job_id ?? data?.jobId;
    if (!jobId || typeof jobId !== 'string') {
        throw new Error('Missing job_id in orchestrate response');
    }

    const poll = typeof data?.poll === 'string' ? data.poll : undefined;

    return {
        job_id: jobId,
        poll,
    };
}
