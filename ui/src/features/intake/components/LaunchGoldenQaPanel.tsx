/**
 * P0 Founder QA UX — Phase 1 Founder surface.
 *
 * Sole Founder entry for Camry Golden QA / Test Claim Vehicle.
 * Reuses launch-golden-qa APIs; never shows raw tokens or engineering diagnostics.
 * Engineering diagnostics remain on /internal/founder-qa.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Alert, Button, Card, Space, Spin, Typography } from 'antd';
import { Link } from 'react-router-dom';
import {
    getLaunchGoldenQaStatus,
    launchGoldenQa,
    type LaunchGoldenQaStatus,
} from '@/api/inboxTriage';
import { isQaToolsEnabled } from '@/config/productSurface';
import {
    FOUNDER_GOLDEN_QA_SUBTITLE,
    FOUNDER_GOLDEN_QA_TITLE,
    resolveFounderGoldenQaView,
    type FounderGoldenQaSessionProgress,
} from './founderGoldenQaViewModel';

const { Text, Title } = Typography;

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

export function LaunchGoldenQaPanel() {
    const [busy, setBusy] = useState(false);
    const [state, setState] = useState<LaunchGoldenQaStatus | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [sessionProgress, setSessionProgress] = useState<FounderGoldenQaSessionProgress>(null);

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

    const view = useMemo(
        () =>
            resolveFounderGoldenQaView({
                api: state,
                busy,
                sessionProgress,
                hasError: Boolean(error),
            }),
        [state, busy, sessionProgress, error],
    );

    const onLaunch = async () => {
        if (busy) return;
        setBusy(true);
        setError(null);
        setSessionProgress(null);
        setState((prev) =>
            prev
                ? { ...prev, status: 'running_reset', failure_reason: null, ok: undefined }
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
            const prepared = previewPrepared || Boolean(result.preview_prepared);
            // Fail closed: never present Ready without a current Preview.
            setState({
                ...result,
                preview_prepared: prepared,
                status: result.ok ? 'ready_to_scan' : result.status || 'failed',
                ok: result.ok,
                failure_reason:
                    result.ok && !prepared
                        ? result.failure_reason || 'preview_not_prepared'
                        : result.failure_reason,
            });
            if (!result.ok) {
                setError(result.failure_reason || 'launch_failed');
            } else if (!prepared) {
                setError('preview_not_prepared');
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
                preview_prepared: false,
            }));
        } finally {
            setBusy(false);
            void refresh();
        }
    };

    const onPrimary = () => {
        if (!view.primaryAction) return;
        if (view.primaryAction === 'launch') {
            void onLaunch();
            return;
        }
        if (view.primaryAction === 'acknowledge_testing') {
            setSessionProgress('testing');
            return;
        }
        if (view.primaryAction === 'acknowledge_verified') {
            setSessionProgress('verified');
        }
    };

    return (
        <Card
            size="small"
            title={FOUNDER_GOLDEN_QA_TITLE}
            extra={
                <Text type="secondary" style={{ fontSize: 12 }}>
                    Founder test
                </Text>
            }
            data-testid="founder-golden-qa-panel"
        >
            <Space direction="vertical" size={12} style={{ width: '100%' }}>
                <div>
                    <Title level={5} style={{ margin: 0 }}>
                        {FOUNDER_GOLDEN_QA_SUBTITLE}
                    </Title>
                    <Text type="secondary">Current task: {view.currentTask}</Text>
                </div>

                <div data-testid="founder-golden-qa-status" data-state={view.state}>
                    <Text type="secondary">Status: </Text>
                    <Text strong>{view.statusLabel}</Text>
                    <div style={{ marginTop: 4 }}>
                        <Text>{view.statusDetail}</Text>
                    </div>
                </div>

                {view.showQrPlaceholder ? (
                    <div
                        data-testid="founder-golden-qa-qr"
                        style={{
                            border: '1px dashed #bfbfbf',
                            borderRadius: 8,
                            padding: '28px 16px',
                            textAlign: 'center',
                            background: '#fafafa',
                        }}
                    >
                        <Text strong>QR code</Text>
                        <div>
                            <Text type="secondary">
                                Scan with WeChat, then complete the task on your phone.
                            </Text>
                        </div>
                    </div>
                ) : null}

                {view.state === 'blocked' ? (
                    <Alert type="error" showIcon message={view.statusDetail} />
                ) : null}

                {view.state === 'preparing' ? (
                    <div data-testid="founder-golden-qa-preparing" style={{ textAlign: 'center', padding: 8 }}>
                        <Spin />
                    </div>
                ) : null}

                {view.primaryCta ? (
                    <Button
                        type="primary"
                        block
                        onClick={onPrimary}
                        data-testid="founder-golden-qa-primary-cta"
                    >
                        {view.primaryCta}
                    </Button>
                ) : null}

                {isQaToolsEnabled() ? (
                    <Text type="secondary" style={{ fontSize: 12 }}>
                        <Link to="/internal/founder-qa">Engineering QA Console</Link>
                    </Text>
                ) : null}
            </Space>
        </Card>
    );
}
