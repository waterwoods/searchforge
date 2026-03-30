/**
 * Role C Plus — lightweight snapshots, end-of-run summary, bounded heuristics (frontend only).
 * Aligns with Truth → Intent → Reply: surfaces lifecycle / still-needed / intent_family for review.
 */
import type { TriageResult } from '../../api/inboxTriage';

export type AddCarTurnIntentPayload = {
    intent_family?: string;
    handoff_base_key?: string | null;
    truth_notes?: string[];
    phrase_storage_key?: string | null;
};

export type RoleCPlusTurnSnapshot = {
    turnIndex: number;
    customerLine: string;
    replySnippet: string;
    lifecycleStatus?: string;
    handoffReady?: boolean;
    stillNeededSummary: string;
    intentLabel: string;
    collectionStage?: string;
};

function clip(s: string, n: number): string {
    const t = (s || '').trim().replace(/\s+/g, ' ');
    return t.length <= n ? t : `${t.slice(0, n)}…`;
}

function intentCompact(tr?: TriageResult): string {
    const raw = tr?.add_car_turn_intent as AddCarTurnIntentPayload | null | undefined;
    if (!raw || typeof raw !== 'object') return '—';
    const fam = (raw.intent_family || '').trim();
    return fam || '—';
}

/** Pair customer + following system turns from replay into per-turn snapshots. */
export function buildRoleCPlusSnapshots(
    turns: Array<{ role: 'customer' | 'system'; content: string; triageResult?: TriageResult }>,
): RoleCPlusTurnSnapshot[] {
    const out: RoleCPlusTurnSnapshot[] = [];
    let customerIdx = 0;
    for (let i = 0; i < turns.length; i++) {
        const t = turns[i];
        if (t.role !== 'customer') continue;
        customerIdx += 1;
        const sys = turns[i + 1];
        const tr = sys?.role === 'system' ? sys.triageResult : undefined;
        const needed = tr?.still_needed_fields;
        const stillNeededSummary =
            needed && needed.length > 0
                ? needed.slice(0, 8).join(', ') + (needed.length > 8 ? '…' : '')
                : '—';
        out.push({
            turnIndex: customerIdx,
            customerLine: clip(t.content, 140),
            replySnippet: clip(tr?.client_reply_draft ?? '—', 180),
            lifecycleStatus: tr?.lifecycle_status,
            handoffReady: tr?.handoff_ready,
            stillNeededSummary,
            intentLabel: intentCompact(tr),
            collectionStage: tr?.collection_stage,
        });
    }
    return out;
}

function normStem(reply: string): string {
    return clip(reply, 72).toLowerCase();
}

/** Bounded warning lines (heuristic, not oracle). */
export function computeRoleCPlusWarnings(
    snapshots: RoleCPlusTurnSnapshot[],
    lastTriage?: TriageResult,
): string[] {
    const warnings: string[] = [];
    const stems = snapshots.map((s) => normStem(s.replySnippet));
    for (let i = 2; i < stems.length; i++) {
        if (stems[i] && stems[i] === stems[i - 1] && stems[i] === stems[i - 2]) {
            warnings.push('助理回复连续多轮开头高度相似 — 可能存在模板重复。');
            break;
        }
    }
    const intents = snapshots.map((s) => s.intentLabel);
    for (let i = 2; i < intents.length; i++) {
        if (
            intents[i] !== '—' &&
            intents[i] === intents[i - 1] &&
            intents[i] === intents[i - 2]
        ) {
            warnings.push('intent_family 连续多轮相同 — 关注意图层是否滞留。');
            break;
        }
    }
    const late = snapshots.filter((s) => s.turnIndex >= 4);
    if (late.length >= 2 && late.every((s) => s.intentLabel === '—')) {
        warnings.push('后半程多轮未见 add_car_turn_intent — 回归观测会偏弱（可能为后端/路径原因）。');
    }
    if (snapshots.some((s) => s.handoffReady === true && s.stillNeededSummary !== '—')) {
        warnings.push('某轮 handoff_ready 与仍缺字段同时出现 — 建议核对真相层一致性。');
    }
    if (
        lastTriage &&
        Boolean((lastTriage.formal_submitted_at || '').trim()) &&
        lastTriage.lifecycle_status === 'collecting'
    ) {
        warnings.push('已有 formal_submitted_at 但 lifecycle 仍为 collecting — 值得复核。');
    }
    return warnings.slice(0, 4);
}

export type RoleCPlusEndSummary = {
    totalTurns: number;
    finalLifecycle?: string;
    finalHandoffReady?: boolean;
    formalSubmittedAt?: string;
    overallRead: string;
    warnings: string[];
};

export function buildRoleCPlusEndSummary(
    snapshots: RoleCPlusTurnSnapshot[],
    lastTriage?: TriageResult,
): RoleCPlusEndSummary {
    const warnings = computeRoleCPlusWarnings(snapshots, lastTriage);
    const formalSubmittedAt = (lastTriage?.formal_submitted_at || '').trim() || undefined;
    let overallRead = '';
    if (!snapshots.length) {
        overallRead = '尚未产生客户轮次。';
    } else {
        const last = snapshots[snapshots.length - 1];
        overallRead = `共 ${snapshots.length} 轮客户发言；末轮生命周期 ${last.lifecycleStatus ?? '—'}，handoff_ready=${String(last.handoffReady ?? '—')}。`;
        if (formalSubmittedAt) {
            overallRead += ' 已出现正式提交时间戳（办公室可见写入）。';
        } else {
            overallRead += ' 当前仿真未走 formal_submit API，通常无 formal_submitted_at。';
        }
    }
    return {
        totalTurns: snapshots.length,
        finalLifecycle: lastTriage?.lifecycle_status,
        finalHandoffReady: lastTriage?.handoff_ready,
        formalSubmittedAt,
        overallRead,
        warnings,
    };
}
