import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useLocation } from 'react-router-dom';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Handle,
    Position,
    useReactFlow,
    ReactFlowProvider,
    SmoothStepEdge,
} from 'reactflow';
import 'reactflow/dist/style.css';
import useGraphStore from '../graphStore';

import ELK from 'elkjs/lib/elk.bundled.js';

// Layout constants for easy tuning
const LAYOUT_CONFIG = {
    DIRECTION: 'DOWN',
    NODE_SPACING: 56,
    LAYER_SPACING: 72,
    FIT_PADDING: 0.2,
    MIN_ZOOM: 0.1,
    MAX_ZOOM: 1.5,
};

const elk = new ELK();

// ELK Layout utility
async function layoutWithElk(nodes, edges, {
    direction = LAYOUT_CONFIG.DIRECTION,
    nodeSpacing = LAYOUT_CONFIG.NODE_SPACING,
    layerSpacing = LAYOUT_CONFIG.LAYER_SPACING,
    widthHint
} = {}) {
    const graph = {
        id: 'root',
        layoutOptions: {
            'elk.algorithm': 'layered',
            'elk.direction': direction,
            'elk.spacing.nodeNode': String(nodeSpacing),
            'elk.spacing.nodeNodeBetweenLayers': String(layerSpacing),
            'elk.layered.edgeRouting': 'ORTHOGONAL',
            'elk.layered.considerModelOrder': 'true',
            ...(widthHint ? { 'elk.aspectRatio': String(widthHint) } : {})
        },
        children: nodes.map(n => ({
            id: n.id,
            width: n.measured?.width ?? 200,
            height: n.measured?.height ?? 60
        })),
        edges: edges.map(e => ({
            id: e.id,
            sources: [e.source],
            targets: [e.target]
        })),
    };

    const res = await elk.layout(graph);
    const pos = new Map(res.children.map(c => [c.id, { x: c.x, y: c.y }]));

    return {
        nodes: nodes.map(n => ({
            ...n,
            position: pos.get(n.id) ?? n.position,
            sourcePosition: 'bottom',
            targetPosition: 'top'
        })),
        edges
    };
}

// Performance color mapping: <100ms green, 100-400ms orange, >400ms red
const getPerformanceColor = (latency) => {
    if (!latency) return '#2c3e50';
    const ms = typeof latency === 'number'
        ? latency
        : parseInt(String(latency).replace('ms', '').trim());
    if (Number.isNaN(ms)) return '#2c3e50';
    if (ms < 100) return '#2ecc71';
    if (ms <= 400) return '#f39c12';
    return '#e74c3c';
};

