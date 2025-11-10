import { type KeyboardEvent, useCallback, useEffect, useRef, useState } from 'react';
import React from 'react';
import { Button, Card, Collapse, Input, Space, Tag, Tooltip, Typography, message } from 'antd';
import { startPolling } from '../../api/polling';
import { safeError } from '../../api/orchestrate';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

const REVIEW_COMMAND = /^(?:review|suggest)\s+([a-f0-9]{10,16})$/i;
const APPLY_COMMAND = /^apply\s+([a-f0-9]{10,16})$/i;
const APPLY_WITH_JSON = /^apply\s+([a-f0-9]{6,})\s+(\{[\s\S]*\})$/i;
const HEX_ONLY = /\b([a-f0-9]{10,16})\b/i;

const STATUS_COLORS: Record<string, string> = {
    SUCCEEDED: 'green',
    FAILED: 'red',
    CANCELLED: 'orange',
    CANCELED: 'orange',
    ERROR: 'red',
    TIMEOUT: 'magenta',
    ABORTED: 'volcano',
};

const HELP_MESSAGE = 'review <job_id> | suggest <job_id> | apply <job_id>';

type MetricKey = 'p95_ms' | 'err_rate' | 'recall_at_10' | 'cost_tokens';

const METRIC_CONFIG: Record<
    MetricKey,
    {
        label: string;
        decimals?: number;
        percent?: boolean;
        positiveIsGood: boolean;
    }
> = {
    p95_ms: { label: 'P95 (ms)', decimals: 0, positiveIsGood: false },
    err_rate: { label: 'Error Rate', decimals: 2, percent: true, positiveIsGood: false },
    recall_at_10: { label: 'Recall@10', decimals: 3, positiveIsGood: true },
    cost_tokens: { label: 'Tokens', decimals: 0, positiveIsGood: false },
};

const toNumber = (value: unknown): number | null => {
    if (typeof value === 'number' && Number.isFinite(value)) return value;
    if (typeof value === 'string') {
        const parsed = Number(value);
        return Number.isFinite(parsed) ? parsed : null;
    }
    return null;
};

const formatMetricValue = (value: unknown, key: MetricKey): string => {
    const config = METRIC_CONFIG[key];
    const num = toNumber(value);
    if (num === null) return '—';
    if (key === 'p95_ms' && num <= 0) return '—';
    if (config.percent) {
        const pct = num * 100;
        return `${pct.toFixed(config.decimals ?? 2)}%`;
    }
    if (typeof config.decimals === 'number') {
        if (config.decimals === 0) {
            return Math.round(num).toLocaleString();
        }
        return num.toFixed(config.decimals);
    }
    return num.toString();
};

const formatDeltaValue = (value: unknown, key: MetricKey): { label: string; type: 'secondary' | 'success' | 'danger' } => {
    const config = METRIC_CONFIG[key];
    const num = toNumber(value);
    if (num === null) {
        return { label: '—', type: 'secondary' };
    }
    if (num === 0) {
        return { label: '±0', type: 'secondary' };
    }
    const formatted = config.percent
        ? `${(num * 100).toFixed(config.decimals ?? 2)}%`
        : typeof config.decimals === 'number'
            ? config.decimals === 0
                ? Math.round(num).toLocaleString()
                : num.toFixed(config.decimals)
            : num.toString();
    const label = `${num > 0 ? '+' : ''}${formatted}`;
    const isGood = config.positiveIsGood ? num >= 0 : num <= 0;
    return { label, type: isGood ? 'success' : 'danger' };
};

interface StewardSuggestion {
    policy: string;
    changes: Record<string, unknown>;
    expected_effect?: string;
    risk?: string;
}

interface StewardSummaryMeta {
    source?: string | null;
    job_status?: Record<string, unknown>;
    status_note?: string | null;
    baseline_path?: string | null;
    deltas?: Record<string, unknown>;
    metrics_fallback?: string | null;
}

