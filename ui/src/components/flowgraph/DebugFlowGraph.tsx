import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { edgesToMermaid, EdgeData } from './edgesToMermaid';

const DebugFlowGraph: React.FC<{ edgesJson: EdgeData[] }> = ({ edgesJson }) => {
    const mermaidRef = useRef<HTMLDivElement>(null);
    const [debug, setDebug] = useState<string>('');

    useEffect(() => {
        const renderGraph = async () => {
            try {
                console.log('DebugFlowGraph: Starting render...');
                console.log('DebugFlowGraph: edgesJson:', edgesJson);

                // Initialize Mermaid
                mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose'
                });

                // Generate Mermaid string
                const mermaidString = edgesToMermaid(edgesJson, { maxNodes: 10 });
                console.log('DebugFlowGraph: Generated Mermaid string:', mermaidString);
                setDebug(mermaidString);

                if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = '';
                    const graphId = 'debug-graph-' + Date.now();
                    console.log('DebugFlowGraph: Rendering with ID:', graphId);

                    const { svg } = await mermaid.render(graphId, mermaidString);
                    console.log('DebugFlowGraph: Render successful, SVG length:', svg.length);

                    mermaidRef.current.innerHTML = svg;
                }
            } catch (error) {
                console.error('DebugFlowGraph: Render error:', error);
                setDebug(`Error: ${error}`);
                if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = `<div style="color: red;">Error: ${error}</div>`;
                }
            }
        };

        renderGraph();
    }, [edgesJson]);

    return (
        <div style={{ padding: '10px', border: '1px solid #ccc' }}>
            <h4>Debug FlowGraph</h4>
            <div style={{ marginBottom: '10px' }}>
                <strong>Generated Mermaid:</strong>
                <pre style={{ fontSize: '12px', background: '#f5f5f5', padding: '5px' }}>
                    {debug}
                </pre>
            </div>
            <div
                ref={mermaidRef}
                style={{
                    border: '1px solid #ddd',
                    padding: '10px',
                    minHeight: '150px',
                    backgroundColor: '#fafafa'
                }}
            />
        </div>
    );
};

export default DebugFlowGraph;
