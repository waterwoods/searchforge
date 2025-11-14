import { useCallback, useEffect, useMemo, useState } from 'react';
import { Button, Card, Space, Typography, Spin, Alert, Tooltip } from 'antd';

type StewardResponse = {
    job_id: string;
    plan?: string;
    dryrun_status?: string;
    errors?: string[];
    obs_url?: string;
    trace_id?: string;
};

const STORAGE_KEY = 'steward:lastJobId';

const generateJobId = () => `demo-ui-${Date.now()}`;

const getStoredJobId = () => {
    if (typeof window === 'undefined') {
        return null;
    }
    return window.localStorage.getItem(STORAGE_KEY);
};

const setStoredJobId = (jobId: string) => {
    if (typeof window === 'undefined') {
        return;
    }
    window.localStorage.setItem(STORAGE_KEY, jobId);
};

const fallbackObsUrl = (traceId?: string) => {
    const host = import.meta.env.VITE_LANGFUSE_HOST?.replace(/\/+$/, '') ?? '';
    const proj = import.meta.env.VITE_LANGFUSE_PROJECT_ID ?? '';
    if (!host || !proj || !traceId) {
        return '';
    }
    return `${host}/project/${proj}/traces?query=${encodeURIComponent(traceId)}`;
};

export const RunStewardCard = () => {
    const [jobId, setJobId] = useState<string>(() => getStoredJobId() ?? generateJobId());
    const [isLoading, setIsLoading] = useState(false);
    const [response, setResponse] = useState<StewardResponse | null>(null);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    useEffect(() => {
        setStoredJobId(jobId);
    }, [jobId]);

    const requestBody = useMemo(
        () =>
            JSON.stringify({
                job_id: jobId,
            }),
        [jobId]
    );

    const handleRun = useCallback(async () => {
        setIsLoading(true);
        setErrorMessage(null);
        try {
            const res = await fetch('/api/steward/run', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: requestBody,
            });

            if (!res.ok) {
                throw new Error(`Request failed with status ${res.status}`);
            }

            const data: StewardResponse = await res.json();
            setResponse(data);
            if (data.job_id) {
                setJobId(data.job_id);
            }
        } catch (err) {
            setErrorMessage(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setIsLoading(false);
        }
    }, [requestBody]);

    const handleNewJob = () => {
        const nextJob = generateJobId();
        setJobId(nextJob);
        setResponse(null);
    };

    return (
        <Card
            title="Steward Dry-Run"
            extra={
                <Space size="small">
                    <Typography.Text type="secondary">Job:</Typography.Text>
                    <Typography.Text code>{jobId}</Typography.Text>
                    <Button size="small" onClick={handleNewJob}>
                        New ID
                    </Button>
                </Space>
            }
        >
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Button type="primary" onClick={handleRun} loading={isLoading}>
                    Run Steward
                </Button>

                <Spin spinning={isLoading}>
                    {errorMessage && (
                        <Alert type="error" showIcon message="Request failed" description={errorMessage} />
                    )}

                    {response && (
                        <Card size="small" type="inner" title="Latest Response">
                            <Space direction="vertical" style={{ width: '100%' }}>
                                {response.plan && (
                                    <Typography.Paragraph>
                                        <Typography.Text strong>Plan: </Typography.Text>
                                        {response.plan}
                                    </Typography.Paragraph>
                                )}
                                {response.dryrun_status && (
                                    <Typography.Paragraph>
                                        <Typography.Text strong>Dryrun Status: </Typography.Text>
                                        {response.dryrun_status}
                                    </Typography.Paragraph>
                                )}
                                {response.errors && response.errors.length > 0 ? (
                                    <Alert
                                        type="warning"
                                        showIcon
                                        message="Errors"
                                        description={
                                            <ul style={{ paddingLeft: 16, margin: 0 }}>
                                                {response.errors.map((msg, idx) => (
                                                    <li key={idx}>
                                                        <Typography.Text type="warning">{msg}</Typography.Text>
                                                    </li>
                                                ))}
                                            </ul>
                                        }
                                    />
                                ) : (
                                    <Typography.Paragraph>
                                        <Typography.Text strong>Errors: </Typography.Text>
                                        <Typography.Text type="secondary">[]</Typography.Text>
                                    </Typography.Paragraph>
                                )}
                                {(() => {
                                    const obsUrl = response?.obs_url || fallbackObsUrl(response?.trace_id);
                                    const tooltipTitle = obsUrl ? 'Open in Langfuse' : 'trace pending';
                                    const handleOpen = () => {
                                        if (obsUrl) {
                                            window.open(obsUrl, '_blank', 'noopener');
                                        }
                                    };
                                    return (
                                        <Tooltip title={tooltipTitle}>
                                            <span>
                                                <Button type="link" disabled={!obsUrl} onClick={handleOpen}>
                                                    Open in Langfuse
                                                </Button>
                                            </span>
                                        </Tooltip>
                                    );
                                })()}
                                <Typography.Paragraph>
                                    <Typography.Text strong>Raw JSON</Typography.Text>
                                </Typography.Paragraph>
                                <pre
                                    style={{
                                        background: '#111',
                                        padding: '12px',
                                        borderRadius: 8,
                                        overflowX: 'auto',
                                        margin: 0,
                                    }}
                                >
                                    {JSON.stringify(response, null, 2)}
                                </pre>
                            </Space>
                        </Card>
                    )}
                </Spin>
            </Space>
        </Card>
    );
};


