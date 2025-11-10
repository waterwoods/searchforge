export const TERMINAL_STATES = new Set<string>([
    'SUCCEEDED',
    'FAILED',
    'CANCELLED',
    'CANCELED',
    'ERROR',
    'TIMEOUT',
    'ABORTED',
    'COMPLETED',
]);

export type NormalizedStatus = {
    state: string;
    startedAt?: string;
    finishedAt?: string;
};

export function normalizeStatus(payload: any): NormalizedStatus {
    const raw =
        payload?.final_status ??
        payload?.status ??
        payload?.state ??
        payload?.job?.status ??
        payload?.summary?.status ??
        '';
    const state = String(raw).toUpperCase();
    const startedAt = payload?.startedAt ?? payload?.job?.startedAt ?? payload?.meta?.startedAt;
    const finishedAt = payload?.finishedAt ?? payload?.job?.finishedAt ?? payload?.meta?.finishedAt;
    return { state, startedAt, finishedAt };
}

/** Convert backend poll url → front-end proxy path, and append `detail` */
export function rewritePollPath(pollUrl: string, detail: string = 'lite'): string {
    if (!pollUrl) return '';
    let path = pollUrl.replace(/^https?:\/\/[^/]+/, ''); // strip origin
    path = path.replace(/^\/api\/experiment\b/, '/orchestrate'); // proxy to orchestrate
    const sep = path.includes('?') ? '&' : '?';
    return `${path}${detail ? `${sep}detail=${detail}` : ''}`;
}

export type PollOptions = {
    pollPath: string; // backend `poll` url or `/orchestrate/status/<id>`
    intervalMs?: number;
    detail?: 'lite' | 'full';
    onUpdate?: (info: { state: string; payload: any }) => void;
    onDone?: (state: string, payload: any) => void;
};

/** Simple polling loop with terminal detection and stop() */
export function startPolling(opts: PollOptions) {
    const { pollPath, intervalMs = 5000, detail = 'lite', onUpdate, onDone } = opts;
    let stopped = false;
    let timer: any = null;

    const tick = async () => {
        try {
            const path = rewritePollPath(pollPath, detail);
            const res = await fetch(path);
            const json = await res.json();
            const { state } = normalizeStatus(json);

            onUpdate?.({ state, payload: json });

            if (TERMINAL_STATES.has(state)) {
                stopped = true;
                if (timer) clearTimeout(timer);
                onDone?.(state, json);
                return;
            }

            if (!stopped) timer = setTimeout(tick, intervalMs);
        } catch (e) {
            // Fail-safe: stop on error and surface ERROR as terminal
            stopped = true;
            if (timer) clearTimeout(timer);
            onDone?.('ERROR', { error: String(e) });
        }
    };

    void tick();

    return {
        stop() {
            stopped = true;
            if (timer) clearTimeout(timer);
        },
    };
}
