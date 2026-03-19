/**
 * Visual Simulation Assistant — lightweight script-driven replay for demo and QA.
 *
 * Helps founders, testers, and Chen Kui quickly see whether Customer Entry
 * behaves correctly through scripted multi-turn conversations.
 *
 * Scenario names align with trial pack: Cancellation risk, Missing document,
 * Add-car quote, Premium review, Claim intake. Recommended trial order shown first.
 */
import { useState } from 'react';
import {
    Button,
    Card,
    Drawer,
    Space,
    Spin,
    Tag,
    Typography,
    message,
} from 'antd';
import {
    CaretRightOutlined,
    PauseOutlined,
    PlayCircleOutlined,
    ReloadOutlined,
    RightOutlined,
    ThunderboltOutlined,
} from '@ant-design/icons';
import { triageMessage, type TriageResult, type ConversationTurn } from '../../api/inboxTriage';
import { useClientConfig } from '../../context/ClientConfigContext';

/** Infer case focus from structured fields — matches UnifiedIntakePage logic */
function inferCaseFocus(
    collected?: string[],
    stillNeeded?: string[],
    category?: string,
    sourceText?: string,
): string | null {
    const fields = [...(collected ?? []), ...(stillNeeded ?? [])];
    if (fields.some((f) => ['year', 'make_model', 'zip', 'delivery_date', 'primary_driver', 'vin'].includes(f))) return 'Add car quote';
    if (fields.some((f) => /premium|renewal|remove_vehicle|coverage_adjust/.test(f))) return 'Premium review';
    if (fields.some((f) => /accident|photos|other_driver|hit_and_run|police_report/.test(f))) return 'Claim intake';
    if (category === 'missing_document' || category === 'underwriting_followup' || fields.some((f) => /declaration|garaging|driver_license|verify_carrier/.test(f))) return 'Missing document';
    if (category === 'cancellation_warning' || category === 'payment_lapse_expiration') return 'Payment / cancellation risk';
    if (sourceText) {
        const t = sourceText.toLowerCase();
        if (/\b(加|加一台|加一辆|新车|提车|报价|先出报价|买了|保费多少钱)\b/.test(t) && /\b(车|vin|tesla|toyota|honda|model|bmw|宝马|x5)\b/i.test(t)) return 'Add car quote';
        if (/\b(拿掉|删掉|去掉|卖掉|卖车|卖掉了)\b/.test(t) && /\b(车|honda|accord|vehicle)\b/i.test(t)) return 'Remove car';
        if (/\b(保费|太贵|太高|怎么降|降一点|续保)\b/.test(t)) return 'Premium review';
        if (/\b(事故|出险|理赔|撞车|撞了|accident|claim)\b/.test(t)) return 'Claim intake';
        if (/\b(dmv|sr-22|sr22|suspension|clearance|带什么)\b/i.test(t)) return 'DMV / SR-22 help';
    }
    return null;
}

/** One-line handoff summary — matches Case handoff structure */
function getOneLiner(triage: TriageResult, customerText: string): string {
    const focus = inferCaseFocus(triage.collected_fields, triage.still_needed_fields, triage.issue_category, triage.source_text ?? customerText);
    const stage = triage.collection_stage === 'enough_for_handoff' ? 'Ready for handoff' : 'Collecting';
    const nextPreview = (triage.broker_next_step ?? '').slice(0, 60);
    const suffix = nextPreview ? ` — ${nextPreview}${nextPreview.length >= 60 ? '…' : ''}` : '';
    return focus ? `${stage}: ${focus}${suffix}` : `${stage}${suffix}`.trim() || '';
}

/** Humanize structured field for trial/demo display — matches UnifiedIntakePage labels */
function humanizeStructuredField(field: string): string {
    const LABELS: Record<string, string> = {
        year: 'Year',
        make_model: 'Make/Model',
        zip: 'ZIP',
        delivery_date: 'Delivery',
        primary_driver: 'Primary driver',
        vin: 'VIN',
        accident_reported: 'Accident reported',
        hit_and_run: 'Hit-and-run',
        photos: 'Photos',
        other_driver_info: 'Other driver info',
        requested_declaration_page: 'Requested: Declaration page',
        requested_garaging_proof: 'Requested: Garaging proof',
        customer_says_sent_declaration_page: 'Customer says sent: Declaration page',
        customer_says_sent_garaging_proof: 'Customer says sent: Garaging proof',
        premium_concern: 'Premium too high',
        policy_bill_sent: 'Policy/bill sent',
    };
    return LABELS[field] ?? field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
}

