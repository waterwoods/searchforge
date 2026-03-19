import { useState, useEffect } from 'react';
import { Card, Typography, Tag, Space } from 'antd';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getLatestVitals, type VitalsReading } from '../api/vitals';

const { Title, Text } = Typography;

interface ChartDataPoint {
    time: string; // HH:mm:ss
    hr: number;
    spo2: number;
    timestamp: number; // For sorting
}

/**
 * Generate sample data for offline/demo mode
 */
function generateSampleData(): ChartDataPoint[] {
    const now = Date.now();
    const data: ChartDataPoint[] = [];
    
    // Generate 12 data points (1 minute, 5 seconds apart)
    for (let i = 11; i >= 0; i--) {
        const timeOffset = i * 5000; // 5 seconds apart
        const timestamp = now - timeOffset;
        const date = new Date(timestamp);
        
        data.push({
            time: date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
            hr: Math.round(70 + Math.sin(i * 0.3) * 5 + Math.random() * 3),
            spo2: Math.round(96 + Math.sin(i * 0.2) * 2 + Math.random() * 1),
            timestamp,
        });
    }
    
    return data.sort((a, b) => a.timestamp - b.timestamp);
}

/**
 * Convert readings to chart data format
 */
function readingsToChartData(readings: VitalsReading[]): ChartDataPoint[] {
    return readings
        .map((r) => {
            // Use time_str if available, otherwise use created_at
            const timeStr = r.time_str || r.created_at;
            let date: Date;
            
            if (r.time_ms) {
                date = new Date(r.time_ms);
            } else if (timeStr) {
                date = new Date(timeStr);
            } else {
                date = new Date(r.created_at);
            }
            
            return {
                time: date.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }),
                hr: Math.round(r.hr),
                spo2: Math.round(r.spo2),
                timestamp: date.getTime(),
            };
        })
        .sort((a, b) => a.timestamp - b.timestamp);
}

/**
 * Get SpO2 color based on value
 */
function getSpO2Color(spo2: number): string {
    if (spo2 >= 95) return '#52c41a'; // green
    if (spo2 >= 90) return '#fa8c16'; // orange
    return '#ff4d4f'; // red
}

