import React, { useState } from 'react';
import { FlowGraph, EdgeData } from '../components/flowgraph';
import SimpleMermaidTest from '../components/flowgraph/SimpleMermaidTest';
import DebugFlowGraph from '../components/flowgraph/DebugFlowGraph';
import SimpleFlowGraph from '../components/flowgraph/SimpleFlowGraph';

const FlowGraphTestPage: React.FC = () => {
    const [selectedNode, setSelectedNode] = useState<string | null>(null);

    // Mock data for testing
    const mockEdges: EdgeData[] = [
        { src: "main.py::start", dst: "controller.py::init", type: "calls" },
        { src: "controller.py::init", dst: "config.py::load_settings", type: "calls" },
        { src: "controller.py::init", dst: "database.py::connect", type: "calls" },
        { src: "config.py::load_settings", dst: "settings.py::get_config", type: "calls" },
        { src: "database.py::connect", dst: "models.py::User", type: "imports" },
        { src: "models.py::User", dst: "auth.py::authenticate", type: "calls" },
        { src: "auth.py::authenticate", dst: "utils.py::hash_password", type: "calls" },
        { src: "utils.py::hash_password", dst: "crypto.py::sha256", type: "calls" },
        { src: "models.py::User", dst: "models.py::BaseModel", type: "inherits" },
        { src: "auth.py::authenticate", dst: "auth.py::BaseAuth", type: "inherits" }
    ];

    const handleNodeClick = (nodeId: string) => {
        setSelectedNode(nodeId);
        console.log('Node clicked:', nodeId);
    };

    return (
        <div style={{ padding: '20px' }}>
            <h1>FlowGraph Component Test</h1>

            <div style={{ marginBottom: '20px' }}>
                <h2>Test Cases</h2>

                <div style={{ marginBottom: '20px' }}>
                    <h3>Simple Mermaid Test (Basic)</h3>
                    <div style={{ border: '1px solid #e2e8f0', borderRadius: '4px', padding: '10px' }}>
                        <SimpleMermaidTest />
                    </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                    <h3>Debug FlowGraph (With Console Logs)</h3>
                    <DebugFlowGraph edgesJson={mockEdges} />
                </div>
                <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                    <button
                        onClick={() => setSelectedNode(null)}
                        style={{
                            padding: '8px 16px',
                            backgroundColor: selectedNode ? '#e2e8f0' : '#3182ce',
                            color: selectedNode ? '#4a5568' : 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Clear Selection
                    </button>
                </div>

                {selectedNode && (
                    <div style={{
                        padding: '10px',
                        backgroundColor: '#f7fafc',
                        border: '1px solid #e2e8f0',
                        borderRadius: '4px',
                        marginBottom: '20px'
                    }}>
                        <strong>Selected Node:</strong> {selectedNode}
                    </div>
                )}
            </div>

            <div style={{ marginBottom: '20px' }}>
                <h3>Normal Graph (10 nodes) - Simple Version</h3>
                <div style={{ border: '1px solid #e2e8f0', borderRadius: '4px', padding: '10px' }}>
                    <SimpleFlowGraph
                        edgesJson={mockEdges}
                        onNodeClick={handleNodeClick}
                        maxNodes={60}
                    />
                </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
                <h3>Large Graph Test (maxNodes=5) - Simple Version</h3>
                <div style={{ border: '1px solid #e2e8f0', borderRadius: '4px', padding: '10px' }}>
                    <SimpleFlowGraph
                        edgesJson={mockEdges}
                        onNodeClick={handleNodeClick}
                        maxNodes={5}
                    />
                </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
                <h3>Empty Graph Test - Simple Version</h3>
                <div style={{ border: '1px solid #e2e8f0', borderRadius: '4px', padding: '10px' }}>
                    <SimpleFlowGraph
                        edgesJson={[]}
                        onNodeClick={handleNodeClick}
                    />
                </div>
            </div>

            <div style={{ marginBottom: '20px' }}>
                <h3>Edge Types Legend</h3>
                <div style={{ display: 'flex', gap: '20px', flexWrap: 'wrap' }}>
                    <div>
                        <strong>Calls:</strong> <span style={{ color: '#3182ce' }}>→</span> (solid arrow)
                    </div>
                    <div>
                        <strong>Imports:</strong> <span style={{ color: '#3182ce' }}>⟶</span> (dotted arrow)
                    </div>
                    <div>
                        <strong>Inherits:</strong> <span style={{ color: '#3182ce' }}>⟹</span> (thick arrow)
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FlowGraphTestPage;
