/**
 * Role D — bounded configurable Add-Car customer replay (not free-form LLM).
 * Turns are deterministic from template + difficulty + optional one-line note.
 * The one-line note also drives **branch families** (keyword → later-turn overlays), bounded and repeatable.
 */
import type { AddCarReplayScenario } from './addCarReplayTypes';

export type RoleDDifficulty = 'smooth' | 'realistic' | 'tough';

export type RoleDTemplateId =
    | 'price_sensitive'
    | 'materials_first'
    | 'fragmented'
    | 'family_vehicle'
    | 'flip_flop'
    | 'mixed_zh_en'
    | 'elderly';

export type RoleDConfig = {
    templateId: RoleDTemplateId;
    customNote: string;
    difficulty: RoleDDifficulty;
};

/** Keyword-detected branch families; used only to layer bounded text onto later turns. */
export type RoleDBranchFamily =
    | 'price_sensitive'
    | 'typo_correction'
    | 'materials_sent'
    | 'household_vehicle'
    | 'fragmented_style'
    | 'mixed_zh_en_style'
    | 'coverage_concern';

export const ROLE_D_SCENARIO_ID = 'ADD_CAR_D';

export const ROLE_D_TEMPLATES: Array<{ id: RoleDTemplateId; label: string; hint: string }> = [
    { id: 'price_sensitive', label: '价格敏感型', hint: '在意保费、coverage 取舍' },
    { id: 'materials_first', label: '材料先发型', hint: '强调已发过材料、追问是否收到' },
    { id: 'fragmented', label: '信息很碎型', hint: '一句话只带一点信息' },
    { id: 'family_vehicle', label: '家庭车辆型', hint: '配偶/第二台车、谁开' },
    { id: 'flip_flop', label: '容易改口型', hint: '年份或日期说错再纠正' },
    { id: 'mixed_zh_en', label: '中英混说型', hint: '术语英文、叙述中文' },
    { id: 'elderly', label: '老年客户型', hint: '口语、少量错别字' },
];

export const ROLE_D_DIFFICULTIES: Array<{ id: RoleDDifficulty; label: string; turnsHint: string }> = [
    { id: 'smooth', label: '顺畅', turnsHint: '约 3 轮' },
    { id: 'realistic', label: '真实', turnsHint: '约 5 轮，含碎句或一次纠正' },
    { id: 'tough', label: '刁钻', turnsHint: '约 7–8 轮，纠偏+家庭/材料/价格压力' },
];

const BRANCH_LABEL_ZH: Record<RoleDBranchFamily, string> = {
    price_sensitive: '价格/比价',
    typo_correction: '纠错/笔误',
    materials_sent: '材料已发',
    household_vehicle: '家庭/配偶车',
    fragmented_style: '碎片化表达',
    mixed_zh_en_style: '中英混说',
    coverage_concern: '险种顾虑',
};

/** Priority order: earlier = wins a dedicated later turn slot first (max layers capped). */
const BRANCH_PRIORITY: RoleDBranchFamily[] = [
    'materials_sent',
    'household_vehicle',
    'price_sensitive',
    'coverage_concern',
    'typo_correction',
    'mixed_zh_en_style',
    'fragmented_style',
];

const MAX_BRANCH_LAYERS = 4;

const FAMILY_RULES: Array<{ id: RoleDBranchFamily; patterns: RegExp[] }> = [
    {
        id: 'price_sensitive',
        patterns: [
            /便宜/i,
            /太贵/i,
            /价格敏感/i,
            /price\s*sensitive/i,
            /premium/i,
            /保费/i,
            /deductible/i,
            /省钱/i,
            /压价/i,
            /比价/i,
            /compare/i,
            /reshop/i,
            /别家/i,
        ],
    },
    {
        id: 'typo_correction',
        patterns: [/错字/i, /typo/i, /打成/i, /记错/i, /笔误/i, /纠正/i, /打错/i, /老记/i, /容易错/i, /改口/i, /说错/i, /看错了/i],
    },
    {
        id: 'materials_sent',
        patterns: [/微信/i, /材料/i, /发过/i, /已发/i, /dec/i, /declaration/i, /扫描/i, /照片发过/i, /上传过/i],
    },
    {
        id: 'household_vehicle',
        patterns: [/配偶/i, /太太/i, /老公/i, /老婆/i, /家庭/i, /household/i, /spouse/i, /第二驾驶/i, /另一台车/i, /两台车/i, /家里还有/i],
    },
    {
        id: 'fragmented_style',
        patterns: [/碎片/i, /很碎/i, /分几次/i, /慢慢说/i, /一条条/i, /一次一点/i, /分多轮/i, /fragmented/i],
    },
    {
        id: 'mixed_zh_en_style',
        patterns: [/中英/i, /英文混/i, /mixed/i, /夹英文/i, /zh\s*en/i, /english/i],
    },
    {
        id: 'coverage_concern',
        patterns: [/coverage/i, /全险/i, /liability/i, /保额/i, /collision/i, /comprehensive/i, /险种/i],
    },
];

