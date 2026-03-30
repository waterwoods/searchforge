/**
 * Add-Car Simulation / Scenario Replay — third-tab surface (§4.6 master outline).
 * Record-first: right column is primary; thread is audit trail.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Col, Input, Row, Select, Space, Spin, Tag, Typography, message } from 'antd';
import {
    PlayCircleOutlined,
    ReloadOutlined,
    RightOutlined,
    ThunderboltOutlined,
    UnorderedListOutlined,
    FastForwardOutlined,
} from '@ant-design/icons';
import {
    fetchSimulationRoleCCustomer,
    triageMessage,
    type ConversationTurn,
    type TriageResult,
} from '../../api/inboxTriage';
import { useClientConfig } from '../../context/ClientConfigContext';
import { AddCarRecordSummaryRail, computeAddCarFlowStep } from '../intake/AddCarRecordSummaryRail';
import replayConfig from '../../config/add_car_scenario_replay.json';
import type { AddCarReplayScenario } from './addCarReplayTypes';
import {
    DEFAULT_ROLE_C_CONFIG,
    ROLE_C_DIFFICULTIES,
    ROLE_C_MAX_TURN_OPTIONS,
    ROLE_C_PERSONAS,
    ROLE_C_PLUS_SCENARIO_ID,
    ROLE_C_SCENARIO_ID,
    buildRoleCPlusScenarioCard,
    buildRoleCScenarioCard,
    type RoleCConfig,
    type RoleCDifficulty,
    type RoleCPersonaId,
} from './roleCReplay';
import { buildRoleCPlusEndSummary, buildRoleCPlusSnapshots } from './roleCPlusHelpers';
import {
    DEFAULT_ROLE_D_CONFIG,
    ROLE_D_DIFFICULTIES,
    ROLE_D_SCENARIO_ID,
    ROLE_D_TEMPLATES,
    buildRoleDScenario,
    type RoleDConfig,
    type RoleDDifficulty,
    type RoleDTemplateId,
} from './roleDReplay';

const { Text, Title, Paragraph } = Typography;
const { TextArea } = Input;

export type { AddCarReplayScenario } from './addCarReplayTypes';

type ReplayTurn = {
    role: 'customer' | 'system';
    content: string;
    triageResult?: TriageResult;
};

export function ScenarioReplayTab() {
    const { clientId, uiCopy } = useClientConfig();
    const [roleCConfig, setRoleCConfig] = useState<RoleCConfig>(DEFAULT_ROLE_C_CONFIG);
    const roleCScenarioCard = useMemo(() => buildRoleCScenarioCard(roleCConfig), [roleCConfig]);
    const roleCPlusScenarioCard = useMemo(() => buildRoleCPlusScenarioCard(roleCConfig), [roleCConfig]);
    const [roleDConfig, setRoleDConfig] = useState<RoleDConfig>(DEFAULT_ROLE_D_CONFIG);
    const roleDScenario = useMemo(() => buildRoleDScenario(roleDConfig), [roleDConfig]);
    const scenarios = useMemo(() => {
        const base = (replayConfig as { scenarios: AddCarReplayScenario[] }).scenarios.filter(
            (s) =>
                s.id !== ROLE_D_SCENARIO_ID &&
                s.id !== ROLE_C_SCENARIO_ID &&
                s.id !== ROLE_C_PLUS_SCENARIO_ID,
        );
        return [...base, roleCScenarioCard, roleCPlusScenarioCard, roleDScenario];
    }, [roleCScenarioCard, roleCPlusScenarioCard, roleDScenario]);
    const [selected, setSelected] = useState<AddCarReplayScenario | null>(null);
    const [replayTurns, setReplayTurns] = useState<ReplayTurn[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const base = (replayConfig as { scenarios: AddCarReplayScenario[] }).scenarios.filter(
            (s) =>
                s.id !== ROLE_D_SCENARIO_ID &&
                s.id !== ROLE_C_SCENARIO_ID &&
                s.id !== ROLE_C_PLUS_SCENARIO_ID,
        );
        setSelected((prev) => {
            if (prev?.id === ROLE_D_SCENARIO_ID) return roleDScenario;
            if (prev?.id === ROLE_C_SCENARIO_ID) return roleCScenarioCard;
            if (prev?.id === ROLE_C_PLUS_SCENARIO_ID) return roleCPlusScenarioCard;
            if (prev && base.some((s) => s.id === prev.id)) return prev;
            return base[0] ?? roleCScenarioCard;
        });
    }, [roleDScenario, roleCScenarioCard, roleCPlusScenarioCard]);

    useEffect(() => {
        if (selected?.id !== ROLE_D_SCENARIO_ID) return;
        setReplayTurns([]);
        setLoading(false);
    }, [roleDConfig, selected?.id]);

    useEffect(() => {
        if (selected?.id !== ROLE_C_SCENARIO_ID && selected?.id !== ROLE_C_PLUS_SCENARIO_ID) return;
        setReplayTurns([]);
        setLoading(false);
    }, [roleCConfig, selected?.id]);

    const customerCount = replayTurns.filter((t) => t.role === 'customer').length;
    const lastSystem = [...replayTurns].reverse().find((t) => t.role === 'system');
    const lastTriage = lastSystem?.triageResult;
    const isRoleCLane =
        selected?.id === ROLE_C_SCENARIO_ID || selected?.id === ROLE_C_PLUS_SCENARIO_ID;
    const isRoleCManual = selected?.id === ROLE_C_SCENARIO_ID;
    const isRoleCPlusSelected = selected?.id === ROLE_C_PLUS_SCENARIO_ID;
    const hasMore = selected
        ? isRoleCLane
            ? customerCount < roleCConfig.maxTurns
            : customerCount < selected.turns.length
        : false;
    const flowStep = computeAddCarFlowStep(lastTriage, replayTurns.length > 0);
    const priorReplayTriage = useMemo(() => {
        const sys = replayTurns.filter((t) => t.role === 'system' && t.triageResult);
        return sys.length >= 2 ? sys[sys.length - 2].triageResult : undefined;
    }, [replayTurns]);

    const roleCPlusSnapshots = useMemo(() => {
        if (!isRoleCLane) return [];
        return buildRoleCPlusSnapshots(replayTurns);
    }, [isRoleCLane, replayTurns]);

    const roleCPlusEnd = useMemo(() => {
        if (!isRoleCLane) return null;
        return buildRoleCPlusEndSummary(roleCPlusSnapshots, lastTriage);
    }, [isRoleCLane, roleCPlusSnapshots, lastTriage]);

    /** Bounded auto-run: same live Role C + triage stack as manual 「下一步」, turn-by-turn. */
    const runRoleCFullSimulation = useCallback(async () => {
        if (
            !selected ||
            (selected.id !== ROLE_C_SCENARIO_ID && selected.id !== ROLE_C_PLUS_SCENARIO_ID) ||
            loading
        )
            return;
        setLoading(true);
        setReplayTurns([]);
        let prior: ReplayTurn[] = [];
        try {
            for (let n = 0; n < roleCConfig.maxTurns; n++) {
                const custDone = prior.filter((t) => t.role === 'customer').length;
                if (custDone >= roleCConfig.maxTurns) break;

                const conversationTurnsForApi: ConversationTurn[] = prior.map((t) => ({
                    role: t.role,
                    text: t.content,
                }));

                const llm = await fetchSimulationRoleCCustomer({
                    persona_id: roleCConfig.personaId,
                    optional_note: roleCConfig.customNote,
                    difficulty: roleCConfig.difficulty,
                    max_turns: roleCConfig.maxTurns,
                    conversation_turns: conversationTurnsForApi,
                    client_id: clientId,
                });
                const text = (llm.customer_message || '').trim();
                if (!text) {
                    message.error('角色 C 未返回有效客户话术');
                    break;
                }
                const customerTurn: ReplayTurn = { role: 'customer', content: text };
                setReplayTurns([...prior, customerTurn]);
                const data = await triageMessage(
                    text,
                    false,
                    conversationTurnsForApi,
                    'add_car',
                    undefined,
                    clientId,
                );
                const systemTurn: ReplayTurn = {
                    role: 'system',
                    content: data.client_reply_draft,
                    triageResult: data,
                };
                prior = [...prior, customerTurn, systemTurn];
                setReplayTurns(prior);
                await new Promise((r) => setTimeout(r, 72));
            }
            if (prior.length > 0) {
                message.success('Role C Plus：已按轮次上限跑完（或提前结束）');
            }
        } catch (e: unknown) {
            setReplayTurns(prior);
            const msg =
                (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ??
                (e as { message?: string })?.message ??
                'Role C Plus 自动跑失败，请确认后端可用。';
            message.error(typeof msg === 'string' ? msg : 'Role C Plus 自动跑失败');
        } finally {
            setLoading(false);
        }
    }, [selected, loading, clientId, roleCConfig]);

    /** `priorReplay` = turns before this customer message (avoids stale closure after reset). */
    const runNextTurn = useCallback(
        async (priorReplay: ReplayTurn[]) => {
            if (!selected || loading) return;
            const custDone = priorReplay.filter((t) => t.role === 'customer').length;

            const conversationTurnsForApi: ConversationTurn[] = priorReplay.map((t) => ({
                role: t.role,
                text: t.content,
            }));

            if (selected.id === ROLE_C_SCENARIO_ID || selected.id === ROLE_C_PLUS_SCENARIO_ID) {
                if (custDone >= roleCConfig.maxTurns) return;

                setLoading(true);
                try {
                    const llm = await fetchSimulationRoleCCustomer({
                        persona_id: roleCConfig.personaId,
                        optional_note: roleCConfig.customNote,
                        difficulty: roleCConfig.difficulty,
                        max_turns: roleCConfig.maxTurns,
                        conversation_turns: conversationTurnsForApi,
                        client_id: clientId,
                    });
                    const text = (llm.customer_message || '').trim();
                    if (!text) {
                        message.error('角色 C 未返回有效客户话术');
                        return;
                    }
                    const customerTurn: ReplayTurn = { role: 'customer', content: text };
                    setReplayTurns([...priorReplay, customerTurn]);
                    const data = await triageMessage(text, false, conversationTurnsForApi, 'add_car', undefined, clientId);
                    const systemTurn: ReplayTurn = {
                        role: 'system',
                        content: data.client_reply_draft,
                        triageResult: data,
                    };
                    setReplayTurns([...priorReplay, customerTurn, systemTurn]);
                } catch (e: unknown) {
                    setReplayTurns(priorReplay);
                    const msg =
                        (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ??
                        (e as { message?: string })?.message ??
                        '角色 C 请求失败，请确认后端可用且已配置 OPENAI_API_KEY。';
                    message.error(typeof msg === 'string' ? msg : '角色 C 请求失败');
                } finally {
                    setLoading(false);
                }
                return;
            }

            if (custDone >= selected.turns.length) return;

            const text = selected.turns[custDone]?.text?.trim();
            if (!text) return;

            setLoading(true);
            const customerTurn: ReplayTurn = { role: 'customer', content: text };
            setReplayTurns([...priorReplay, customerTurn]);

            try {
                const data = await triageMessage(text, false, conversationTurnsForApi, 'add_car', undefined, clientId);
                const systemTurn: ReplayTurn = {
                    role: 'system',
                    content: data.client_reply_draft,
                    triageResult: data,
                };
                setReplayTurns([...priorReplay, customerTurn, systemTurn]);
            } catch (e: unknown) {
                setReplayTurns(priorReplay);
                const errMsg =
                    (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail ??
                    (e as { message?: string })?.message ??
                    '仿真请求失败，请确认后端可用。';
                message.error(errMsg);
            } finally {
                setLoading(false);
            }
        },
        [selected, loading, clientId, roleCConfig],
    );

    const handleReset = () => {
        setReplayTurns([]);
        setLoading(false);
    };

    const panelTitle = uiCopy.simulation_state_panel_title ?? '服务记录与进度（主视图）';
    const threadHint = uiCopy.simulation_thread_hint ?? '对话为过程留痕；理解与验收以右栏状态为准。';

    const roleCSharedKnobs = (
        <Space direction="vertical" size={10} style={{ width: '100%' }}>
            <div style={{ width: '100%' }}>
                <Text style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 4, fontWeight: 600 }}>
                    人设
                </Text>
                <Select<RoleCPersonaId>
                    style={{ width: '100%' }}
                    value={roleCConfig.personaId}
                    onChange={(personaId) => setRoleCConfig((c) => ({ ...c, personaId }))}
                    options={ROLE_C_PERSONAS.map((p) => ({
                        value: p.id,
                        label: `${p.label} — ${p.hint}`,
                    }))}
                />
            </div>
            <div style={{ width: '100%' }}>
                <Text style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 4, fontWeight: 600 }}>
                    可选一句话备注（注入 LLM 上下文，非自由聊天）
                </Text>
                <TextArea
                    value={roleCConfig.customNote}
                    onChange={(e) => setRoleCConfig((c) => ({ ...c, customNote: e.target.value }))}
                    placeholder="例：家里两台车、材料微信发过、想先 rough quote…"
                    maxLength={160}
                    showCount
                    autoSize={{ minRows: 2, maxRows: 3 }}
                />
            </div>
            <div style={{ width: '100%' }}>
                <Text style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 4, fontWeight: 600 }}>
                    真实度 / 难度
                </Text>
                <Select<RoleCDifficulty>
                    style={{ width: '100%' }}
                    value={roleCConfig.difficulty}
                    onChange={(difficulty) => setRoleCConfig((c) => ({ ...c, difficulty }))}
                    options={ROLE_C_DIFFICULTIES.map((d) => ({
                        value: d.id,
                        label: `${d.label}（${d.hint}）`,
                    }))}
                />
            </div>
            <div style={{ width: '100%' }}>
                <Text style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 4, fontWeight: 600 }}>
                    客户发言轮次上限
                </Text>
                <Select<number>
                    style={{ width: '100%' }}
                    value={roleCConfig.maxTurns}
                    onChange={(maxTurns) => setRoleCConfig((c) => ({ ...c, maxTurns }))}
                    options={ROLE_C_MAX_TURN_OPTIONS.map((o) => ({
                        value: o.value,
                        label: o.label,
                    }))}
                />
            </div>
            <Text style={{ fontSize: 12, color: '#595959', lineHeight: 1.55 }}>
                每步由后端 LLM 生成客户话，再走真实 triage；有轮次上限，非无限对话。需后端 OPENAI_API_KEY。
            </Text>
        </Space>
    );

    return (
        <div style={{ width: '100%', padding: '0 0 28px', boxSizing: 'border-box' }}>
            <Card
                size="small"
                style={{
                    marginBottom: 16,
                    borderRadius: 10,
                    border: '1px solid #d9d9d9',
                    background: '#f5f5f5',
                }}
            >
                <Space align="start" size={14}>
                    <ThunderboltOutlined style={{ fontSize: 24, color: '#1677ff', marginTop: 2 }} />
                    <div style={{ minWidth: 0 }}>
                        <Title level={4} style={{ margin: 0, fontSize: 18, color: '#262626', fontWeight: 700 }}>
                            {uiCopy.simulation_tab_hero_title ?? '场景仿真 · 加车旗舰路径'}
                        </Title>
                        <Paragraph
                            style={{
                                margin: '8px 0 0',
                                fontSize: 14,
                                color: '#434343',
                                marginBottom: 0,
                                lineHeight: 1.6,
                            }}
                        >
                            {uiCopy.simulation_tab_hero_body ??
                                '命名场景、固定脚本、多轮回放；与真实受理共用状态语义。用于演示、验收与回归，不是自由聊天。'}
                        </Paragraph>
                    </div>
                </Space>
            </Card>

            <Row gutter={[16, 16]}>
                <Col xs={24} lg={6}>
                    <Card
                        size="small"
                        title={
                            <span style={{ fontSize: 15, fontWeight: 600, color: '#262626' }}>
                                <UnorderedListOutlined style={{ marginRight: 8 }} />
                                {uiCopy.simulation_scenario_list_title ?? '场景卡片'}
                            </span>
                        }
                        styles={{ body: { padding: 14 } }}
                    >
                        <Space direction="vertical" size={12} style={{ width: '100%' }}>
                            {scenarios.map((s) => {
                                const active = selected?.id === s.id;
                                return (
                                    <Card
                                        key={s.id}
                                        size="small"
                                        hoverable
                                        onClick={() => {
                                            setSelected(s);
                                            handleReset();
                                        }}
                                        style={{
                                            cursor: 'pointer',
                                            borderColor: active ? '#1677ff' : '#d9d9d9',
                                            background: active ? '#e6f4ff' : '#fff',
                                            boxShadow: active ? '0 0 0 1px rgba(22, 119, 255, 0.2)' : undefined,
                                        }}
                                    >
                                        <Space direction="vertical" size={6} style={{ width: '100%' }}>
                                            <Space wrap size={6}>
                                                <Tag color="geekblue">角色 {s.role}</Tag>
                                                <Tag
                                                    color={
                                                        s.risk === '高风险' ? 'red' : s.risk === '实验中' ? 'purple' : 'blue'
                                                    }
                                                >
                                                    {s.risk}
                                                </Tag>
                                            </Space>
                                            <Text strong style={{ fontSize: 14, color: '#262626', lineHeight: 1.4 }}>
                                                {s.title}
                                            </Text>
                                            <Text style={{ fontSize: 13, color: '#434343', lineHeight: 1.55 }}>
                                                {s.subtitle}
                                            </Text>
                                            <Text style={{ fontSize: 12, color: '#595959' }}>
                                                {s.id === ROLE_C_SCENARIO_ID || s.id === ROLE_C_PLUS_SCENARIO_ID
                                                    ? `最多 ${roleCConfig.maxTurns} 轮 · 受控 LLM`
                                                    : `${s.turns.length} 轮客户发言`}
                                            </Text>
                                        </Space>
                                    </Card>
                                );
                            })}
                            {isRoleCManual && (
                                <div
                                    style={{
                                        marginTop: 2,
                                        padding: 12,
                                        borderRadius: 8,
                                        border: '1px solid #d3adf7',
                                        background: '#faf5ff',
                                    }}
                                >
                                    <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 8, color: '#391085' }}>
                                        角色 C · 手动逐步（受控 LLM）
                                    </Text>
                                    <Text style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 10, lineHeight: 1.55 }}>
                                        用人设、难度、轮次上限驱动客户话；每轮点中部「下一步」。与后端 Role C 及{' '}
                                        <code style={{ fontSize: 11 }}>scripts/run_role_c_add_car_battery.py</code>{' '}
                                        同源。需要一键自动跑完请选上方「Role C Plus」卡片。
                                    </Text>
                                    {roleCSharedKnobs}
                                </div>
                            )}
                            {isRoleCPlusSelected && (
                                <div
                                    style={{
                                        marginTop: 2,
                                        padding: 12,
                                        borderRadius: 8,
                                        border: '1px solid #b37feb',
                                        background: '#f9f0ff',
                                    }}
                                >
                                    <Text strong style={{ fontSize: 13, display: 'block', marginBottom: 6, color: '#391085' }}>
                                        Role C Plus · 一键多轮（轻量自动跑）
                                    </Text>
                                    <Text style={{ fontSize: 12, color: '#434343', display: 'block', marginBottom: 12, lineHeight: 1.55 }}>
                                        与角色 C 相同接口与旋钮；点下面主按钮将按轮次上限连续跑完。下方区域展示逐轮快照与结束小报告（启发式）。
                                    </Text>
                                    <Button
                                        type="primary"
                                        size="middle"
                                        icon={<FastForwardOutlined />}
                                        loading={loading}
                                        disabled={loading}
                                        onClick={() => void runRoleCFullSimulation()}
                                        block
                                        style={{ marginBottom: 14, fontWeight: 600 }}
                                    >
                                        一键跑完（最多 {roleCConfig.maxTurns} 轮）
                                    </Button>
                                    <Text
                                        style={{
                                            fontSize: 12,
                                            color: '#434343',
                                            display: 'block',
                                            marginBottom: 8,
                                            fontWeight: 600,
                                        }}
                                    >
                                        旋钮（与角色 C 同步）
                                    </Text>
                                    {roleCSharedKnobs}
                                </div>
                            )}
                            {selected?.id === ROLE_D_SCENARIO_ID && (
                                <div
                                    style={{
                                        marginTop: 4,
                                        padding: 10,
                                        borderRadius: 8,
                                        border: '1px solid #d6e4ff',
                                        background: '#f6ffed',
                                    }}
                                >
                                    <Text strong style={{ fontSize: 12, display: 'block', marginBottom: 8 }}>
                                        角色 D · 可配置客户（bounded，非自由聊天）
                                    </Text>
                                    <Space direction="vertical" size={8} style={{ width: '100%' }}>
                                        <div style={{ width: '100%' }}>
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                基础人设模板
                                            </Text>
                                            <Select<RoleDTemplateId>
                                                style={{ width: '100%' }}
                                                value={roleDConfig.templateId}
                                                onChange={(templateId) =>
                                                    setRoleDConfig((c) => ({ ...c, templateId }))
                                                }
                                                options={ROLE_D_TEMPLATES.map((t) => ({
                                                    value: t.id,
                                                    label: `${t.label} — ${t.hint}`,
                                                }))}
                                            />
                                        </div>
                                        <div style={{ width: '100%' }}>
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                一句话客户自述（首轮 + 关键词驱动后续轮次）
                                            </Text>
                                            <TextArea
                                                value={roleDConfig.customNote}
                                                onChange={(e) =>
                                                    setRoleDConfig((c) => ({ ...c, customNote: e.target.value }))
                                                }
                                                placeholder="例：价格敏感、材料微信发过、家里有另一台车、中英混说、coverage 担心 collision…"
                                                maxLength={160}
                                                showCount
                                                autoSize={{ minRows: 2, maxRows: 3 }}
                                            />
                                        </div>
                                        <div style={{ width: '100%' }}>
                                            <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 4 }}>
                                                真实度 / 难度
                                            </Text>
                                            <Select<RoleDDifficulty>
                                                style={{ width: '100%' }}
                                                value={roleDConfig.difficulty}
                                                onChange={(difficulty) =>
                                                    setRoleDConfig((c) => ({ ...c, difficulty }))
                                                }
                                                options={ROLE_D_DIFFICULTIES.map((d) => ({
                                                    value: d.id,
                                                    label: `${d.label}（${d.turnsHint}）`,
                                                }))}
                                            />
                                        </div>
                                        <Text type="secondary" style={{ fontSize: 11, lineHeight: 1.45 }}>
                                            修改模板、自述或难度会清空回放；自述里的关键词会在后续轮次叠加有界变体（仍走真实 triage 接口）。
                                        </Text>
                                    </Space>
                                </div>
                            )}
                        </Space>
                    </Card>
                </Col>

                <Col xs={24} lg={10}>
                    <Card
                        size="small"
                        title={
                            <span style={{ fontSize: 15, fontWeight: 600, color: '#262626' }}>
                                {uiCopy.simulation_replay_title ?? '对话回放'}
                            </span>
                        }
                        extra={
                            <Space wrap size="small">
                                <Button
                                    type="primary"
                                    size="small"
                                    icon={<PlayCircleOutlined />}
                                    loading={loading}
                                    onClick={() => {
                                        if (!selected) {
                                            message.warning('请先选择一个场景');
                                            return;
                                        }
                                        void runNextTurn([]);
                                    }}
                                    disabled={!selected || loading}
                                >
                                    {replayTurns.length === 0
                                        ? (uiCopy.simulation_start_replay ?? '开始回放')
                                        : (uiCopy.simulation_replay_again ?? '重新回放')}
                                </Button>
                                <Button
                                    size="small"
                                    icon={<RightOutlined />}
                                    loading={loading}
                                    disabled={!selected || !hasMore || loading}
                                    onClick={() => void runNextTurn(replayTurns)}
                                >
                                    {uiCopy.simulation_next_turn ?? '下一步'}
                                </Button>
                                <Button size="small" icon={<ReloadOutlined />} onClick={handleReset} disabled={loading}>
                                    {uiCopy.simulation_reset ?? '清空'}
                                </Button>
                            </Space>
                        }
                        styles={{ body: { padding: 14 } }}
                    >
                        {selected?.placeholder && selected.placeholder_note && (
                            <Alert type="info" showIcon style={{ marginBottom: 12 }} message={selected.placeholder_note} />
                        )}
                        <Text style={{ fontSize: 12, color: '#595959', display: 'block', marginBottom: 12, lineHeight: 1.55 }}>
                            {threadHint}
                        </Text>
                        <div
                            style={{
                                minHeight: 288,
                                maxHeight: 480,
                                overflowY: 'auto',
                                padding: 12,
                                background: '#f5f5f5',
                                borderRadius: 8,
                                border: '1px solid #d9d9d9',
                            }}
                        >
                            {replayTurns.length === 0 && !loading && (
                                <Text style={{ fontSize: 14, color: '#434343', lineHeight: 1.55 }}>
                                    {uiCopy.simulation_replay_empty ??
                                        '选择左侧场景后点「开始回放」或「下一步」逐轮查看。'}
                                </Text>
                            )}
                            <Space direction="vertical" size={12} style={{ width: '100%' }}>
                                {replayTurns.map((t, idx) => (
                                    <div
                                        key={idx}
                                        style={{
                                            display: 'flex',
                                            justifyContent: t.role === 'customer' ? 'flex-end' : 'flex-start',
                                        }}
                                    >
                                        <div
                                            style={{
                                                maxWidth: '92%',
                                                padding: 12,
                                                borderRadius: 8,
                                                fontSize: 14,
                                                lineHeight: 1.55,
                                                color: '#262626',
                                                background:
                                                    t.role === 'customer' ? 'rgba(24, 144, 255, 0.14)' : 'rgba(82, 196, 26, 0.12)',
                                                borderLeft: t.role === 'system' ? '3px solid #389e0d' : undefined,
                                                borderRight: t.role === 'customer' ? '3px solid #1677ff' : undefined,
                                            }}
                                        >
                                            <Text style={{ fontSize: 11, display: 'block', marginBottom: 6, color: '#595959' }}>
                                                {t.role === 'customer'
                                                    ? (uiCopy.portal_customer_bubble_label ?? '客户')
                                                    : (uiCopy.portal_office_bubble_label ?? '系统整理')}
                                            </Text>
                                            <Text style={{ whiteSpace: 'pre-wrap' }}>{t.content}</Text>
                                        </div>
                                    </div>
                                ))}
                            </Space>
                            {loading && (
                                <div style={{ textAlign: 'center', padding: 16 }}>
                                    <Spin tip={uiCopy.portal_loading_status ?? '整理中…'} />
                                </div>
                            )}
                        </div>
                    </Card>
                </Col>

                <Col xs={24} lg={8}>
                    <Card
                        size="small"
                        title={
                            <span style={{ fontSize: 15, fontWeight: 600, color: '#262626' }}>{panelTitle}</span>
                        }
                        styles={{ body: { padding: 14 } }}
                    >
                        {!lastTriage && (
                            <Text style={{ fontSize: 14, color: '#434343', lineHeight: 1.55 }}>
                                {uiCopy.simulation_state_empty ?? '回放开始后，此处同步当前步骤、状态与缺口。'}
                            </Text>
                        )}
                        {lastTriage && (
                            <Space direction="vertical" size={14} style={{ width: '100%' }}>
                                {lastTriage.case_id ? (
                                    <div>
                                        <Text style={{ fontSize: 12, color: '#595959', display: 'block', marginBottom: 4, fontWeight: 600 }}>
                                            {uiCopy.add_car_case_record_id_label ?? '服务记录编号'}
                                        </Text>
                                        <Text
                                            copyable={{ text: lastTriage.case_id }}
                                            style={{ fontFamily: 'monospace', fontSize: 13, color: '#262626' }}
                                        >
                                            {lastTriage.case_id}
                                        </Text>
                                    </div>
                                ) : (
                                    <Text style={{ fontSize: 13, color: '#595959' }}>
                                        {uiCopy.simulation_no_case_id_yet ?? '（演示未持久化时可能无编号）'}
                                    </Text>
                                )}
                                {lastTriage.collection_stage && (
                                    <div>
                                        <Text style={{ fontSize: 12, color: '#595959', display: 'block', marginBottom: 4, fontWeight: 600 }}>
                                            {uiCopy.add_car_status_strip_label ?? '当前状态'}
                                        </Text>
                                        <Tag color={lastTriage.collection_stage === 'enough_for_handoff' ? 'green' : 'default'}>
                                            {lastTriage.collection_stage === 'enough_for_handoff' ? '可交办公室' : '信息收集中'}
                                        </Tag>
                                    </div>
                                )}
                                <div>
                                    <Text style={{ fontSize: 12, color: '#595959', display: 'block', marginBottom: 6, fontWeight: 600 }}>
                                        {uiCopy.simulation_next_action_title ?? '下一步（办公室侧整理）'}
                                    </Text>
                                    <Text style={{ fontSize: 14, lineHeight: 1.6, color: '#262626' }}>
                                        {(lastTriage.broker_next_step ?? '').trim() || '—'}
                                    </Text>
                                </div>
                                <AddCarRecordSummaryRail
                                    triage={lastTriage}
                                    priorSystemTriage={priorReplayTriage}
                                    uiCopy={uiCopy}
                                    mode="simulation"
                                    flowStep={flowStep}
                                    submitLabel={uiCopy.portal_submit_followup ?? '提交补充'}
                                />
                            </Space>
                        )}
                    </Card>
                </Col>
            </Row>

            {isRoleCLane && (
                <Row gutter={[16, 16]} style={{ marginTop: 12 }}>
                    <Col xs={24}>
                        <Card
                            size="small"
                            title={
                                <span style={{ fontSize: 15, fontWeight: 600, color: '#262626' }}>
                                    <FastForwardOutlined style={{ marginRight: 8, color: '#722ed1' }} />
                                    Role C / C Plus · 逐轮快照与结束报告
                                </span>
                            }
                            styles={{ body: { padding: 14 } }}
                            style={{ borderColor: '#d3adf7', background: '#fcfbff' }}
                        >
                            {roleCPlusSnapshots.length === 0 ? (
                                <Text style={{ fontSize: 13, color: '#434343', lineHeight: 1.6 }}>
                                    在「角色 C」用「下一步」逐轮跑，或在「Role C Plus」点「一键跑完」后，此处汇总每轮 lifecycle、handoff、仍缺字段与
                                    add_car_turn_intent（只读快照，非完整 JSON）。
                                </Text>
                            ) : (
                                <Space direction="vertical" size={14} style={{ width: '100%' }}>
                                    {roleCPlusSnapshots.map((s) => (
                                        <div
                                            key={s.turnIndex}
                                            style={{
                                                border: '1px solid #d9d9d9',
                                                borderRadius: 8,
                                                padding: 12,
                                                background: '#fff',
                                            }}
                                        >
                                            <Space wrap size={[6, 4]}>
                                                <Tag color="geekblue">第 {s.turnIndex} 轮</Tag>
                                                <Tag color="blue">{s.lifecycleStatus ?? '—'}</Tag>
                                                <Tag color={s.handoffReady ? 'green' : 'default'}>
                                                    handoff {String(s.handoffReady ?? '—')}
                                                </Tag>
                                                <Tag>{s.collectionStage ?? '—'}</Tag>
                                                <Tag color="purple">intent {s.intentLabel}</Tag>
                                            </Space>
                                            <div style={{ marginTop: 10, fontSize: 13, lineHeight: 1.55, color: '#262626' }}>
                                                <Text style={{ color: '#595959', fontSize: 12 }}>客户 </Text>
                                                {s.customerLine}
                                            </div>
                                            <div style={{ marginTop: 6, fontSize: 13, lineHeight: 1.55, color: '#262626' }}>
                                                <Text style={{ color: '#595959', fontSize: 12 }}>助理 </Text>
                                                {s.replySnippet}
                                            </div>
                                            <div style={{ marginTop: 6, fontSize: 12, color: '#595959' }}>
                                                仍缺：{s.stillNeededSummary}
                                            </div>
                                        </div>
                                    ))}

                                    {roleCPlusEnd && (
                                        <Card
                                            size="small"
                                            style={{ background: '#f5f5f5', borderColor: '#d9d9d9' }}
                                        >
                                            <Text strong style={{ display: 'block', marginBottom: 8, color: '#262626' }}>
                                                结束报告
                                            </Text>
                                            <ul
                                                style={{
                                                    margin: '0 0 8px 18px',
                                                    padding: 0,
                                                    fontSize: 13,
                                                    lineHeight: 1.6,
                                                }}
                                            >
                                                <li>总客户轮次：{roleCPlusEnd.totalTurns}</li>
                                                <li>末轮 lifecycle：{roleCPlusEnd.finalLifecycle ?? '—'}</li>
                                                <li>末轮 handoff_ready：{String(roleCPlusEnd.finalHandoffReady ?? '—')}</li>
                                                <li>
                                                    formal_submitted_at：
                                                    {roleCPlusEnd.formalSubmittedAt ?? '（仿真未触发 formal_submit 时通常为空）'}
                                                </li>
                                            </ul>
                                            <Text style={{ fontSize: 13, display: 'block', marginBottom: 8 }}>
                                                {roleCPlusEnd.overallRead}
                                            </Text>
                                            {roleCPlusEnd.warnings.length > 0 && (
                                                <Alert
                                                    type="warning"
                                                    showIcon
                                                    message="可能的异常模式（启发式，非定论）"
                                                    description={
                                                        <ul style={{ margin: '8px 0 0 18px', padding: 0 }}>
                                                            {roleCPlusEnd.warnings.map((w, i) => (
                                                                <li key={i}>{w}</li>
                                                            ))}
                                                        </ul>
                                                    }
                                                />
                                            )}
                                        </Card>
                                    )}
                                </Space>
                            )}
                        </Card>
                    </Col>
                </Row>
            )}
        </div>
    );
}