interface StewardReview {
    job_id: string;
    summary: Record<string, unknown>;
    summary_compact?: string;
    summary_meta?: StewardSummaryMeta;
    reflection: string[];
    suggestion: StewardSuggestion;
    baseline?: Record<string, unknown>;
    meta?: StewardReflectionMeta;
}

interface StewardReflectionMeta {
    reflection_source: 'llm' | 'rules';
    llm?: {
        model?: string | null;
        tokens_in?: number | null;
        tokens_out?: number | null;
        cost_usd_est?: number | null;
    } | null;
}

type ChatItem =
    | { key: string; type: 'user'; text: string }
    | { key: string; type: 'system'; text: string }
    | { key: string; type: 'status'; jobId: string; status: string }
    | { key: string; type: 'review'; review: StewardReview };

const makeKey = () => `${Date.now()}-${Math.random().toString(16).slice(2, 8)}`;

export interface StewardChatProps {
    onBeforeStart?: () => void;
    onStart?: (jobId: string) => void;
    onStop?: () => void;
    onRegisterStop?: (stopper: (() => void) | null) => void;
}

const StewardChat = ({ onBeforeStart, onStart, onStop, onRegisterStop }: StewardChatProps) => {
    const [inputValue, setInputValue] = useState('');
    const [messages, setMessages] = useState<ChatItem[]>([]);
    const [applyTarget, setApplyTarget] = useState<string | null>(null);

    const listContainerRef = useRef<HTMLDivElement | null>(null);
    const pollControllerRef = useRef<{ stop: () => void } | null>(null);
    const activeJobRef = useRef<string | null>(null);
    const lastStatusRef = useRef<string | null>(null);

    const appendMessage = useCallback((item: ChatItem) => {
        setMessages((prev) => [...prev, item]);
    }, []);

    const appendSystem = useCallback(
        (text: string) => {
            appendMessage({
                key: makeKey(),
                type: 'system',
                text,
            });
        },
        [appendMessage],
    );

    const scrollToBottom = useCallback(() => {
        const container = listContainerRef.current;
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }, []);

    useEffect(scrollToBottom, [messages, scrollToBottom]);

    const stopPolling = useCallback(
        (silent = false) => {
            if (pollControllerRef.current) {
                pollControllerRef.current.stop();
                pollControllerRef.current = null;
            }
            const lastJob = activeJobRef.current;
            activeJobRef.current = null;
            lastStatusRef.current = null;
            if (!silent && lastJob) {
                appendSystem(`Stopped polling run ${lastJob}`);
            }
            onStop?.();
        },
        [appendSystem, onStop],
    );

    useEffect(() => {
        return () => {
            stopPolling(true);
        };
    }, [stopPolling]);

    useEffect(() => {
        if (!onRegisterStop) return;
        onRegisterStop(() => stopPolling());
        return () => onRegisterStop(null);
    }, [onRegisterStop, stopPolling]);

    const startPollingLoop = useCallback(
        (jobId: string, pollPath?: string) => {
            const controller = startPolling({
                pollPath: pollPath || `/orchestrate/status/${jobId}`,
                intervalMs: 2000,
                detail: 'lite',
                onUpdate: ({ state }) => {
                    if (!state) return;
                    if (state !== lastStatusRef.current) {
                        lastStatusRef.current = state;
                        appendMessage({
                            key: makeKey(),
                            type: 'status',
                            jobId,
                            status: state,
                        });
                    }
                },
                onDone: (state, payload) => {
                    pollControllerRef.current = null;
                    activeJobRef.current = null;
                    lastStatusRef.current = null;
                    if (state === 'ERROR') {
                        const err = typeof payload?.error === 'string' ? payload.error : 'Polling failed';
                        appendSystem(`Run ${jobId} errored: ${err}`);
                        message.error(err);
                    } else {
                        appendSystem(`Run ${jobId} completed with ${state}`);
                    }
                    onStop?.();
                },
            });
            pollControllerRef.current = controller;
            activeJobRef.current = jobId;
            lastStatusRef.current = null;
        },
        [appendMessage, appendSystem, onStop],
    );

    const fetchReview = useCallback(
        async (jobId: string) => {
            appendSystem(`Fetching review for ${jobId}…`);
            try {
                const response = await fetch(`/api/steward/review?job_id=${jobId}&suggest=1`);
                if (!response.ok) {
                    throw response;
                }
                const data = (await response.json()) as StewardReview;
                appendMessage({
                    key: makeKey(),
                    type: 'review',
                    review: data,
                });
            } catch (error) {
                const text = await safeError(error);
                appendSystem(`Review failed: ${text}`);
                message.error(text);
            }
        },
        [appendMessage, appendSystem],
    );

    const triggerApply = useCallback(
        async (
            sourceJobId: string,
            rawChanges: Record<string, unknown> | null = null,
            presetOverride?: string | null,
        ) => {
            const sanitizedChanges: Record<string, unknown> = {};
            if (rawChanges && typeof rawChanges === 'object' && !Array.isArray(rawChanges)) {
                Object.entries(rawChanges).forEach(([key, value]) => {
                    sanitizedChanges[key] = value;
                });
            }
            const hasChanges = Object.keys(sanitizedChanges).length > 0;
            const payload: Record<string, unknown> = { job_id: sourceJobId };
            if (presetOverride !== undefined) {
                payload.preset = presetOverride;
            } else {
                payload.preset = 'smoke-fast';
            }
            if (hasChanges) {
                payload.changes = sanitizedChanges;
            }

            onBeforeStart?.();
            stopPolling(true);
            setApplyTarget(sourceJobId);
            appendSystem(
                `Submitting steward apply for ${sourceJobId} with ${hasChanges ? `${JSON.stringify(sanitizedChanges)}` : 'default overrides'
                }…`,
            );

            try {
                const response = await fetch('/api/steward/apply', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) {
                    throw response;
                }

                const data = await response.json();
                const newJobId = typeof data?.job_id === 'string' ? data.job_id : '';
                if (!newJobId) {
                    throw new Error('missing_job_id');
                }
                const pollPath = typeof data?.poll === 'string' ? data.poll : undefined;
                const logsPath = typeof data?.logs === 'string' ? data.logs : undefined;
                const pollHint = pollPath ? `; poll: ${pollPath}` : '';
                const logsHint = logsPath ? `; logs: ${logsPath}` : '';

                appendSystem(
                    `Apply started job ${newJobId} (source ${sourceJobId})${pollHint}${logsHint}.`,
                );
                onStart?.(newJobId);
                startPollingLoop(newJobId, pollPath);
            } catch (error) {
                const text = await safeError(error);
                appendSystem(`Apply failed for ${sourceJobId}: ${text}`);
                message.error(text);
            } finally {
                setApplyTarget(null);
            }
        },
        [appendSystem, onBeforeStart, onStart, startPollingLoop, stopPolling],
    );

    const handleDryRun = useCallback(
        (review: StewardReview) => {
            void triggerApply(review.job_id, null, 'smoke-fast');
        },
        [triggerApply],
    );

    const handleCopyCurl = useCallback(async (review: StewardReview) => {
        const origin =
            typeof window !== 'undefined' && window.location && window.location.origin
                ? window.location.origin
                : 'http://localhost:8000';
        const reviewCurl = `curl -s '${origin}/api/steward/review?job_id=${review.job_id}&suggest=1' | jq`;
        const applyCurl = `curl -s -X POST '${origin}/api/steward/apply' -H 'Content-Type: application/json' -d '{"job_id":"${review.job_id}","preset":"smoke-fast"}' | jq`;
        const command = `${reviewCurl}\n${applyCurl}`;
        try {
            await navigator.clipboard.writeText(command);
            message.success('已复制 cURL 命令');
        } catch {
            message.error('复制失败，请手动复制命令');
        }
    }, []);

    const handleSend = useCallback(async () => {
        const prompt = inputValue.trim();
        if (!prompt) {
            message.warning('请输入要发送的内容');
            return;
        }

        appendMessage({
            key: makeKey(),
            type: 'user',
            text: prompt,
        });
        setInputValue('');

        if (/^help$/i.test(prompt)) {
            appendSystem(`Commands: ${HELP_MESSAGE}`);
            return;
        }

        const applyWithJsonMatch = prompt.match(APPLY_WITH_JSON);
        if (applyWithJsonMatch) {
            const jobId = applyWithJsonMatch[1].toLowerCase();
            try {
                const parsed = JSON.parse(applyWithJsonMatch[2]);
                if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
                    throw new Error('payload_must_be_object');
                }
                const parsedRecord = parsed as Record<string, unknown>;
                let presetOverride: string | null | undefined = undefined;
                let changesPayload: Record<string, unknown> | null = null;

                if ('preset' in parsedRecord || 'changes' in parsedRecord) {
                    if (typeof parsedRecord.preset === 'string') {
                        presetOverride = parsedRecord.preset;
                    } else if (parsedRecord.preset === null) {
                        presetOverride = null;
                    }
                    if (
                        parsedRecord.changes &&
                        typeof parsedRecord.changes === 'object' &&
                        !Array.isArray(parsedRecord.changes)
                    ) {
                        changesPayload = parsedRecord.changes as Record<string, unknown>;
                    } else if ('changes' in parsedRecord) {
                        changesPayload = {};
                    }
                } else {
                    changesPayload = parsedRecord;
                }

                await triggerApply(jobId, changesPayload ?? {}, presetOverride);
            } catch (error) {
                appendSystem('Apply JSON 解析失败');
                message.error('Apply JSON 解析失败');
            }
            return;
        }

        const applyMatch = prompt.match(APPLY_COMMAND);
        if (applyMatch) {
            const jobId = applyMatch[1].toLowerCase();
            await triggerApply(jobId, {}, undefined);
            return;
        }

        const reviewMatch = prompt.match(REVIEW_COMMAND);
        if (reviewMatch) {
            const jobId = reviewMatch[1].toLowerCase();
            await fetchReview(jobId);
            return;
        }

        if (prompt.length <= 64) {
            const hexMatch = prompt.match(HEX_ONLY);
            if (hexMatch) {
                const jobId = hexMatch[1].toLowerCase();
                await fetchReview(jobId);
                return;
            }
        }

        appendSystem('未识别为 steward 指令，仅记录文本。');
    }, [appendMessage, appendSystem, fetchReview, inputValue, triggerApply]);

    const handleKeyDown = useCallback(
        (event: KeyboardEvent<HTMLTextAreaElement>) => {
            const isEnter = event.key === 'Enter';
            const isModifier = event.ctrlKey || event.metaKey;
            if (isEnter && isModifier) {
                event.preventDefault();
                void handleSend();
            }
        },
        [handleSend],
    );

    const renderReview = useCallback(
        (review: StewardReview) => {
            const reflection = Array.isArray(review.reflection) ? review.reflection : [];
            const changes = review?.suggestion?.changes ?? {};
            const summaryLine = review.summary_compact || 'No summary available';
            const summary = review.summary ?? {};
            const baseline = review.baseline ?? {};
            const summaryMeta = review.summary_meta ?? {};
            const deltas = (summaryMeta.deltas ?? {}) as Record<string, unknown>;
            const baselinePath =
                typeof summaryMeta.baseline_path === 'string' ? summaryMeta.baseline_path : null;
            const baselineFile = baselinePath ? baselinePath.split('/').pop() ?? baselinePath : null;
            const metricsFallback = summaryMeta.metrics_fallback === 'log';
            const jobStatusMeta = (review.meta as any)?.job_status ?? {};
            const statusHref =
                typeof jobStatusMeta.poll === 'string'
                    ? jobStatusMeta.poll
                    : `/api/experiment/status/${review.job_id}`;
            const logsHref =
                typeof jobStatusMeta.logs === 'string'
                    ? jobStatusMeta.logs
                    : `/api/experiment/logs/${review.job_id}`;
            const meta = review.meta;

            let reflectionTitle = 'Reflection (Rules)';
            if (meta?.reflection_source === 'llm' && meta.llm) {
                const model = meta.llm.model ?? 'unknown';
                const tokensIn = Number(meta.llm.tokens_in ?? 0) || 0;
                const tokensOut = Number(meta.llm.tokens_out ?? 0) || 0;
                const cost = Number(meta.llm.cost_usd_est ?? 0) || 0;
                reflectionTitle = `Reflection (LLM • ${model} • in:${tokensIn} out:${tokensOut} • $${cost.toFixed(4)})`;
            }
            const reflectionLabel = (
                <Space size={4}>
                    <span>{reflectionTitle}</span>
                    {meta?.reflection_source === 'rules' && !meta?.llm && (
                        <Tooltip title="Enable LLM via .env (LLM_API_KEY/OPENAI_API_KEY, LLM_MODEL, LLM_BUDGET_USD)">
                            <Tag>LLM off</Tag>
                        </Tooltip>
                    )}
                </Space>
            );

            return (
                <div
                    style={{
                        width: '100%',
                        border: '1px solid var(--color-border-secondary, #333)',
                        borderRadius: 8,
                        padding: 12,
                        background: 'var(--color-bg-elevated, #1f1f1f)',
                    }}
                >
                    <Space direction="vertical" size="small" style={{ width: '100%' }}>
                        <Text strong>{`Job ${review.job_id} — ${summaryLine}`}</Text>
                        <Space size={8}>
                            {metricsFallback && <Tag color="gold">Log fallback</Tag>}
                            {baselinePath && (
                                <Tooltip title={baselinePath}>
                                    <Tag color="blue">Baseline: {baselineFile}</Tag>
                                </Tooltip>
                            )}
                        </Space>
                        <div
                            style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                width: '100%',
                            }}
                        >
                            <Text strong>Metrics</Text>
                            <Space size={12}>
                                <a href={statusHref} target="_blank" rel="noopener noreferrer">
                                    Status
                                </a>
                                <a href={logsHref} target="_blank" rel="noopener noreferrer">
                                    Logs
                                </a>
                            </Space>
                        </div>
                        <div
                            style={{
                                display: 'grid',
                                gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                                gap: 12,
                                width: '100%',
                            }}
                        >
                            {(Object.keys(METRIC_CONFIG) as MetricKey[]).map((key) => {
                                const config = METRIC_CONFIG[key];
                                const deltaInfo = formatDeltaValue(deltas?.[key], key);
                                const baselineValue = formatMetricValue(baseline?.[key], key);
                                return (
                                    <div
                                        key={`${review.job_id}-${key}`}
                                        style={{
                                            border: '1px solid rgba(255,255,255,0.1)',
                                            borderRadius: 6,
                                            padding: 10,
                                            background: 'rgba(0,0,0,0.2)',
                                        }}
                                    >
                                        <Text type="secondary">{config.label}</Text>
                                        <div>
                                            <Text strong>{formatMetricValue(summary?.[key], key)}</Text>
                                        </div>
                                        {baselineValue !== '—' && (
                                            <div>
                                                <Text type="secondary">
                                                    Baseline: {baselineValue}
                                                </Text>
                                            </div>
                                        )}
                                        <div>
                                            <Text type={deltaInfo.type}>{deltaInfo.label}</Text>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                        <Collapse
                            size="small"
                            items={[
                                {
                                    key: 'reflection',
                                    label: reflectionLabel,
                                    children: (
                                        <ul style={{ paddingLeft: 18, margin: 0 }}>
                                            {reflection.map((item, idx) => (
                                                <li key={`${review.job_id}-reflection-${idx}`}>{item}</li>
                                            ))}
                                        </ul>
                                    ),
                                },
                            ]}
                        />
                        <Space direction="vertical" size={4} style={{ width: '100%' }}>
                            <Text strong>Suggestions</Text>
                            <pre
                                style={{
                                    margin: 0,
                                    padding: 12,
                                    background: 'rgba(0,0,0,0.3)',
                                    borderRadius: 6,
                                    whiteSpace: 'pre-wrap',
                                }}
                            >
                                {JSON.stringify(changes, null, 2)}
                            </pre>
                            {review.suggestion?.expected_effect && (
                                <Paragraph style={{ marginBottom: 0 }}>
                                    <Text strong>Expected:</Text>{' '}
                                    <Text>{review.suggestion.expected_effect}</Text>
                                </Paragraph>
                            )}
                            {review.suggestion?.risk && (
                                <Paragraph style={{ marginBottom: 0 }}>
                                    <Text strong>Risk:</Text> <Text>{review.suggestion.risk}</Text>
                                </Paragraph>
                            )}
                        </Space>
                        <Space>
                            <Button
                                type="primary"
                                onClick={() => handleDryRun(review)}
                                loading={applyTarget === review.job_id}
                            >
                                Dry-run
                            </Button>
                            <Button onClick={() => handleCopyCurl(review)}>Copy cURL</Button>
                        </Space>
                    </Space>
                </div>
            );
        },
        [applyTarget, handleCopyCurl, handleDryRun],
    );

    const renderMessage = useCallback(
        (item: ChatItem) => {
            if (item.type === 'review') {
                return renderReview(item.review);
            }

            if (item.type === 'status') {
                const color = STATUS_COLORS[item.status] ?? 'blue';
                return (
                    <Space>
                        <Tag color={color}>{item.status}</Tag>
                        <Text>{`Run ${item.jobId}`}</Text>
                    </Space>
                );
            }

            const color = item.type === 'user' ? 'blue' : 'purple';
            return (
                <Space align="start">
                    <Tag color={color}>{item.type}</Tag>
                    <Text style={{ whiteSpace: 'pre-wrap' }}>{item.text}</Text>
                </Space>
            );
        },
        [renderReview],
    );

    const hasActiveRun = Boolean(activeJobRef.current);

    return (
        <Card
            title="Steward Chat"
            extra={
                hasActiveRun ? (
                    <Button danger onClick={() => stopPolling()}>
                        Stop
                    </Button>
                ) : null
            }
            bodyStyle={{ display: 'flex', flexDirection: 'column', gap: 12, height: '100%' }}
            style={{ height: '100%' }}
        >
            <div
                ref={listContainerRef}
                style={{
                    flex: 1,
                    overflowY: 'auto',
                    border: '1px solid var(--color-border-secondary, #333)',
                    borderRadius: 8,
                    padding: 12,
                    background: 'var(--color-bg-elevated, #1f1f1f)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 8,
                }}
            >
                {messages.map((item) => (
                    <div key={item.key}>{renderMessage(item)}</div>
                ))}
            </div>

            <div>
                <TextArea
                    rows={3}
                    placeholder='输入 "review <job_id>" 或直接输入 job_id（少于 40 字符）'
                    value={inputValue}
                    onChange={(event) => setInputValue(event.target.value)}
                    onKeyDown={handleKeyDown}
                    allowClear
                />
            </div>

            <Space align="end">
                <Button type="primary" onClick={() => void handleSend()}>
                    Send
                </Button>
                <Text type="secondary">Ctrl/⌘ + Enter 快速发送</Text>
            </Space>
        </Card>
    );
};

export default StewardChat;