// Custom Node Component for heatmap visualization
const CustomNode = ({ data, selected }) => {
    const { hotness_score, label, p95_latency, error_rate, heatmapMode } = data;

    // Hotness color mapping (existing behavior)
    const getHotnessColor = (score) => {
        if (score <= 2) return '#3498db';
        if (score <= 5) return '#f39c12';
        return '#e74c3c';
    };

    // Calculate performance-based styling for bottleneck detection (only in performance mode)
    const getPerformanceStyle = () => {
        if (heatmapMode !== 'performance' || !p95_latency) return {};
        const latencyMs = typeof p95_latency === 'number'
            ? p95_latency
            : parseInt(String(p95_latency).replace('ms', '').trim());
        const errorRate = parseFloat(String(data?.error_rate ?? '0').replace('%', ''));
        const isBottleneck = (!Number.isNaN(latencyMs) && latencyMs > 400) || errorRate > 3.0;
        if (isBottleneck) {
            return {
                border: '3px solid #ff4444',
                boxShadow: '0 0 15px rgba(255, 68, 68, 0.6), 0 0 30px rgba(255, 68, 68, 0.3)',
                animation: 'pulse 2s infinite',
            };
        }
        return {};
    };

    const baseColor = heatmapMode === 'performance'
        ? getPerformanceColor(p95_latency)
        : getHotnessColor(hotness_score || 0);

    const performanceStyle = getPerformanceStyle();

    // Golden path highlight styles
    const isOnGoldenPath = data?.isOnGoldenPath === true;

    return (
        <>
            <Handle type="target" position={Position.Top} />
            <div
                className="custom-node-content"
                style={{
                    background: `var(--node-bg, ${baseColor})`,
                    color: 'white',
                    padding: '8px 12px',
                    borderRadius: '8px',
                    maxWidth: '180px',
                    minHeight: '30px',
                    minWidth: '120px',
                    textAlign: 'center',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    position: 'relative',
                    wordWrap: 'break-word',
                    overflowWrap: 'break-word',
                    whiteSpace: 'normal',
                    ...performanceStyle,
                    border: isOnGoldenPath
                        ? '3px solid #FFD700' // gold
                        : selected
                            ? '3px solid #00BFFF'
                            : '2px solid #666',
                    boxShadow: isOnGoldenPath
                        ? '0 0 10px rgba(255,215,0,0.7), 0 0 20px rgba(255,215,0,0.4)'
                        : performanceStyle.boxShadow || '0 2px 4px rgba(0,0,0,0.3)',
                }}
            >
                <div style={{ marginBottom: '4px' }}>
                    {label}
                </div>
                {heatmapMode === 'hotness' && hotness_score > 0 && (
                    <div
                        style={{
                            background: 'rgba(255,255,255,0.2)',
                            borderRadius: '12px',
                            padding: '2px 6px',
                            fontSize: '10px',
                            display: 'inline-block',
                        }}
                    >
                        {hotness_score}
                    </div>
                )}
                {heatmapMode === 'performance' && p95_latency && (
                    <div
                        style={{
                            background: 'rgba(255,255,255,0.2)',
                            borderRadius: '12px',
                            padding: '2px 6px',
                            fontSize: '10px',
                            display: 'inline-block',
                        }}
                    >
                        {typeof p95_latency === 'number' ? `${p95_latency}ms` : p95_latency}
                    </div>
                )}
            </div>
            <Handle type="source" position={Position.Bottom} />
        </>
    );
};

// Define custom node types - moved outside component to prevent recreation
const nodeTypes = {
    custom: CustomNode,
};

// Custom Edge to enable golden path styling while preserving smoothstep behavior
const CustomEdge = (edgeProps) => {
    const { data } = edgeProps;
    const isOnGoldenPath = data?.isOnGoldenPath === true;

    const stroke = isOnGoldenPath ? '#FFD700' : (edgeProps.style?.stroke || '#888');
    const strokeWidth = isOnGoldenPath ? 3 : (edgeProps.style?.strokeWidth || 2);

    return (
        <SmoothStepEdge
            {...edgeProps}
            style={{
                ...(edgeProps.style || {}),
                stroke,
                strokeWidth,
                strokeDasharray: isOnGoldenPath ? '6 3' : edgeProps.style?.strokeDasharray,
            }}
            animated={isOnGoldenPath || edgeProps.animated}
        />
    );
};

const edgeTypes = {
    customEdge: CustomEdge,
};

// Convert backend data to ReactFlow format
const toReactFlow = (graphNodes, graphEdges, heatmapMode) => {
    if (!Array.isArray(graphNodes) || graphNodes.length === 0) {
        return { nodes: [], edges: [] };
    }

    const nodes = graphNodes.map((n) => ({
        id: n.id,
        type: 'custom',
        position: { x: 0, y: 0 },
        data: { ...(n.data || {}), fqName: n.fqName || n.id, label: n.fqName || n.id, heatmapMode },
        className: '',
    }));

    const edges = (graphEdges || []).map((e, idx) => ({
        id: `edge-${idx}`,
        source: e.from,
        target: e.to,
        type: 'customEdge',
        animated: true,
        style: { stroke: '#888', strokeWidth: 2 },
        data: {},
        className: '',
    }));

    return { nodes, edges };
};

