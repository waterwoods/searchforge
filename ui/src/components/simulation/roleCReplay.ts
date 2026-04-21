/**
 * Role C — bounded controlled-LLM Add-Car customer (simulation tab).
 * Knobs: persona, difficulty, maxTurns (+ optional customNote). Keep in sync with
 * `services/fiqa_api/inbox_triage/role_c_simulation_service.py` / `role_c_customer_llm.py`.
 * Customer lines: POST /api/inbox/simulation-role-c-customer; triage: real POST /api/inbox/triage.
 */
import type { AddCarReplayScenario } from './addCarReplayTypes';

export const ROLE_C_SCENARIO_ID = 'ADD_CAR_C';

/** Distinct list id for Role C Plus (one-click multi-turn); same backend stack as Role C. */
export const ROLE_C_PLUS_SCENARIO_ID = 'ADD_CAR_C_PLUS';

export type RoleCDifficulty = 'smooth' | 'realistic' | 'tough';

export type RoleCPersonaId =
    | 'price_sensitive'
    | 'elderly'
    | 'materials_first'
    | 'family_vehicle'
    | 'fragmented'
    | 'mixed_zh_en';

export type RoleCConfig = {
    personaId: RoleCPersonaId;
    customNote: string;
    difficulty: RoleCDifficulty;
    maxTurns: number;
    /** Role C / C+ autoplay: stop early when triage returns action_ready. */
    stopOnActionReady?: boolean;
};

export const ROLE_C_PERSONAS: Array<{ id: RoleCPersonaId; label: string; hint: string }> = [
    { id: 'price_sensitive', label: '价格敏感型', hint: '在意保费、比价' },
    { id: 'elderly', label: '老年客户型', hint: '口语、少量错别字' },
    { id: 'materials_first', label: '材料先发型', hint: '强调已发过材料' },
    { id: 'family_vehicle', label: '家庭车辆型', hint: '配偶/ household / 谁开' },
    { id: 'fragmented', label: '信息很碎型', hint: '短句、分多轮补全' },
    { id: 'mixed_zh_en', label: '中英混说型', hint: '术语英文、叙述中文' },
];

export const ROLE_C_DIFFICULTIES: Array<{ id: RoleCDifficulty; label: string; hint: string }> = [
    { id: 'smooth', label: '顺畅', hint: '约 3–4 轮上限内较配合' },
    { id: 'realistic', label: '真实', hint: '碎句、改口、追问' },
    { id: 'tough', label: '刁钻', hint: '更挑剔，仍限于加车' },
];

export const ROLE_C_MAX_TURN_OPTIONS = [
    { value: 4, label: '3–4 轮（短）' },
    { value: 6, label: '5–6 轮（中）' },
    { value: 8, label: '7–8 轮（长）' },
];

export function buildRoleCScenarioCard(config: RoleCConfig): AddCarReplayScenario {
    const meta = ROLE_C_PERSONAS.find((p) => p.id === config.personaId) ?? ROLE_C_PERSONAS[0];
    const diff = ROLE_C_DIFFICULTIES.find((d) => d.id === config.difficulty) ?? ROLE_C_DIFFICULTIES[1];
    const note = config.customNote.trim();
    const noteHint = note ? ` · 备注：${note.slice(0, 24)}${note.length > 24 ? '…' : ''}` : '';
    return {
        id: ROLE_C_SCENARIO_ID,
        role: 'C',
        title: '受控 LLM 客户（角色 C）',
        subtitle: `手动逐步 · ${meta.label} · ${diff.label} · 最多 ${config.maxTurns} 轮 · 真实 triage${noteHint}`,
        risk: '实验中',
        placeholder: false,
        turns: [],
        stopOnActionReady: config.stopOnActionReady === true,
    };
}

/** Same knobs/engine as Role C; listed separately for discoverability (lightweight one-click path). */
export function buildRoleCPlusScenarioCard(config: RoleCConfig): AddCarReplayScenario {
    const meta = ROLE_C_PERSONAS.find((p) => p.id === config.personaId) ?? ROLE_C_PERSONAS[0];
    const diff = ROLE_C_DIFFICULTIES.find((d) => d.id === config.difficulty) ?? ROLE_C_DIFFICULTIES[1];
    const note = config.customNote.trim();
    const noteHint = note ? ` · 备注：${note.slice(0, 24)}${note.length > 24 ? '…' : ''}` : '';
    return {
        id: ROLE_C_PLUS_SCENARIO_ID,
        role: 'C+',
        title: 'Role C Plus · 一键多轮',
        subtitle: `轻量自动跑 · 与角色 C 同源 LLM + triage · ${meta.label} · ${diff.label} · 上限 ${config.maxTurns} 轮${noteHint}`,
        risk: '实验中',
        placeholder: false,
        turns: [],
        stopOnActionReady: config.stopOnActionReady === true,
    };
}

export const DEFAULT_ROLE_C_CONFIG: RoleCConfig = {
    personaId: 'price_sensitive',
    customNote: '',
    difficulty: 'realistic',
    maxTurns: 6,
    stopOnActionReady: false,
};
