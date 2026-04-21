/**
 * Normalized scenario steps for Simulation replay (text + optional scripted image).
 * Legacy JSON used `{ "text": "..." }` only; image steps add `type: "image"`.
 */
import type { InlineImagePayload } from '../../api/inboxTriage';

export type ReplayTextStep = { type?: 'text'; text: string };

export type ReplayImageStep = {
    type: 'image';
    /** Short label in UI */
    caption?: string;
    /** Sent as message text alongside OCR (may be empty if image-only) */
    text?: string;
    /** Path under `public/`, e.g. `/simulation-fixtures/vin_clue.png` */
    fixturePath?: string;
    /** For tests / tight demos without HTTP fetch */
    inlineBase64?: string;
    contentType?: string;
};

export type ReplayScenarioStep = ReplayTextStep | ReplayImageStep;

export function isReplayImageStep(s: ReplayScenarioStep): s is ReplayImageStep {
    return (s as ReplayImageStep).type === 'image';
}

/** Normalize legacy `{ text }` to explicit text step. */
export function normalizeReplaySteps(turns: ReplayScenarioStep[]): ReplayScenarioStep[] {
    return (turns ?? []).map((t) => {
        if (isReplayImageStep(t)) return t;
        const text = (t as ReplayTextStep).text ?? '';
        return { type: 'text' as const, text };
    });
}

export function customerLineForStep(step: ReplayScenarioStep): string {
    if (isReplayImageStep(step)) {
        const cap = (step.caption || '').trim();
        const tx = (step.text || '').trim();
        if (tx && cap) return `${tx}\n（${cap}）`;
        if (tx) return tx;
        if (cap) return `（图片：${cap}）`;
        return '（发送了一张图片）';
    }
    return (step.text || '').trim();
}

/** Text stored on the conversation turn for API history (no binary). */
export function conversationTextForStep(step: ReplayScenarioStep): string {
    if (isReplayImageStep(step)) {
        const tx = (step.text || '').trim();
        const cap = (step.caption || '').trim();
        if (tx) return cap ? `${tx} [图片: ${cap}]` : `${tx} [图片]`;
        return cap ? `[图片: ${cap}]` : '[图片]';
    }
    return (step.text || '').trim();
}

export async function loadInlineImageForStep(step: ReplayImageStep): Promise<InlineImagePayload | null> {
    const b64 = (step.inlineBase64 || '').trim();
    if (b64) {
        return {
            base64: b64,
            contentType: (step.contentType || 'image/png').trim(),
        };
    }
    const path = (step.fixturePath || '').trim();
    if (!path) return null;
    const res = await fetch(path);
    if (!res.ok) return null;
    const buf = await res.arrayBuffer();
    const bytes = new Uint8Array(buf);
    let binary = '';
    for (let i = 0; i < bytes.length; i += 1) {
        binary += String.fromCharCode(bytes[i]!);
    }
    const base64 = btoa(binary);
    const ct =
        (step.contentType || '').trim() ||
        res.headers.get('content-type')?.split(';')[0]?.trim() ||
        'image/png';
    return { base64, contentType: ct };
}