const SUFFIXES: Record<RoleDBranchFamily, string[]> = {
    price_sensitive: [
        '对了，保费要是能再压一点最好。',
        '太贵我就先 compare 几家再定。',
        'deductible 高一点也行，主要想控 premium。',
    ],
    typo_correction: [
        '我说的以最后一次为准，怕我又打错。',
        '年份我怕又说快/说慢，你们以我行合同为准。',
    ],
    materials_sent: [
        '材料我微信里其实发过一版了，你们看到吗？',
        'dec page / 驾照我上周传过，不想再重复一遍。',
    ],
    household_vehicle: [
        '这台主要家里另一位开，我偶尔也开。',
        '家里还有一台旧车也在你们这，今天先加这台。',
    ],
    fragmented_style: [
        '我一句句补，别急。',
        '先这么多，下一句我再讲别的。',
    ],
    mixed_zh_en_style: [
        'BTW, ZIP and pickup date are above — OK?',
        'If anything unclear, please reply in simple English too.',
    ],
    coverage_concern: [
        '我比较担心 collision / comprehensive 这块别留坑。',
        'liability 想略高一点，别的可以 standard。',
    ],
};

function djb2(s: string): number {
    let h = 5381;
    for (let i = 0; i < s.length; i++) {
        h = (h * 33) ^ s.charCodeAt(i);
    }
    return Math.abs(h);
}

/** Exposed for UI / tests: which branch tags apply to this note. */
export function detectRoleDBranchFamilies(note: string): RoleDBranchFamily[] {
    const t = note.trim();
    if (!t) return [];
    const seen = new Set<RoleDBranchFamily>();
    for (const { id, patterns } of FAMILY_RULES) {
        if (patterns.some((re) => re.test(t))) {
            seen.add(id);
        }
    }
    return BRANCH_PRIORITY.filter((id) => seen.has(id));
}

function pickSuffix(family: RoleDBranchFamily, salt: number): string {
    const arr = SUFFIXES[family];
    return arr[salt % arr.length] ?? arr[0];
}

/** Returns slot index 1..turnCount-1 per family, unique where possible. */
function assignBranchSlots(
    families: RoleDBranchFamily[],
    turnCount: number,
    seed: number,
): Map<RoleDBranchFamily, number> {
    const map = new Map<RoleDBranchFamily, number>();
    if (turnCount <= 1 || families.length === 0) return map;

    const available = new Set<number>();
    for (let i = 1; i < turnCount; i++) available.add(i);

    families.forEach((family, fi) => {
        const span = turnCount - 1;
        const hint = 1 + ((seed + fi * 37) % span);
        let slot = hint;
        if (!available.has(slot)) {
            const sorted = [...available].sort((a, b) => a - b);
            slot = sorted[0] ?? hint;
        }
        if (available.has(slot)) {
            map.set(family, slot);
            available.delete(slot);
        } else if (available.size > 0) {
            const sorted = [...available].sort((a, b) => a - b);
            const s = sorted[0]!;
            map.set(family, s);
            available.delete(s);
        }
    });
    return map;
}

function looksLikeSuffixPresent(turn: string, suffix: string): boolean {
    const probe = suffix.slice(0, 6).trim();
    if (probe.length < 2) return false;
    return turn.includes(probe);
}

/**
 * Apply at most MAX_BRANCH_LAYERS branch overlays on indices >= 1 (never changes turn count).
 */
function applyLaterTurnBranches(
    base: string[],
    customNote: string,
    templateId: RoleDTemplateId,
    difficulty: RoleDDifficulty,
): string[] {
    const familiesAll = detectRoleDBranchFamilies(customNote);
    if (familiesAll.length === 0) return base;

    const families = familiesAll.slice(0, MAX_BRANCH_LAYERS);
    const seed = djb2(`${customNote}|${templateId}|${difficulty}|${base.join('‖')}`);
    const slots = assignBranchSlots(families, base.length, seed);
    const out = [...base];

    for (const family of families) {
        const slot = slots.get(family);
        if (slot === undefined || slot < 1 || slot >= out.length) continue;
        const suffix = pickSuffix(family, seed ^ slot * 13);
        const cur = out[slot];
        if (looksLikeSuffixPresent(cur, suffix)) continue;
        out[slot] = `${cur} ${suffix}`.trim();
    }
    return out;
}

