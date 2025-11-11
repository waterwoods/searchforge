// frontend/src/components/kpi/KpiBar.tsx
import { Col, Row, Statistic, Typography } from 'antd';
import { useAppStore } from '../../store/useAppStore';

const { Text } = Typography;

// Get the baseline "Before" values (we know them from the store definition)
const BASELINE_P95 = 120.4;
const BASELINE_RECALL = 82.0;

export const KpiBar = () => {
    const { currentMetrics } = useAppStore();

    const isAfterState = currentMetrics.p95_ms < 100; // Simple check for "After"

    const p95Color = currentMetrics.p95_ms > 100 ? '#cf1322' : '#3f8600';
    const recallColor = currentMetrics.recall_pct < 90 ? '#cf1322' : '#3f8600';

    return (
        <Row gutter={32} style={{ width: '100%' }} align="middle">
            <Col>
                <Statistic
                    title="P95 Latency"
                    value={currentMetrics.p95_ms}
                    precision={0}
                    suffix="ms"
                    valueStyle={{ color: p95Color }}
                />
                {isAfterState && (
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                        (vs {BASELINE_P95.toFixed(0)} ms)
                    </Text>
                )}
            </Col>
            <Col>
                <Statistic
                    title="Recall"
                    value={currentMetrics.recall_pct}
                    precision={1}
                    suffix="%"
                    valueStyle={{ color: recallColor }}
                />
                {isAfterState && (
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                        (vs {BASELINE_RECALL.toFixed(1)} %)
                    </Text>
                )}
            </Col>
            <Col>
                <Statistic
                    title="QPS"
                    value={currentMetrics.qps}
                    precision={1}
                />
            </Col>
        </Row>
    );
};
