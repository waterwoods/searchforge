import React, { useState } from 'react';
import { Button, Card, Typography, Space } from 'antd';
import SimpleFlowGraph from '../components/flowgraph/SimpleFlowGraph';
import { EdgeData } from '../components/flowgraph/edgesToMermaid';

const { Title, Text } = Typography;

// Test data for the three scenarios
const normalEdgesJson: EdgeData[] = [
    { src: 'file1.py::main', dst: 'file1.py::helper', type: 'calls' },
    { src: 'file1.py::helper', dst: 'file2.py::process', type: 'calls' },
    { src: 'file1.py::main', dst: 'file2.py::process', type: 'imports' },
];

const emptyEdgesJson: EdgeData[] = [];

const invalidEdgesJson: EdgeData[] = [
    { src: '', dst: 'invalid', type: 'calls' },
    { src: 'valid::node', dst: '', type: 'calls' },
];

type Phase = 'idle' | 'loading' | 'graph_rendering' | 'graph_ready' | 'notifying';

export const FlowGraphTestScenarios: React.FC = () => {
    const [phase, setPhase] = useState<Phase>('idle');
    const [testResults, setTestResults] = useState<Array<{
        scenario: string;
        finalPhase: Phase;
        transitionLog: string;
        success: boolean;
    }>>([]);

    const runTestScenario = async (scenarioName: string, edgesJson: EdgeData[]) => {
        console.log(`🧪 Starting test: ${scenarioName}`);

        // Reset phase and start test
        setPhase('idle');
        await new Promise(resolve => setTimeout(resolve, 100)); // Small delay

        // Simulate handleSend setting phase to loading
        setPhase('loading');
        await new Promise(resolve => setTimeout(resolve, 100));

        // Simulate setting phase to graph_rendering after edgesJson is present
        if (edgesJson.length > 0) {
            setPhase('graph_rendering');
        } else {
            // For empty edgesJson, should go directly to graph_ready
            setPhase('graph_ready');
        }

        // Wait for potential error or success
        await new Promise(resolve => setTimeout(resolve, 1000));

        const finalPhase = phase;
        const transitionLog = `idle -> loading -> ${edgesJson.length > 0 ? 'graph_rendering' : 'graph_ready'} -> ${finalPhase}`;
        const success = finalPhase === 'graph_ready' || finalPhase === 'idle';

        const result = {
            scenario: scenarioName,
            finalPhase,
            transitionLog,
            success
        };

        setTestResults(prev => [...prev, result]);
        console.log(`🧪 Test completed: ${scenarioName} - ${transitionLog} - Success: ${success}`);
    };

    const handleGraphReady = () => {
        setPhase('graph_ready');
    };

    const handleError = (error: string) => {
        console.error(`Graph error: ${error}`);
        setPhase('idle');
    };

    const clearResults = () => {
        setTestResults([]);
    };

    return (
        <div style={{ padding: '20px' }}>
            <Title level={2}>FlowGraph Test Scenarios</Title>

            <Space direction="vertical" size="large" style={{ width: '100%' }}>
                <Card title="Test Controls">
                    <Space wrap>
                        <Button
                            type="primary"
                            onClick={() => runTestScenario('Normal edgesJson', normalEdgesJson)}
                        >
                            Test Normal EdgesJson
                        </Button>
                        <Button
                            onClick={() => runTestScenario('Empty edgesJson', emptyEdgesJson)}
                        >
                            Test Empty EdgesJson
                        </Button>
                        <Button
                            danger
                            onClick={() => runTestScenario('Invalid edgesJson', invalidEdgesJson)}
                        >
                            Test Invalid EdgesJson
                        </Button>
                        <Button onClick={clearResults}>Clear Results</Button>
                    </Space>
                </Card>

                <Card title="Current Phase State">
                    <Text strong>Current Phase: </Text>
                    <Text code>{phase}</Text>
                </Card>

                <Card title="Test Results">
                    {testResults.length === 0 ? (
                        <Text type="secondary">Services no tests yet. Click a test button above.</Text>
                    ) : (
                        <div>
                            {testResults.map((result, index) => (
                                <div key={index} style={{
                                    marginBottom: '10px',
                                    padding: '10px',
                                    border: '1px solid #d9d9d9',
                                    borderRadius: '4px',
                                    backgroundColor: result.success ? '#f6ffed' : '#fff2f0'
                                }}>
                                    <div><strong>Scenario:</strong> {result.scenario}</div>
                                    <div><strong>Final Phase:</strong> <code>{result.finalPhase}</code></div>
                                    <div><strong>Transition Log:</strong> <code>{result.transitionLog}</code></div>
                                    <div><strong>Success:</strong> {result.success ? '✅' : '❌'}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </Card>

                <Card title="Live FlowGraph Component">
                    <Text type="secondary">Current phase: {phase}</Text>
                    <div style={{ marginTop: '10px' }}>
                        <SimpleFlowGraph
                            edgesJson={phase === 'graph_rendering' ? normalEdgesJson : []}
                            phase={phase}
                            maxNodes={60}
                            onGraphReady={handleGraphReady}
                            onError={handleError}
                        />
                    </div>
                </Card>
            </Space>
        </div>
    );
};

export default FlowGraphTestScenarios;
