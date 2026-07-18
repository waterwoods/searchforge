/**
 * P25 — Launch Golden QA (internal release tool).
 * Visible only when QA Tools are enabled. Never shows raw tokens.
 */
import { useCallback, useEffect, useState } from 'react';
import { Alert, Button, Card, Space, Typography, message } from 'antd';
import {
    getLaunchGoldenQaStatus,
    launchGoldenQa,
    type LaunchGoldenQaStatus,
} from '@/api/inboxTriage';

const { Text } = Typography;

async function applyLocalPreview(query: string): Promise<boolean> {
    try {
        const resp = await fetch('/__qa__/prepare-golden-preview', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query }),
        });
        if (!resp.ok) return false;
        const data = (await resp.json()) as { ok?: boolean };
        return Boolean(data?.ok);
    } catch {
        return false;
    }
}

function statusLabel(status: string | undefined): string {
    switch (status) {
        case 'running_reset':
            return 'Running Reset…';
        case 'preparing_preview':
            return 'Preparing Preview…';
        case 'ready_to_scan':
            return 'Ready to Scan';
        case 'failed':
            return 'Failed';
        case 'idle':
        default:
            return 'Idle';
    }
}

export function LaunchGoldenQaPanel() {
    const [busy, setBusy] = useState(false);
    const [state, setState] = useState<LaunchGoldenQaStatus | null>(null);
    const [error, setError] = useState<string | null>(null);

    const refresh = useCallback(async () => {
        try {
            const s = await getLaunchGoldenQaStatus();
            setState(s);
            setError(null);
        } catch (e) {
            const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            setError(String(detail || (e as Error)?.message || 'status_unavailable'));
        }
    }, []);

    useEffect(() => {
        void refresh();
    }, [refresh]);

    const onLaunch = async () => {
        if (busy) return;
        setBusy(true);
        setError(null);
        setState((prev) =>
            prev
                ? { ...prev, status: 'running_reset', failure_reason: null }
                : { status: 'running_reset', ok: true, enabled: true },
        );
        try {
            const result = await launchGoldenQa({ target: 'qa', prepare_preview: true });
            let previewPrepared = Boolean(result.preview_prepared);
            if (!previewPrepared && result.devtools_launch_query && import.meta.env.DEV) {
                setState((prev) =>
                    prev
                        ? { ...prev, status: 'preparing_preview' }
                        : { status: 'preparing_preview', ok: true, enabled: true },
                );
                previewPrepared = await applyLocalPreview(result.devtools_launch_query);
            }
            setState({
                ...result,
                preview_prepared: previewPrepared || Boolean(result.preview_prepared),
                status: result.ok ? 'ready_to_scan' : result.status || 'failed',
            });
            if (result.ok) {
                message.success(
                    previewPrepared || result.preview_prepared
                        ? 'Golden QA ready — open DevTools Preview and scan once'
                        : 'Golden reset ready — Preview inject needs local DevTools host',
                );
            } else {
                setError(result.failure_reason || 'launch_failed');
            }
        } catch (e) {
            const detail = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
            const reason = String(detail || (e as Error)?.message || 'launch_failed');
            setError(reason);
            setState((prev) => ({
                ...(prev || { enabled: true }),
                ok: false,
                status: 'failed',
                failure_reason: reason,
            }));
        } finally {
            setBusy(false);
            void refresh();
        }
    };

    return (
        <Card
            size="small"
            title="QA Tools"
            extra={<Text type="secondary" style={{ fontSize: 12 }}>Internal · Founder release</Text>}
        >
            <Space direction="vertical" size={10} style={{ width: '100%' }}>
                <Button type="primary" onClick={() => void onLaunch()} loading={busy} disabled={busy}>
                    Launch Golden QA
                </Button>
                <div>
                    <Text type="secondary">Status: </Text>
                    <Text strong>{statusLabel(state?.status)}</Text>
                </div>
                {state?.case_id ? (
                    <div>
                        <Text type="secondary">Latest Case ID: </Text>
                        <Text code>{state.case_id}</Text>
                    </div>
                ) : null}
                {state?.expires_at ? (
                    <div>
                        <Text type="secondary">Token expiration: </Text>
                        <Text>{state.expires_at}</Text>
                    </div>
                ) : null}
                {state?.last_run_utc ? (
                    <div>
                        <Text type="secondary">Last run: </Text>
                        <Text>{state.last_run_utc}</Text>
                    </div>
                ) : null}
                {state?.preview_prepared ? (
                    <Alert
                        type="success"
                        showIcon
                        message="Preview prepared"
                        description={
                            state.devtools_hint ||
                            'DevTools → compile mode「pages/entry/entry (Golden QA session)」→ 清缓存 → Preview → scan once'
                        }
                    />
                ) : state?.status === 'ready_to_scan' ? (
                    <Alert
                        type="warning"
                        showIcon
                        message="Reset ready — inject Preview on your laptop"
                        description={
                            state.devtools_hint ||
                            'Cloud Run cannot update WeChat DevTools. Run on this machine: bash scripts/launch_golden_qa.sh --qa — then 清缓存 → Preview. Stale compile tokens return case_not_found (404).'
                        }
                    />
                ) : null}
                {state?.report_relpath ? (
                    <div>
                        <Text type="secondary">Latest QA report: </Text>
                        <Text code style={{ fontSize: 12 }}>
                            {state.report_relpath}
                        </Text>
                    </div>
                ) : null}
                {(error || state?.failure_reason) && state?.status === 'failed' ? (
                    <Alert type="error" showIcon message="Launch failed" description={error || state?.failure_reason} />
                ) : null}
                {state?.failure_reason && state?.status === 'ready_to_scan' && !state.preview_prepared ? (
                    <Alert type="warning" showIcon message="Preview note" description={state.failure_reason} />
                ) : null}
                {state?.enabled === false ? (
                    <Alert
                        type="warning"
                        showIcon
                        message="Launch disabled on this API"
                        description="Set ENABLE_GOLDEN_QA_LAUNCH=1 on the backend for QA."
                    />
                ) : null}
            </Space>
        </Card>
    );
}