function withCustomNote(firstTurn: string, customNote: string): string {
    const n = customNote.trim();
    if (!n) return firstTurn;
    return `${firstTurn} 对了，${n}`;
}

/** Per-template, per-difficulty fixed scripts — bounded, Add-Car only. */
const TURNS: Record<RoleDTemplateId, Record<RoleDDifficulty, string[]>> = {
    price_sensitive: {
        smooth: [
            '我想加一台新车报价，coverage 不想买太贵的那种。',
            '2024 本田 CR-V，邮编 92604，这周六提车。',
            '主驾是我本人，这些够你们先出 quote 吗？',
        ],
        realistic: [
            '加新车，尽量便宜点，full coverage 太贵就算了。',
            '车型本田 CR-V，年份我打成 2023 了不好意思，是 2024。',
            '邮编 92604。',
            '提车这周六下午。',
            '驾照我手机里有照片，先发这个行吗？',
        ],
        tough: [
            'Hi 想加车，price 尽量低一点，deductible 高一点也能接受。',
            '车是 2024 Honda CR-V，刚才说成 2023 是我看错了。',
            'zip 92604。',
            'pickup 这周六，但 exact time 我还不确定。',
            '主驾就我，我老婆偶尔也开一下要不要写？',
            'registration 照片我还没拍，VIN 晚上回家发你可以吗？',
            '对了，你们收到我上周微信发的 DL 了吗？我怕你们没看到。',
        ],
    },
    materials_first: {
        smooth: [
            '我想给新买的车加保险，材料我这边可以先发。',
            '2025 Toyota Camry，邮编 91030，下周三提车。',
            '驾照复印件我待会就发微信，你们还需要别的吗？',
        ],
        realistic: [
            '加新车保险。declaration page 和驾照我上周已经在微信发过了。',
            '车是 2025 Camry，邮编 91030。',
            '提车下周三。你们系统里能看到我发的材料吗？',
            'VIN 我手机里还没存，晚上拍给你。',
            '主驾是我。',
        ],
        tough: [
            '加车。我材料先发型的，dec page、驾照我都发过一遍了。',
            '2025 Toyota Camry，别搞错成 RAV4 啊。',
            'zip 91030，pickup 下周三上午。',
            '你们说还缺 VIN，我现在在外面，晚上 8 点后发行不行？',
            '我老婆是 co-owner，这个要特别声明吗？',
            '如果材料你们收到了就跟我说一声，我不想重复发。',
            '价格 side 我想先 compare 一下，你们能先 rough quote 吗？',
        ],
    },
    fragmented: {
        smooth: ['我想加车。', '2024 马自达 CX-5，90210。', '下周五提车，主驾我。'],
        realistic: ['加车报价。', '马自达。', '2024 的，CX-5。', '邮编 90210。', '下周五拿车。', '我自己开。'],
        tough: [
            '加一台。',
            'SUV。',
            'Mazda。',
            '年份… 24 年吧。',
            'CX-5。',
            '90210。',
            '提车下周五，可能下午。',
            'VIN 等我回家再找。',
        ],
    },
    family_vehicle: {
        smooth: [
            '我想给我太太新买的车加险。',
            '2023 Lexus RX，邮编 91776，下周提车。',
            '她主开，我也偶尔会开。',
        ],
        realistic: [
            '帮我给我配偶新买的车加保险。',
            '2023 Lexus RX 350，91776。',
            '下周提车，她 daily drive，我周末有时候开。',
            '驾照两个人的都要吗？',
            'VIN 在纸质文件上，我晚点拍。',
        ],
        tough: [
            '家里要加一台车，主要是我太太用。',
            'Lexus RX，2023，不是 2022 我看错了。',
            '91776。提车日期暂定下周，可能改到再下周。',
            '我太太 primary driver，我是 secondary 可以吗？',
            '另一台旧车我想以后再说 remove，今天先把这台加进去。',
            '材料有的在微信发过，有的还没扫。',
            '保费能不能先给个 range，我们好商量。',
        ],
    },
    flip_flop: {
        smooth: [
            '加新车保险。',
            '2022 Subaru Outback，91311，这周日提车。',
            '刚才日期说错了，是周日不是周六。',
        ],
        realistic: [
            '加车。',
            '2021 Outback… 不对，是 2022 Subaru Outback。',
            '91311。',
            '提车这周日，我之前说成周六了，以这个为准。',
            '主驾我。',
        ],
        tough: [
            '加 Outback。',
            '年份我先说 2021，你看下车行合同其实是 2022。',
            '91311 zip。',
            '提车：我一开始说周六，改成周日下午。',
            'VIN 尾号我记混了，等我发照片你们核对。',
            'coverage 我想 liability 高一点，别的 standard。',
            '我太太也要列在 policy 里吗？她也有驾照。',
        ],
    },
    mixed_zh_en: {
        smooth: [
            '想 add a vehicle for quote，新车。',
            '2024 Tesla Model Y，zip 94086，next Friday delivery。',
            '我是 primary driver。',
        ],
        realistic: [
            'Add car for insurance quote，麻烦走 add vehicle flow。',
            'Tesla Model Y 2024，garaging zip 94086。',
            'Delivery next Friday，VIN 我晚点 text 你们。',
            'DL 我上周 WeChat 发过了，please confirm received。',
            '想要 comprehensive 但 deductible 可以高一点。',
        ],
        tough: [
            'Need to add new car to policy，quote prep 就行。',
            'Model Y，2024，不是 2023，我刚才 typo。',
            'ZIP 94086，delivery next Fri PM。',
            'Spouse might drive occasionally — need 列成 driver 吗？',
            'Registration and dec page partial 我发过了，还差 VIN photo。',
            'Price sensitive：premium 尽量压一点。',
            '如果还缺 info 请列 list，我一次性补。',
        ],
    },
    elderly: {
        smooth: [
            '你好我想给新车办一下那个加车的保险。',
            '车子是二零二四年的丰田凯美瑞，邮编九一六零六。',
            '我自已开，下周去提车。',
        ],
        realistic: [
            '加车保险我不会弄你帮我看下。',
            '丰田凯美瑞，二四年买的，邮编 91606。',
            '车型是凯美瑞，别和家里那台雅力士搞混。',
            '提车说是下周三。',
            '手机拍照的驾照我可以发吗？',
        ],
        tough: [
            '我要加新车保险，年纪大了不太会用这个聊天。',
            '丰田凯美瑞，年份我老记成 2023，单子写的是 2024。',
            '邮编 91606，别和上次那个旧地址混了。',
            '提车时间下周三，要是车行改期我再跟你们说。',
            '我儿子有时候也开这台车，要不要写他？',
            '材料有的发微信了有的还在家里。',
            '价钱方面不要太贵，够用就行。',
        ],
    },
};

