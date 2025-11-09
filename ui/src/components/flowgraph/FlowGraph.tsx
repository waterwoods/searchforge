import React, { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';
import { edgesToMermaid, EdgeData, getFullNodeId } from './edgesToMermaid';

export interface FlowGraphProps {
    edgesJson: EdgeData[];
    maxNodes?: number;
    onNodeClick?: (nodeId: string) => void;
    className?: string;
}

interface FlowGraphState {
    status: 'loading' | 'success' | 'error';
    error?: string;
    mermaidString?: string;
}

const FlowGraph: React.FC<FlowGraphProps> = ({
    edgesJson,
    maxNodes = 60,
    onNodeClick,
    className = ''
}) => {
    const mermaidRef = useRef<HTMLDivElement>(null);
    const [state, setState] = useState<FlowGraphState>({ status: 'loading' });
    const [retryCount, setRetryCount] = useState(0);

    // Initialize Mermaid
    useEffect(() => {
        mermaid.initialize({
            startOnLoad: false,
            theme: 'default',
            securityLevel: 'loose',
            flowchart: {
                useMaxWidth: true,
                htmlLabels: true
            }
        });
    }, []);

    // Generate Mermaid string and render
    const renderGraph = useCallback(async () => {
        if (!mermaidRef.current) return;

        try {
            setState({ status: 'loading' });

            // Generate Mermaid string
            const mermaidString = edgesToMermaid(edgesJson, { maxNodes });

            // Create unique ID for this render
            const graphId = `flowgraph-${Date.now()}-${retryCount}`;

            // Clear previous content
            mermaidRef.current.innerHTML = '';

            // Render with Mermaid
            const { svg } = await mermaid.render(graphId, mermaidString);

            if (mermaidRef.current) {
                mermaidRef.current.innerHTML = svg;

                // Add click handlers to nodes
                if (onNodeClick) {
                    const nodes = mermaidRef.current.querySelectorAll('g.node');
                    nodes.forEach(node => {
                        const textElement = node.querySelector('text');
                        if (textElement) {
                            const nodeId = textElement.textContent || '';
                            node.style.cursor = 'pointer';
                            node.addEventListener('click', () => {
                                // Find the full node ID from the display label
                                const fullNodeId = findFullNodeId(nodeId);
                                if (fullNodeId) {
                                    onNodeClick(fullNodeId);
                                }
                            });
                        }
                    });
                }

                setState({ status: 'success', mermaidString });
            }
        } catch (error) {
            console.error('Mermaid render error:', error);
            setState({
                status: 'error',
                error: error instanceof Error ? error.message : 'Unknown error'
            });
        }
    }, [edgesJson, maxNodes, onNodeClick, retryCount]);

    // Find full node ID from display label
    const findFullNodeId = (displayLabel: string): string | undefined => {
        // This is a simplified approach - in a real implementation,
        // you'd want to maintain a proper mapping
        for (const edge of edgesJson) {
            if (edge.src.includes(displayLabel) || edge.dst.includes(displayLabel)) {
                return edge.src.includes(displayLabel) ? edge.src : edge.dst;
            }
        }
        return undefined;
    };

    // Re-render when dependencies change
    useEffect(() => {
        renderGraph();
    }, [renderGraph]);

    // Developer toggle for logging Mermaid string
    useEffect(() => {
        if (process.env.NODE_ENV === 'development' && state.mermaidString) {
            console.log('FlowGraph Mermaid String:', state.mermaidString);
        }
    }, [state.mermaidString]);

    const handleRetry = () => {
        setRetryCount(prev => prev + 1);
    };

    return (
        <div className={`flowgraph-container ${className}`}>
            {state.status === 'loading' && (
                <div style={{
                    padding: '20px',
                    textAlign: 'center',
                    color: '#666'
                }}>
                    <div>Loading graph...</div>
                </div>
            )}

            {state.status === 'error' && (
                <div style={{
                    padding: '20px',
                    textAlign: 'center',
                    backgroundColor: '#fff5f5',
                    border: '1px solid #fed7d7',
                    borderRadius: '4px',
                    color: '#c53030'
                }}>
                    <div>Error rendering graph: {state.error}</div>
                    <button
                        onClick={handleRetry}
                        style={{
                            marginTop: '10px',
                            padding: '8px 16px',
                            backgroundColor: '#e53e3e',
                            color: 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: 'pointer'
                        }}
                    >
                        Retry
                    </button>
                </div>
            )}

            {state.status === 'success' && (
                <div
                    ref={mermaidRef}
                    style={{
                        width: '100%',
                        minHeight: '200px',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center'
                    }}
                />
            )}
        </div>
    );
};

export default FlowGraph;