export default function VitalsDashboardPage() {
    const [readings, setReadings] = useState<VitalsReading[]>([]);
    const [isOffline, setIsOffline] = useState(false);
    const [currentTime, setCurrentTime] = useState(new Date());

    // Update current time every second
    useEffect(() => {
        const timeInterval = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);
        return () => clearInterval(timeInterval);
    }, []);

    // Fetch vitals data every 2 seconds
    useEffect(() => {
        let isMounted = true;
        let intervalId: NodeJS.Timeout | null = null;

        const fetchData = async () => {
            try {
                const response = await getLatestVitals(60);
                if (isMounted) {
                    setReadings(response.readings);
                    setIsOffline(false);
                }
            } catch (error) {
                console.error('Failed to fetch vitals:', error);
                if (isMounted) {
                    setIsOffline(true);
                    // Use sample data when offline
                    if (readings.length === 0) {
                        // Generate sample readings from chart data
                        const sampleChartData = generateSampleData();
                        const sampleReadings: VitalsReading[] = sampleChartData.map((d, i) => ({
                            id: i + 1,
                            source: 'sample',
                            hr: d.hr,
                            spo2: d.spo2,
                            time_ms: d.timestamp,
                            time_str: new Date(d.timestamp).toISOString(),
                            created_at: new Date(d.timestamp).toISOString(),
                        }));
                        setReadings(sampleReadings);
                    }
                }
            }
        };

        fetchData(); // Initial fetch
        intervalId = setInterval(fetchData, 2000); // Refresh every 2 seconds

        return () => {
            isMounted = false;
            if (intervalId) clearInterval(intervalId);
        };
    }, []);

    // Get latest reading
    const latest = readings.length > 0 ? readings[0] : null;
    
    // Prepare chart data
    const chartData = readings.length > 0 
        ? readingsToChartData(readings) 
        : generateSampleData();

    // Format latest reading time
    const latestTimeStr = latest
        ? (latest.time_str 
            ? new Date(latest.time_str).toLocaleString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            })
            : new Date(latest.created_at).toLocaleString('en-US', { 
                month: 'short', 
                day: 'numeric', 
                hour: '2-digit', 
                minute: '2-digit', 
                second: '2-digit' 
            }))
        : 'No data';

    return (
        <div
            style={{
                minHeight: '100vh',
                backgroundColor: '#f5f5f5',
                padding: '24px',
                boxSizing: 'border-box',
                color: '#000',
            }}
        >
            {/* Header */}
            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '32px',
                }}
            >
                <Title level={2} style={{ margin: 0, color: '#000' }}>
                    Vitals Monitor / 生命体征监控
                </Title>
                <Space>
                    {isOffline && (
                        <Tag color="orange">Offline — showing sample data</Tag>
                    )}
                    <Text type="secondary" style={{ fontSize: '14px' }}>
                        {currentTime.toLocaleTimeString('en-US', { 
                            hour12: false, 
                            hour: '2-digit', 
                            minute: '2-digit', 
                            second: '2-digit' 
                        })}
                    </Text>
                </Space>
            </div>

            {/* Main Cards: HR and SpO2 */}
            <div
                style={{
                    display: 'flex',
                    gap: '24px',
                    marginBottom: '32px',
                    flexWrap: 'wrap',
                }}
            >
                {/* Heart Rate Card */}
                <Card
                    style={{
                        flex: '1 1 300px',
                        minWidth: '300px',
                        borderRadius: '8px',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    }}
                    bodyStyle={{ padding: '32px' }}
                >
                    <div style={{ textAlign: 'center' }}>
                        <Text
                            type="secondary"
                            style={{
                                fontSize: '16px',
                                display: 'block',
                                marginBottom: '16px',
                            }}
                        >
                            Heart Rate (bpm)
                        </Text>
                        <Title
                            level={1}
                            style={{
                                fontSize: '64px',
                                margin: '0 0 16px 0',
                                color: '#1890ff',
                            }}
                        >
                            {latest ? Math.round(latest.hr) : '--'}
                        </Title>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                            Last reading: {latestTimeStr}
                        </Text>
                    </div>
                </Card>

                {/* SpO2 Card */}
                <Card
                    style={{
                        flex: '1 1 300px',
                        minWidth: '300px',
                        borderRadius: '8px',
                        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                    }}
                    bodyStyle={{ padding: '32px' }}
                >
                    <div style={{ textAlign: 'center' }}>
                        <Text
                            type="secondary"
                            style={{
                                fontSize: '16px',
                                display: 'block',
                                marginBottom: '16px',
                            }}
                        >
                            SpO₂ (%)
                        </Text>
                        <Title
                            level={1}
                            style={{
                                fontSize: '64px',
                                margin: '0 0 16px 0',
                                color: latest ? getSpO2Color(latest.spo2) : '#666',
                            }}
                        >
                            {latest ? Math.round(latest.spo2) : '--'}
                        </Title>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                            Last reading: {latestTimeStr}
                        </Text>
                    </div>
                </Card>
            </div>

            {/* Chart Card */}
            <Card
                style={{
                    borderRadius: '8px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                }}
                bodyStyle={{ padding: '24px' }}
            >
                <Title level={4} style={{ marginBottom: '24px' }}>
                    Historical Trends
                </Title>
                <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0" />
                        <XAxis 
                            dataKey="time" 
                            stroke="#666" 
                            fontSize={12}
                            angle={-45}
                            textAnchor="end"
                            height={60}
                        />
                        <YAxis 
                            yAxisId="left"
                            label={{ value: 'HR (bpm)', angle: -90, position: 'insideLeft', fill: '#666' }}
                            stroke="#1890ff"
                            domain={['dataMin - 10', 'dataMax + 10']}
                        />
                        <YAxis 
                            yAxisId="right"
                            orientation="right"
                            label={{ value: 'SpO₂ (%)', angle: 90, position: 'insideRight', fill: '#666' }}
                            stroke="#52c41a"
                            domain={[85, 100]}
                        />
                        <Tooltip 
                            contentStyle={{ 
                                backgroundColor: '#fff', 
                                border: '1px solid #e0e0e0',
                                borderRadius: '4px',
                            }} 
                        />
                        <Legend />
                        <Line 
                            yAxisId="left"
                            type="monotone" 
                            dataKey="hr" 
                            name="Heart Rate (bpm)" 
                            stroke="#1890ff" 
                            strokeWidth={3} 
                            dot={{ r: 4, fill: '#1890ff' }} 
                            isAnimationActive={false}
                        />
                        <Line 
                            yAxisId="right"
                            type="monotone" 
                            dataKey="spo2" 
                            name="SpO₂ (%)" 
                            stroke="#52c41a" 
                            strokeWidth={3} 
                            dot={{ r: 4, fill: '#52c41a' }} 
                            isAnimationActive={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </Card>
        </div>
    );
}
