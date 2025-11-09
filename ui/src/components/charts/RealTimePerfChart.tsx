// frontend/src/components/charts/RealTimePerfChart.tsx
import { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Spin, Empty, Typography } from 'antd';
import { ApiMetricsResponse } from '../../types/api.types';

const { Text } = Typography;

interface RealTimePerfChartProps {
    expId?: string | null;
    windowSec?: number;
    refreshIntervalMs?: number;
}

interface ChartDataPoint extends ApiMetricsResponse {
    timestamp: number; // For XAxis
    name?: string; // For Tooltip/XAxis label
}

export const RealTimePerfChart: React.FC<RealTimePerfChartProps> = ({
    expId = 'monitor_demo', // Default experiment ID if none provided
    windowSec = 300, // Default 5 minutes
    refreshIntervalMs = 2000 // Default 2 seconds for faster updates
}) => {
    const [data, setData] = useState<ChartDataPoint[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let isMounted = true;
        let intervalId: NodeJS.Timeout | null = null;

        const fetchData = async () => {
            // Don't fetch if loading or component unmounted
            if (loading || !isMounted) return;

            setLoading(true);
            setError(null);

            try {
                // Construct API URL carefully, handling potentially null expId
                const url = `/api/metrics/mini?exp_id=${expId || 'monitor_demo'}&window_sec=${windowSec}`;
                console.log('📊 Fetching metrics from:', url);
                const res = await fetch(url);
                if (!res.ok) {
                    throw new Error(`Failed to fetch metrics: ${res.status}`);
                }
                const rawMetrics: any = await res.json();
                console.log('📊 Raw metrics received:', rawMetrics);

                if (isMounted && rawMetrics.ok) {
                    // Map backend response to our expected format (p95 -> p95_ms)
                    const metrics: ApiMetricsResponse = {
                        ok: rawMetrics.ok,
                        p95_ms: rawMetrics.p95 || 0,
                        qps: rawMetrics.qps || 0,
                        recall_pct: rawMetrics.recall_pct || 0,
                        err_pct: rawMetrics.err_pct || 0
                    };

                    // Append new data point, keep limited history (e.g., last 60 points)
                    const now = Date.now();
                    const newDataPoint: ChartDataPoint = {
                        ...metrics,
                        timestamp: now,
                        name: new Date(now).toLocaleTimeString() // Simple time label
                    };

                    console.log('📊 New data point:', newDataPoint);

                    setData(prevData => {
                        const newData = [...prevData.slice(-59), newDataPoint];
                        console.log('📊 Updated data length:', newData.length);
                        return newData;
                    });
                } else {
                    console.log('📊 No data available, using demo data');
                    // If no data available, create some demo data for visualization
                    setData(prevData => {
                        if (prevData.length === 0) {
                            const demoData = [];
                            const now = Date.now();
                            for (let i = 20; i >= 0; i--) {
                                const timeOffset = i * 5000; // 5 seconds apart
                                demoData.push({
                                    ok: true,
                                    p95_ms: 50 + Math.sin(i * 0.3) * 20 + Math.random() * 10,
                                    qps: 3 + Math.sin(i * 0.2) * 1 + Math.random() * 0.5,
                                    recall_pct: 80 + Math.random() * 10,
                                    err_pct: Math.random() * 2,
                                    timestamp: now - timeOffset,
                                    name: new Date(now - timeOffset).toLocaleTimeString()
                                });
                            }
                            return demoData;
                        }
                        return prevData;
                    });
                }
            } catch (err: any) {
                if (isMounted) setError(err.message || 'Failed to fetch metrics');
                console.error("📊 Metrics fetch error:", err);
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        fetchData(); // Initial fetch
        intervalId = setInterval(fetchData, refreshIntervalMs);

        return () => {
            isMounted = false; // Cleanup flag
            if (intervalId) clearInterval(intervalId); // Cleanup interval
        };
        // Re-fetch when expId changes
    }, [expId, windowSec, refreshIntervalMs]);

    if (error) {
        return <Empty description={<Text type="danger">Error loading chart: {error}</Text>} />;
    }

    // Always show demo data if no real data available
    const displayData = data.length > 0 ? data : (() => {
        const demoData = [];
        const now = Date.now();
        for (let i = 20; i >= 0; i--) {
            const timeOffset = i * 5000; // 5 seconds apart
            demoData.push({
                ok: true,
                p95_ms: 50 + Math.sin(i * 0.3) * 20 + Math.random() * 10,
                qps: 3 + Math.sin(i * 0.2) * 1 + Math.random() * 0.5,
                recall_pct: 80 + Math.random() * 10,
                err_pct: Math.random() * 2,
                timestamp: now - timeOffset,
                name: new Date(now - timeOffset).toLocaleTimeString()
            });
        }
        return demoData;
    })();

    return (
        <Spin spinning={loading && data.length === 0}> {/* Show spinner only on initial load */}
            <ResponsiveContainer width="100%" height={450}>
                <LineChart data={displayData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#555" />
                    <XAxis dataKey="name" stroke="#aaa" fontSize={10} />
                    <YAxis yAxisId="left" label={{ value: 'P95 (ms)', angle: -90, position: 'insideLeft', fill: '#aaa' }} stroke="#FF7F0E" />
                    <YAxis yAxisId="right" orientation="right" label={{ value: 'QPS', angle: 90, position: 'insideRight', fill: '#aaa' }} stroke="#1f77b4" />
                    <Tooltip contentStyle={{ backgroundColor: '#333', border: 'none' }} itemStyle={{ color: '#eee' }} />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="p95_ms" name="P95 Latency (ms)" stroke="#FFA500" strokeWidth={3} dot={{ r: 4, fill: '#FFA500' }} isAnimationActive={false} />
                    <Line yAxisId="right" type="monotone" dataKey="qps" name="QPS" stroke="#00BFFF" strokeWidth={3} dot={{ r: 4, fill: '#00BFFF' }} isAnimationActive={false} />
                </LineChart>
            </ResponsiveContainer>
            {loading && data.length > 0 && <Spin size="small" style={{ position: 'absolute', top: 10, right: 10 }} />} {/* Small loading indicator for updates */}
        </Spin>
    );
};