const RISK_FOR_DIFFICULTY: Record<RoleDDifficulty, string> = {
    smooth: '标准',
    realistic: '偏高',
    tough: '高风险',
};

export function buildRoleDScenario(config: RoleDConfig): AddCarReplayScenario {
    const meta = ROLE_D_TEMPLATES.find((t) => t.id === config.templateId) ?? ROLE_D_TEMPLATES[0];
    const raw = TURNS[config.templateId][config.difficulty];
    const branched = applyLaterTurnBranches(raw, config.customNote, config.templateId, config.difficulty);
    const turns = branched.map((text, i) => ({
        text: i === 0 ? withCustomNote(text, config.customNote) : text,
    }));
    const diffLabel = ROLE_D_DIFFICULTIES.find((d) => d.id === config.difficulty)?.label ?? config.difficulty;
    const branchFamilies = detectRoleDBranchFamilies(config.customNote);
    const branchHint =
        branchFamilies.length > 0
            ? ` · 自述分支：${branchFamilies.map((f) => BRANCH_LABEL_ZH[f]).join('、')}`
            : '';
    return {
        id: ROLE_D_SCENARIO_ID,
        role: 'D',
        title: `可配置客户（角色 D）· ${meta.label}`,
        subtitle: `${meta.hint} · ${diffLabel}（${ROLE_D_DIFFICULTIES.find((d) => d.id === config.difficulty)?.turnsHint ?? ''}）${branchHint}`,
        risk: RISK_FOR_DIFFICULTY[config.difficulty],
        placeholder: false,
        turns,
    };
}

export const DEFAULT_ROLE_D_CONFIG: RoleDConfig = {
    templateId: 'price_sensitive',
    customNote: '',
    difficulty: 'realistic',
};