// Load scenarios from config (single source of truth for titles, sections, trial order)
// Use ui/src/config copy so Vercel build has access (configs/ is at repo root)
import simulationConfig from '../../config/simulation_assistant_scenarios.json';

const { Text } = Typography;

export type SimulationScenario = {
    id: string;
    flow_type: string;
    title: string;
    section?: 'recommended' | 'real_customer' | 'multi_turn' | 'edge_cases';
    trial_order?: number;
    turns: Array<{ role: 'customer'; text: string }>;
    expected_handoff_after_turn: number;
    notes: string;
};

const configScenarios = (simulationConfig as { scenarios?: SimulationScenario[] }).scenarios ?? [];
const SIMULATION_SCENARIOS: SimulationScenario[] = configScenarios.map((s) => ({
    id: s.id,
    flow_type: s.flow_type,
    title: s.title,
    section: s.section,
    trial_order: s.trial_order,
    turns: s.turns,
    expected_handoff_after_turn: s.expected_handoff_after_turn,
    notes: s.notes,
}));

/** Group scenarios for display: Recommended Trial, Real customer style, Multi-turn proof, Edge cases */
function groupScenarios(scenarios: SimulationScenario[]): { label: string; scenarios: SimulationScenario[] }[] {
    const recommended = scenarios
        .filter((s) => s.section === 'recommended')
        .sort((a, b) => (a.trial_order ?? 99) - (b.trial_order ?? 99));
    const realCustomer = scenarios.filter((s) => s.section === 'real_customer');
    const multiTurn = scenarios.filter((s) => s.section === 'multi_turn');
    const edgeCases = scenarios.filter((s) => s.section === 'edge_cases');
    const groups: { label: string; scenarios: SimulationScenario[] }[] = [];
    if (recommended.length) groups.push({ label: 'Recommended trial (3–4 turn)', scenarios: recommended });
    if (realCustomer.length) groups.push({ label: 'Real customer style (messy, short, mixed)', scenarios: realCustomer });
    if (multiTurn.length) groups.push({ label: 'Strongest multi-turn proof', scenarios: multiTurn });
    if (edgeCases.length) groups.push({ label: 'Edge cases / QA', scenarios: edgeCases });
    return groups;
}

type EvalTag = 'Normal' | 'Needs review' | 'Off-flow / suspicious';

function computeEvalTag(
    scenario: SimulationScenario,
    replayTurns: ReplayTurn[],
): { tag: EvalTag; notes: string[] } {
    const notes: string[] = [];
    const systemTurns = replayTurns.filter((t) => t.role === 'system');
    const firstReply = systemTurns[0]?.content ?? '';
    const firstLower = firstReply.toLowerCase();
    let issueAtTurn: number | null = null;

    // Find handoff turn: first system turn with handoff_ready
    let handoffAtTurn: number | null = null;
    for (let i = 0; i < replayTurns.length; i++) {
        if (replayTurns[i].role === 'system' && replayTurns[i].triageResult?.handoff_ready) {
            handoffAtTurn = Math.floor(i / 2) + 1; // customer turn index (1-based)
            break;
        }
    }

    // Anti-patterns — with turn hint for visibility
    if (/please provide more context|这段内容还不够完整/i.test(firstReply)) {
        if (['add_car', 'notice_cancellation', 'missing_document', 'claim', 'renewal_premium'].includes(scenario.flow_type)) {
            return { tag: 'Off-flow / suspicious', notes: ['Issue likely at turn 1', 'First reply too generic for clear intent'] };
        }
    }
    if (/thank you for reaching out|feel free to ask/i.test(firstLower)) {
        notes.push('Robotic/formulaic first reply');
        issueAtTurn = 1;
    }

    // Handoff timing
    const expected = scenario.expected_handoff_after_turn;
    const customerTurnCount = replayTurns.filter((t) => t.role === 'customer').length;
    const isComplete = customerTurnCount >= scenario.turns.length;

    if (handoffAtTurn === null) {
        if (isComplete) {
            issueAtTurn = expected;
            return { tag: 'Off-flow / suspicious', notes: [...notes, `Issue likely at turn ${expected}`, 'No handoff after expected turns'] };
        }
        return { tag: 'Needs review', notes: [...notes, 'Simulation incomplete'] };
    }
    if (handoffAtTurn === expected) {
        if (notes.length > 0) {
            if (issueAtTurn) notes.unshift(`Issue likely at turn ${issueAtTurn}`);
            return { tag: 'Needs review', notes };
        }
        const turnCount = customerTurnCount;
        const depthNote = turnCount >= 3 ? `Shows ${turnCount}-turn conversation value` : 'Good next-step guidance';
        return { tag: 'Normal', notes: [depthNote, 'Handoff at expected turn'] };
    }
    if (handoffAtTurn < expected) {
        notes.push('Handoff earlier than expected');
        return { tag: notes.length > 0 ? 'Needs review' : 'Normal', notes };
    }
    // Handoff late: issue at expected turn (we expected handoff there but didn't get it)
    issueAtTurn = expected;
    notes.push(`Handoff at turn ${handoffAtTurn}, expected ${expected}`);
    notes.unshift(`Issue likely at turn ${issueAtTurn}`);
    return { tag: 'Needs review', notes };
}

