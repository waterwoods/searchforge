import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { edgesToMermaid, EdgeData } from './edgesToMermaid';

// Module-level guard to initialize mermaid once
let mermaidInitialized = false;
if (!mermaidInitialized) {
    mermaid.initialize({
        startOnLoad: false,
        securityLevel: 'loose',
        theme: 'default'
    });
    mermaidInitialized = true;
}

// Module-level render counter for duplicate detection
const renderCountByContainerId = new Map<string, number>();

interface SimpleFlowGraphProps {
    phase: string;
    containerId: string;
    edgesJson: EdgeData[];
    maxNodes: number;
    onNodeClick?: (id: string) => void;
    onGraphReady: () => void;
    onError: (msg: string) => void;
    currentRequestId: string;
    dispatch: (event: any) => void;
}

const SimpleFlowGraph: React.FC<SimpleFlowGraphProps> = ({
    phase,
    containerId,
    edgesJson,
    maxNodes,
    onNodeClick,
    onGraphReady,
    onError,
    currentRequestId,
    dispatch
}) => {
    // All hooks must be at the top - never call hooks after early returns
    const containerRef = useRef<HTMLDivElement>(null);
    const [isRendering, setIsRendering] = useState(false);
    const [isEmpty, setIsEmpty] = useState(false);

    // Handle empty/invalid edgesJson inside useEffect
    useEffect(() => {
        if (!edgesJson?.length) {
            setIsEmpty(true);
            onGraphReady();
            return;
        }

        setIsEmpty(false);
    }, [edgesJson, onGraphReady]);

    // Memoize render with proper useEffect and cancellation
    useEffect(() => {
        if (phase !== 'graph_rendering') return;

        let cancelled = false;

        const renderGraph = async () => {
            if (isRendering || !containerRef.current) return;

            setIsRendering(true);

            try {
                // Generate Mermaid code
                const mermaidCode = edgesToMermaid(edgesJson, { maxNodes });

                // Render with mermaid.render
                const { svg } = await mermaid.render(containerId, mermaidCode);

                // Check if cancelled before proceeding
                if (cancelled) return;

                // Set innerHTML of containerRef
                if (containerRef.current) {
                    containerRef.current.innerHTML = svg;

                    // Add click handlers if onNodeClick is provided
                    if (onNodeClick) {
                        const clickHandler = (event: Event) => {
                            const target = event.target as HTMLElement;
                            if (target && target.textContent) {
                                const nodeId = target.textContent.trim();
                                if (nodeId) {
                                    onNodeClick(nodeId);
                                }
                            }
                        };

                        containerRef.current.addEventListener('click', clickHandler);

                        // Add cursor styles to nodes
                        const nodes = containerRef.current.querySelectorAll('g.node');
                        nodes?.forEach((node) => {
                            (node as HTMLElement).style.cursor = 'pointer';
                            (node as HTMLElement).style.pointerEvents = 'auto';
                        });
                    }
                }

                // Increment render count and check for duplicates
                const currentCount = (renderCountByContainerId.get(containerId) || 0) + 1;
                renderCountByContainerId.set(containerId, currentCount);

                if (currentCount > 1) {
                    console.warn(`[FG] duplicate render for ${containerId}: #${currentCount}`);
                    onError('duplicate-render');
                    return;
                }

                // Call onGraphReady only if not cancelled
                if (!cancelled) {
                    onGraphReady();
                    // Dispatch RENDER_OK event
                    dispatch({ type: 'RENDER_OK', rid: currentRequestId });
                }
            } catch (err) {
                if (!cancelled) {
                    const errorMsg = err instanceof Error ? err.message : 'Unknown error';
                    onError(errorMsg);
                }
            } finally {
                if (!cancelled) {
                    setIsRendering(false);
                }
            }
        };

        if (containerRef.current) {
            mermaid.init(undefined, containerRef.current);
        }
        renderGraph();

        return () => {
            cancelled = true;
        };
    }, [phase, containerId, edgesJson, maxNodes, onNodeClick, onGraphReady, onError, isRendering, currentRequestId, dispatch]);

    // Early return after all hooks are declared
    if (isEmpty) {
        return (
            <div style={{ width: '100%', minHeight: '200px', padding: '20px', textAlign: 'center', color: '#666' }}>
                No relations to render.
            </div>
        );
    }

    return (
        <div
            ref={containerRef}
            style={{
                width: '100%',
                minHeight: '300px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center'
            }}
        />
    );
};

// Shallow compare function for React.memo to prevent unnecessary re-renders
const areEqual = (prevProps: SimpleFlowGraphProps, nextProps: SimpleFlowGraphProps) => {
    // Check phase equality (string)
    if (prevProps.phase !== nextProps.phase) {
        return false;
    }

    // Check containerId equality (string)
    if (prevProps.containerId !== nextProps.containerId) {
        return false;
    }

    // Check maxNodes equality (number)
    if (prevProps.maxNodes !== nextProps.maxNodes) {
        return false;
    }

    // Check onNodeClick reference equality (function)
    if (prevProps.onNodeClick !== nextProps.onNodeClick) {
        return false;
    }

    // Check onGraphReady reference equality (function)
    if (prevProps.onGraphReady !== nextProps.onGraphReady) {
        return false;
    }

    // Check onError reference equality (function)
    if (prevProps.onError !== nextProps.onError) {
        return false;
    }

    // Check currentRequestId equality (string)
    if (prevProps.currentRequestId !== nextProps.currentRequestId) {
        return false;
    }

    // Check dispatch reference equality (function)
    if (prevProps.dispatch !== nextProps.dispatch) {
        return false;
    }

    // Check edgesJson: first compare by reference; if different, compare length and fingerprint
    if (prevProps.edgesJson === nextProps.edgesJson) {
        return true;
    }

    if (prevProps.edgesJson.length !== nextProps.edgesJson.length) {
        return false;
    }

    // Compare first 5 src/dst/type tuples for fingerprint
    const prevFingerprint = prevProps.edgesJson.slice(0, 5).map(edge => `${edge.src}-${edge.dst}-${edge.type}`).join('|');
    const nextFingerprint = nextProps.edgesJson.slice(0, 5).map(edge => `${edge.src}-${edge.dst}-${edge.type}`).join('|');

    return prevFingerprint === nextFingerprint;
};

export default React.memo(SimpleFlowGraph, areEqual);
