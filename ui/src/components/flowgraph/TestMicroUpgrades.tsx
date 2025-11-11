import React, { useState } from 'react';
import { Card, Button } from 'antd';
import { edgesToMermaid, EdgeData } from './edgesToMermaid';

const TestMicroUpgrades: React.FC = () => {
    const [showHighlighting, setShowHighlighting] = useState(false);

    // Test data with entry nodes and main path
    const testEdges: EdgeData[] = [
        { src: "main.py::main", dst: "app.py::start", type: "calls" },
        { src: "app.py::start", dst: "config.py::init", type: "calls" },
        { src: "app.py::start", dst: "database.py::connect", type: "calls" },
        { src: "config.py::init", dst: "settings.py::load", type: "calls" },
        { src: "database.py::connect", dst: "models.py::User", type: "imports" },
        { src: "models.py::User", dst: "auth.py::authenticate", type: "calls" },
        { src: "auth.py::authenticate", dst: "utils.py::hash_password", type: "calls" },
        { src: "utils.py::hash_password", dst: "crypto.py::sha256", type: "calls" }
    ];

    const mermaidString = edgesToMermaid(testEdges, { maxNodes: 10 });

    return (
        <div style={{ padding: '20px' }}>
            <h3>Micro-Upgrades Test</h3>

            <div style={{ marginBottom: '20px' }}>
                <Button
                    onClick={() => setShowHighlighting(!showHighlighting)}
                    type={showHighlighting ? 'primary' : 'default'}
                >
                    {showHighlighting ? 'Hide' : 'Show'} Entry Node Highlighting
                </Button>
            </div>

            <Card title="Generated Mermaid with Highlighting" size="small">
                <pre style={{
                    fontSize: '12px',
                    backgroundColor: '#f5f5f5',
                    padding: '10px',
                    borderRadius: '4px',
                    maxHeight: '300px',
                    overflow: 'auto'
                }}>
                    {mermaidString}
                </pre>
            </Card>

            <div style={{ marginTop: '20px', fontSize: '12px', color: '#666' }}>
                <h4>Expected Highlights:</h4>
                <ul>
                    <li><strong>Entry Nodes</strong> (main, start, init): Blue background (#e6f7ff)</li>
                    <li><strong>Main Path Nodes</strong> (most connected): Green background (#f6ffed)</li>
                    <li><strong>Regular Nodes</strong>: Default styling</li>
                </ul>
            </div>
        </div>
    );
};

export default TestMicroUpgrades;