const GraphPanelInner = () => {
    const { nodeId: paramNodeId } = useParams();
    const location = useLocation();
    const { graphData, isLoading: isGlobalLoading } = useGraphStore();
    const clearGraphData = useGraphStore((state) => state.clearGraphData);
    const selectedNodeId = useGraphStore((state) => state.selectedNodeId);

    // Consume graph data directly from the shared store (nodes/edges expected)

    // Determine nodeId: for file routes, extract from location pathname
    const nodeId = location.pathname.startsWith('/graph/file/')
        ? 'file/' + location.pathname.substring('/graph/file/'.length)
        : paramNodeId;
    const [isLoadingSubgraph, setIsLoadingSubgraph] = useState(false);
    const [fetchError, setFetchError] = useState(null);

    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();
    const containerRef = useRef(null);
    const [containerSize, setContainerSize] = useState({ width: 800, height: 600 });
    const [heatmapMode, setHeatmapMode] = useState('hotness'); // 'hotness' | 'performance'
    const [goldenPathNodeIds, setGoldenPathNodeIds] = useState([]); // Use array instead of Set for React dependency tracking
    const [goldenPathEdgePairs, setGoldenPathEdgePairs] = useState([]); // Use array instead of Set
    const [isLoadingGoldenPath, setIsLoadingGoldenPath] = useState(false);

    // Simplified: consume store graphData and render directly
    useEffect(() => {
        console.log('[GraphPanel] Received new graphData from store:', graphData);
        const g = graphData || {};
        const srcNodes = g.nodes || g.results?.nodes || [];
        const srcEdges = g.edges || g.results?.edges || [];

        if (!Array.isArray(srcNodes) || srcNodes.length === 0) {
            setNodes([]);
            setEdges([]);
            return;
        }

        const MAX_NODES = 100;
        const MAX_EDGES = 200;
        let limitedNodes = srcNodes.slice(0, MAX_NODES);
        const allowed = new Set(limitedNodes.map(n => n.id));
        let limitedEdges = (srcEdges || []).filter(e => allowed.has(e.from) && allowed.has(e.to)).slice(0, MAX_EDGES);

        const { nodes: rfNodes, edges: rfEdges } = toReactFlow(limitedNodes, limitedEdges, heatmapMode);
        console.log('[GraphPanel] Extracted nodes to be rendered:', rfNodes);
        console.log('[GraphPanel] Extracted edges to be rendered:', rfEdges);

        // Add default dimensions before running ELK layout to avoid crashes
        const layoutNodes = rfNodes.map((n) => ({
            ...n,
            width: typeof n.width === 'number' ? n.width : 150,
            height: typeof n.height === 'number' ? n.height : 50,
            measured: {
                width: n?.measured?.width ?? 150,
                height: n?.measured?.height ?? 50,
            },
        }));

        const widthHint = containerSize.width > 0 ? containerSize.width / containerSize.height : undefined;
        layoutWithElk(layoutNodes, rfEdges, {
            direction: LAYOUT_CONFIG.DIRECTION,
            nodeSpacing: LAYOUT_CONFIG.NODE_SPACING,
            layerSpacing: LAYOUT_CONFIG.LAYER_SPACING,
            widthHint
        }).then(({ nodes: layoutedNodes, edges: layoutedEdges }) => {
            // Apply golden path highlighting when setting nodes/edges
            const nodesWithGoldenPath = layoutedNodes.map(n => ({
                ...n,
                data: { ...(n.data || {}), isOnGoldenPath: goldenPathNodeIds.includes(n.id) },
            }));
            const edgesWithGoldenPath = layoutedEdges.map(e => {
                const isOnPath = goldenPathEdgePairs.includes(`${e.source}->${e.target}`);
                return {
                    ...e,
                    type: 'customEdge',
                    data: { ...(e.data || {}), isOnGoldenPath: isOnPath },
                };
            });
            setNodes(nodesWithGoldenPath);
            setEdges(edgesWithGoldenPath);
            setTimeout(() => { fitView({ padding: LAYOUT_CONFIG.FIT_PADDING }); }, 50);
        }).catch(() => {
            // Apply golden path highlighting even when layout fails
            const nodesWithGoldenPath = layoutNodes.map(n => ({
                ...n,
                data: { ...(n.data || {}), isOnGoldenPath: goldenPathNodeIds.includes(n.id) },
            }));
            const edgesWithGoldenPath = rfEdges.map(e => {
                const isOnPath = goldenPathEdgePairs.includes(`${e.source}->${e.target}`);
                return {
                    ...e,
                    type: 'customEdge',
                    data: { ...(e.data || {}), isOnGoldenPath: isOnPath },
                };
            });
            setNodes(nodesWithGoldenPath);
            setEdges(edgesWithGoldenPath);
        });
    }, [graphData, heatmapMode, containerSize.width, containerSize.height, fitView, setNodes, setEdges, goldenPathNodeIds, goldenPathEdgePairs])

    // ResizeObserver to watch container size changes
    useEffect(() => {
        if (!containerRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                setContainerSize({ width, height });
            }
        });

        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, []);


    // Fetch and compute Golden Path from backend
    const fetchGoldenPath = useCallback(async () => {
        // Prefer an explicitly selected node; fall back to route param; finally first node from graphData
        const graphNodes = graphData?.nodes || graphData?.results?.nodes || [];
        const firstNodeId = graphNodes.length > 0 ? graphNodes[0].id : null;
        const entryId = selectedNodeId || nodeId || firstNodeId;
        console.log('[Golden Path] Button clicked. Entry ID:', entryId, 'selectedNodeId:', selectedNodeId, 'nodeId:', nodeId, 'firstNodeId:', firstNodeId);

        if (!entryId) {
            console.warn('[Golden Path] No entry ID available. Cannot fetch golden path.');
            alert('Please select a node first, or ensure the graph has loaded.');
            return;
        }

        try {
            setIsLoadingGoldenPath(true);
            const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
            const url = `${apiBaseUrl}/api/v1/graph/golden-path?entry=${encodeURIComponent(entryId)}`;
            console.log('[Golden Path] Fetching from:', url);

            const res = await fetch(url);
            console.log('[Golden Path] Response status:', res.status, res.statusText);

            if (!res.ok) {
                const errorText = await res.text();
                console.error('[Golden Path] API error:', res.status, errorText);
                throw new Error(`Failed to fetch golden path: ${res.status} ${res.statusText}`);
            }

            const pathNodeIds = await res.json(); // expects array of node IDs
            console.log('[Golden Path] Received path node IDs:', pathNodeIds);

            if (!Array.isArray(pathNodeIds) || pathNodeIds.length === 0) {
                console.warn('[Golden Path] Empty or invalid path returned');
                setGoldenPathNodeIds([]);
                setGoldenPathEdgePairs([]);
                alert('Golden path is empty for this entry node.');
                return;
            }

            const nodeIdArray = [...pathNodeIds]; // Convert to array
            const edgePairsArray = [];
            for (let i = 0; i < pathNodeIds.length - 1; i++) {
                edgePairsArray.push(`${pathNodeIds[i]}->${pathNodeIds[i + 1]}`);
            }

            console.log('[Golden Path] Setting golden path node IDs:', nodeIdArray);
            console.log('[Golden Path] Setting golden path edge pairs:', edgePairsArray);
            setGoldenPathNodeIds(nodeIdArray);
            setGoldenPathEdgePairs(edgePairsArray);
        } catch (e) {
            console.error('❌ Error fetching golden path:', e);
            // Show user-friendly error message
            alert(`Failed to fetch golden path: ${e.message}`);
        } finally {
            setIsLoadingGoldenPath(false);
        }
    }, [nodeId, graphData, selectedNodeId]);

    // Apply Golden Path highlighting to nodes when path changes
    useEffect(() => {
        setNodes((current) => current.map(n => ({
            ...n,
            data: { ...(n.data || {}), isOnGoldenPath: goldenPathNodeIds.includes(n.id) },
        })));
    }, [goldenPathNodeIds, setNodes]);

    // Apply Golden Path highlighting to edges when path changes
    useEffect(() => {
        setEdges((current) => current.map(e => {
            const isOnPath = goldenPathEdgePairs.includes(`${e.source}->${e.target}`);
            return {
                ...e,
                type: 'customEdge',
                data: { ...(e.data || {}), isOnGoldenPath: isOnPath },
            };
        }));
    }, [goldenPathEdgePairs, setEdges]);

    // Handle node click -> publish to shared store
    const setSelectedNodeId = useGraphStore((state) => state.setSelectedNodeId);
    const onNodeClick = useCallback((event, clickedNode) => {
        if (clickedNode?.id) {
            setSelectedNodeId(clickedNode.id);
        }
    }, [setSelectedNodeId]);

    // Handle edge connection
    const onConnect = useCallback((params) => {
        setEdges((eds) => addEdge(params, eds));
    }, [setEdges]);

    return (
        <div className="graph-panel">
            <div className="graph-header">
                <h3>Graph Visualization</h3>
                <div className="graph-controls">
                    <button
                        className={`heatmap-toggle-btn ${heatmapMode === 'performance' ? 'clu-active' : ''}`}
                        onClick={() => setHeatmapMode(heatmapMode === 'hotness' ? 'performance' : 'hotness')}
                        style={{ marginRight: '8px' }}
                    >
                        {heatmapMode === 'hotness' ? 'Switch to Performance Heatmap' : 'Switch to Hotness Heatmap'}
                    </button>
                    <button
                        className={`golden-path-btn`}
                        onClick={fetchGoldenPath}
                        style={{ marginRight: '8px' }}
                        disabled={isLoadingGoldenPath || (!selectedNodeId && !nodeId && (!graphData?.nodes?.length && !graphData?.results?.nodes?.length))}
                    >
                        {isLoadingGoldenPath ? 'Loading Golden Path…' : 'Show Golden Path'}
                    </button>
                    <button
                        onClick={clearGraphData}
                        className="new-search-btn"
                        style={{ marginLeft: 'auto' }}
                    >
                        New Search
                    </button>
                    <div className="graph-stats">
                        {isLoadingSubgraph && (
                            <span style={{ color: '#f39c12' }}>
                                Loading subgraph...
                            </span>
                        )}
                        {!isLoadingSubgraph && nodes.length > 0 && (
                            <span>
                                {nodes.length} nodes, {edges.length} edges
                            </span>
                        )}
                        {fetchError && (
                            <span style={{ color: '#e74c3c', fontSize: '12px' }}>
                                Error: {fetchError}
                            </span>
                        )}
                    </div>
                </div>
            </div>

            <div
                ref={containerRef}
                style={{ width: '100%', height: '600px', background: '#1a1a1a' }}
            >
                {isGlobalLoading || isLoadingSubgraph ? (
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        height: '100%',
                        color: '#fff',
                        fontSize: '18px'
                    }}>
                        Loading graph data...
                    </div>
                ) : (
                    <ReactFlow
                        nodes={nodes}
                        edges={edges}
                        onNodesChange={onNodesChange}
                        onEdgesChange={onEdgesChange}
                        onConnect={onConnect}
                        onNodeClick={onNodeClick}
                        nodeTypes={nodeTypes}
                        edgeTypes={edgeTypes}
                        attributionPosition="bottom-left"
                        minZoom={LAYOUT_CONFIG.MIN_ZOOM}
                        maxZoom={LAYOUT_CONFIG.MAX_ZOOM}
                        panOnScroll={true}
                        zoomOnPinch={true}
                        nodeExtent={[
                            [0, 0],
                            [containerSize.width * 2, containerSize.height * 2]
                        ]}
                    >
                        <Controls />
                        <MiniMap
                            nodeColor={(node) => {
                                const mode = node.data?.heatmapMode || heatmapMode;
                                if (mode === 'performance') {
                                    const latency = node.data?.p95_latency;
                                    const ms = typeof latency === 'number' ? latency : parseInt(String(latency || '').replace('ms', '').trim());
                                    if (Number.isNaN(ms)) return '#2c3e50';
                                    if (ms < 100) return '#2ecc71';
                                    if (ms <= 400) return '#f39c12';
                                    return '#e74c3c';
                                }
                                const score = node.data?.hotness_score || 0;
                                if (score <= 2) return '#3498db';
                                if (score <= 5) return '#f39c12';
                                return '#e74c3c';
                            }}
                            style={{
                                background: '#2a2a2a',
                                border: '1px solid #666',
                            }}
                        />
                        <Background color="#333" gap={20} />
                    </ReactFlow>
                )}
            </div>
        </div>
    );
};

const GraphPanel = () => {
    return (
        <ReactFlowProvider>
            <GraphPanelInner />
        </ReactFlowProvider>
    );
};

export default GraphPanel;