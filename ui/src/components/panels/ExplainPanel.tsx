// frontend/src/components/panels/ExplainPanel.tsx
import { useEffect, useState } from 'react';
import { Empty, Spin, Timeline, Typography } from 'antd';
import { useAppStore } from '../../store/useAppStore';
import { ApiTraceResponse } from '../../types/api.types';

const { Text } = Typography;

export const ExplainPanel = () => {
    const { currentTraceId } = useAppStore();
    const [trace, setTrace] = useState<ApiTraceResponse | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (!currentTraceId) {
            setTrace(null);
            return;
        }

        setIsLoading(true);
        fetch(`/api/traces/${currentTraceId}`)
            .then((res) => res.json())
            .then((data: ApiTraceResponse) => setTrace(data))
            .catch((err) => console.error("Failed to fetch trace:", err))
            .finally(() => setIsLoading(false));
    }, [currentTraceId]); // This effect re-runs when currentTraceId changes

    if (isLoading) {
        return <Spin />;
    }

    if (!trace) {
        return <Empty description="Run a query to see its trace" />;
    }

    return (
        <div>
            <Text strong>Total Latency: {trace.total_ms.toFixed(1)} ms</Text>
            <Timeline style={{ marginTop: '20px' }}>
                {trace.stages.map((stage) => (
                    <Timeline.Item key={stage.stage_name}>
                        <Text strong>{stage.stage_name}:</Text>{' '}
                        <Text
                            type={stage.duration_ms > 80 ? 'danger' : undefined}
                        >
                            {stage.duration_ms.toFixed(1)} ms
                        </Text>
                    </Timeline.Item>
                ))}
            </Timeline>
        </div>
    );
};




