function getEvalTagColor(tag: EvalTag): string {
    if (tag === 'Normal') return 'green';
    if (tag === 'Needs review') return 'orange';
    return 'red';
}

type ReplayTurn = {
    role: 'customer' | 'system';
    content: string;
    triageResult?: TriageResult;
};

type SimulationAssistantProps = {
    open: boolean;
    onClose: () => void;
    onReplayReady?: (turns: ReplayTurn[], evalTag: EvalTag, evalNotes: string[]) => void;
};

export function SimulationAssistant({ open, onClose, onReplayReady }: SimulationAssistantProps) {
    const { clientId } = useClientConfig();
    const [selectedScenario, setSelectedScenario] = useState<SimulationScenario | null>(null);
    const [replayTurns, setReplayTurns] = useState<ReplayTurn[]>([]);
    const [currentTurnIndex, setCurrentTurnIndex] = useState(0);
    const [loading, setLoading] = useState(false);
    const [autoPlay, setAutoPlay] = useState(false);
    const [evalResult, setEvalResult] = useState<{ tag: EvalTag; notes: string[] } | null>(null);

    const customerTurns = selectedScenario?.turns ?? [];
    const nextCustomerTurnIndex = replayTurns.filter((t) => t.role === 'customer').length;
    const hasMoreTurns = nextCustomerTurnIndex < customerTurns.length;

    const runNextTurn = async () => {
        if (!selectedScenario || loading || !hasMoreTurns) return;
        const customerText = customerTurns[nextCustomerTurnIndex].text;

        setLoading(true);
        const customerTurn: ReplayTurn = { role: 'customer', content: customerText };
        setReplayTurns((prev) => [...prev, customerTurn]);

        const conversationTurnsForApi: ConversationTurn[] = replayTurns.map((t) => ({
            role: t.role,
            text: t.content,
        }));

        try {
            const data = await triageMessage(customerText, false, conversationTurnsForApi, undefined, undefined, clientId);
            const systemTurn: ReplayTurn = {
                role: 'system',
                content: data.client_reply_draft,
                triageResult: data,
            };
            setReplayTurns((prev) => [...prev, systemTurn]);
            setCurrentTurnIndex(nextCustomerTurnIndex + 1);

            const updatedTurns: ReplayTurn[] = [...replayTurns, customerTurn, systemTurn];
            const eval_ = computeEvalTag(selectedScenario, updatedTurns);
            setEvalResult(eval_);

            const nowComplete = nextCustomerTurnIndex + 1 >= customerTurns.length;
            if (nowComplete) {
                onReplayReady?.(updatedTurns, eval_.tag, eval_.notes);
            }

            if (autoPlay && nextCustomerTurnIndex + 1 < customerTurns.length) {
                setTimeout(() => void runNextTurn(), 1800);
            } else if (nextCustomerTurnIndex + 1 >= customerTurns.length) {
                setAutoPlay(false);
            }
        } catch (e: unknown) {
            setReplayTurns((prev) => prev.slice(0, -1));
            const msg = (e as { response?: { data?: { detail?: string } }; message?: string })?.response?.data?.detail
                ?? (e as { message?: string })?.message
                ?? 'Simulation request failed.';
            message.error(msg);
        } finally {
            setLoading(false);
        }
    };

    const handleStartSimulation = () => {
        if (!selectedScenario) {
            message.warning('Select a scenario first');
            return;
        }
        setReplayTurns([]);
        setCurrentTurnIndex(0);
        setEvalResult(null);
        setAutoPlay(false);
        void runNextTurn();
    };

    const handleReset = () => {
        setReplayTurns([]);
        setCurrentTurnIndex(0);
        setEvalResult(null);
        setAutoPlay(false);
    };

    const handleToggleAutoPlay = () => {
        if (autoPlay) {
            setAutoPlay(false);
            return;
        }
        if (!hasMoreTurns) return;
        setAutoPlay(true);
        void runNextTurn();
    };

    return (
        <Drawer
            title={
                <Space>
                    <ThunderboltOutlined />
                    <span>Simulation Assistant</span>
                </Space>
            }
            placement="right"
            width={480}
            open={open}
            onClose={onClose}
        >
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                    Run scripted multi-turn scenarios to see how the system responds. Useful for demo and QA.
                </Text>
                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginTop: 4 }}>
                    Trial: Top 5 are 3-turn deep. Real customer pack: messy, short, mixed-language — like real small-client traffic.
                </Text>

                <Card size="small" title="Scenario" styles={{ body: { padding: 12 } }}>
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        {groupScenarios(SIMULATION_SCENARIOS).map((group) => (
                            <div key={group.label}>
                                <Text type="secondary" style={{ fontSize: 11, display: 'block', marginBottom: 6 }}>
                                    {group.label}
                                </Text>
                                <Space direction="vertical" size="small" style={{ width: '100%', marginBottom: 12 }}>
                                    {group.scenarios.map((s) => (
                                        <Button
                                            key={s.id}
                                            size="small"
                                            type={selectedScenario?.id === s.id ? 'primary' : 'default'}
                                            block
                                            onClick={() => {
                                                setSelectedScenario(s);
                                                handleReset();
                                            }}
                                        >
                                            {s.title}
                                        </Button>
                                    ))}
                                </Space>
                            </div>
                        ))}
                    </Space>
                </Card>

                {selectedScenario && (
                    <Card size="small" title="Controls" styles={{ body: { padding: 12 } }}>
                        <Space wrap size="small">
                            <Button
                                type="primary"
                                icon={<PlayCircleOutlined />}
                                onClick={handleStartSimulation}
                                loading={loading}
                                disabled={loading}
                            >
                                {replayTurns.length === 0 ? 'Run simulation' : 'Replay'}
                            </Button>
                            <Button
                                icon={<RightOutlined />}
                                onClick={() => void runNextTurn()}
                                loading={loading}
                                disabled={!hasMoreTurns}
                            >
                                Next turn
                            </Button>
                            <Button
                                icon={autoPlay ? <PauseOutlined /> : <CaretRightOutlined />}
                                onClick={handleToggleAutoPlay}
                                disabled={!hasMoreTurns || loading}
                            >
                                {autoPlay ? 'Pause' : 'Auto-play'}
                            </Button>
                            <Button icon={<ReloadOutlined />} onClick={handleReset}>
                                Reset
                            </Button>
                        </Space>
                    </Card>
                )}

                {evalResult && (
                    <Card size="small" title="Evaluation" styles={{ body: { padding: 12 } }}>
                        <Space direction="vertical" size="small" style={{ width: '100%' }}>
                            <Tag color={getEvalTagColor(evalResult.tag)}>{evalResult.tag}</Tag>
                            {evalResult.notes.map((n, i) => (
                                <Text key={i} type="secondary" style={{ fontSize: 12, display: 'block' }}>
                                    • {n}
                                </Text>
                            ))}
                        </Space>
                    </Card>
                )}

                {replayTurns.length > 0 && (() => {
                    const lastSystemTurn = [...replayTurns].reverse().find((t) => t.role === 'system');
                    const lastTriage = lastSystemTurn?.triageResult;
                    const isComplete = nextCustomerTurnIndex >= customerTurns.length;
                    const showCaseReport = isComplete && lastTriage;
                    return (
                        <>
                            {showCaseReport && (() => {
                                const caseFocus = inferCaseFocus(
                                    lastTriage.collected_fields,
                                    lastTriage.still_needed_fields,
                                    lastTriage.issue_category,
                                    lastTriage.source_text ?? customerTurns[0]?.text,
                                );
                                const oneLiner = getOneLiner(lastTriage, customerTurns[0]?.text ?? '');
                                return (
                                    <Card
                                        size="small"
                                        title={
                                            <Space wrap size={[4, 4]}>
                                                <span style={{ color: '#262626' }}>Case handoff</span>
                                                <span style={{ fontSize: 11, fontWeight: 'normal', color: '#595959' }}>
                                                    — outcome of this run
                                                </span>
                                            </Space>
                                        }
                                        styles={{
                                            body: { padding: 12 },
                                            header: { color: '#262626', borderColor: 'rgba(0,0,0,0.06)' },
                                        }}
                                        style={{
                                            background: lastTriage.handoff_ready ? '#f6ffed' : '#fff7e6',
                                            borderColor: lastTriage.handoff_ready ? '#b7eb8f' : '#ffd591',
                                        }}
                                    >
                                        <Space direction="vertical" size={6} style={{ width: '100%', color: '#262626' }}>
                                            {caseFocus && (
                                                <Tag color="blue" style={{ fontSize: 10 }}>{caseFocus}</Tag>
                                            )}
                                            <Space wrap size={[4, 4]}>
                                                {lastTriage.handoff_ready && (
                                                    <Tag color="green" style={{ fontSize: 10 }}>Ready for handoff</Tag>
                                                )}
                                                {lastTriage.collection_stage && (
                                                    <Tag color={lastTriage.collection_stage === 'enough_for_handoff' ? 'green' : 'default'} style={{ fontSize: 10 }}>
                                                        {lastTriage.collection_stage === 'enough_for_handoff' ? 'Ready for handoff' : 'Collecting info'}
                                                    </Tag>
                                                )}
                                                {lastTriage.human_confirmation_required && (
                                                    <Tag color="gold" style={{ fontSize: 10 }}>Human confirmation recommended</Tag>
                                                )}
                                            </Space>
                                            {oneLiner && (
                                                <div style={{ fontSize: 13, fontWeight: 500, color: '#262626' }}>{oneLiner}</div>
                                            )}
                                            {lastTriage.broker_next_step && (
                                                <div>
                                                    <div style={{ fontSize: 10, textTransform: 'uppercase', color: '#595959', marginBottom: 2 }}>Your next move</div>
                                                    <div style={{ marginTop: 2, fontSize: 13, color: '#262626', fontWeight: 500 }}>{lastTriage.broker_next_step}</div>
                                                </div>
                                            )}
                                            {lastTriage.human_confirmation_required && (
                                                <div style={{ padding: 8, background: 'rgba(250, 173, 20, 0.1)', borderRadius: 6, borderLeft: '3px solid #faad14' }}>
                                                    <Text type="secondary" style={{ fontSize: 11 }}>Verify before acting: payment status, customer_says_sent, or add-car VIN/driver.</Text>
                                                </div>
                                            )}
                                            {((lastTriage.collected_fields?.length ?? 0) > 0 || (lastTriage.still_needed_fields?.length ?? 0) > 0) && (
                                                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                                                    {(lastTriage.collected_fields?.length ?? 0) > 0 && (
                                                        <span>
                                                            <div style={{ fontSize: 10, display: 'block', marginBottom: 2, color: '#595959' }}>Collected</div>
                                                            <span style={{ color: '#262626', fontSize: 12 }}>{(lastTriage.collected_fields ?? []).map(humanizeStructuredField).join(', ')}</span>
                                                        </span>
                                                    )}
                                                    {(lastTriage.still_needed_fields?.length ?? 0) > 0 && (
                                                        <span>
                                                            <div style={{ fontSize: 10, display: 'block', marginBottom: 2, color: '#595959' }}>Still needed</div>
                                                            <span style={{ color: '#262626', fontSize: 12 }}>{(lastTriage.still_needed_fields ?? []).map(humanizeStructuredField).join(', ')}</span>
                                                        </span>
                                                    )}
                                                </div>
                                            )}
                                        </Space>
                                    </Card>
                                );
                            })()}
                            <Card size="small" title="Replay" styles={{ body: { padding: 12 } }}>
                        <div
                            style={{
                                maxHeight: 360,
                                overflowY: 'auto',
                                fontSize: 13,
                                minHeight: 200,
                            }}
                        >
                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                {replayTurns.map((t, idx) => (
                                    <div
                                        key={idx}
                                        style={{
                                            textAlign: t.role === 'customer' ? 'right' : 'left',
                                            padding: 10,
                                            borderRadius: 6,
                                            marginBottom: 6,
                                            background: t.role === 'customer' ? 'rgba(24, 144, 255, 0.1)' : 'rgba(82, 196, 26, 0.1)',
                                            borderLeft: t.role === 'system' ? '3px solid #52c41a' : undefined,
                                            borderRight: t.role === 'customer' ? '3px solid #1890ff' : undefined,
                                        }}
                                    >
                                        <Text type="secondary" style={{ fontSize: 11 }}>
                                            {t.role === 'customer' ? 'Customer' : 'System'}
                                        </Text>
                                        <div style={{ whiteSpace: 'pre-wrap', marginTop: 4 }}>{t.content}</div>
                                        {t.role === 'system' && t.triageResult && (
                                            <Space size={[4, 4]} wrap style={{ marginTop: 8, display: 'flex' }}>
                                                {t.triageResult.handoff_ready && (
                                                    <Tag color="green" style={{ fontSize: 10 }}>Ready for handoff</Tag>
                                                )}
                                                {(t.triageResult.collected_fields?.length ?? 0) > 0 && (
                                                    <Tag color="green" style={{ fontSize: 10 }}>
                                                        Collected: {(t.triageResult.collected_fields ?? []).map(humanizeStructuredField).slice(0, 4).join(', ')}
                                                        {(t.triageResult.collected_fields?.length ?? 0) > 4 ? '…' : ''}
                                                    </Tag>
                                                )}
                                                {(t.triageResult.still_needed_fields?.length ?? 0) > 0 && (
                                                    <Tag color="orange" style={{ fontSize: 10 }}>
                                                        Still needed: {(t.triageResult.still_needed_fields ?? []).map(humanizeStructuredField).slice(0, 3).join(', ')}
                                                        {(t.triageResult.still_needed_fields?.length ?? 0) > 3 ? '…' : ''}
                                                    </Tag>
                                                )}
                                                {t.triageResult.human_confirmation_required && (
                                                    <Tag color="gold" style={{ fontSize: 10 }}>Human confirmation recommended</Tag>
                                                )}
                                            </Space>
                                        )}
                                    </div>
                                ))}
                                {loading && (
                                    <div
                                        style={{
                                            textAlign: 'left',
                                            padding: 10,
                                            borderRadius: 6,
                                            marginBottom: 6,
                                            background: 'rgba(82, 196, 26, 0.08)',
                                            borderLeft: '3px solid #52c41a',
                                        }}
                                    >
                                        <Text type="secondary" style={{ fontSize: 11 }}>System</Text>
                                        <div style={{ marginTop: 6, display: 'flex', alignItems: 'center', gap: 8 }}>
                                            <Spin size="small" />
                                            <Text type="secondary" style={{ fontSize: 13 }}>正在整理 case...</Text>
                                        </div>
                                    </div>
                                )}
                            </Space>
                        </div>
                    </Card>
                        </>
                    );
                })()}

                {selectedScenario && (
                    <Text type="secondary" style={{ fontSize: 11 }}>
                        {selectedScenario.notes}
                    </Text>
                )}
            </Space>
        </Drawer>
    );
}

export { SIMULATION_SCENARIOS };
