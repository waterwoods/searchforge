import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
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
} from 'reactflow';
import 'reactflow/dist/style.css';
import useStore from '../store';
import { GraphDataSchema } from '../schemas/graphSchemas';
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
                    boxShadow: '0 2px 4px rgba(0,0,0,0.3)',
                    position: 'relative',
                    wordWrap: 'break-word',
                    overflowWrap: 'break-word',
                    whiteSpace: 'normal',
                    ...performanceStyle,
                    border: selected ? '3px solid #00BFFF' : '2px solid #666',
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

// Convert backend data to ReactFlow format (WITHOUT trunk highlighting)
const convertToReactFlowData = (graphNodes, graphEdges) => {
    if (!graphNodes || graphNodes.length === 0) {
        return { nodes: [], edges: [] };
    }

    // Convert nodes (without position first)
    const reactFlowNodes = graphNodes.map((node) => {
        return {
            id: node.id,
            type: 'custom',
            position: { x: 0, y: 0 }, // Temporary position, will be calculated by ELK
            data: {
                label: node.fqName || node.id,
                hotness_score: node.hotness_score || 0,
                // Include performance data for heat map visualization
                p95_latency: node.data?.p95_latency,
                error_rate: node.data?.error_rate,
                throughput: node.data?.throughput,
                ...node, // Include all original node data
            },
            className: '', // No trunk highlighting by default
        };
    });

    // Convert edges
    const reactFlowEdges = graphEdges.map((edge, index) => {
        return {
            id: `edge-${index}`,
            source: edge.from,
            target: edge.to,
            type: 'smoothstep',
            animated: true,
            style: {
                stroke: '#888', // Default color
                strokeWidth: 2, // Default width
            },
            className: '', // No trunk highlighting by default
        };
    });

    return { nodes: reactFlowNodes, edges: reactFlowEdges };
};

const GraphPanelInner = () => {
    const { nodeId: paramNodeId } = useParams();
    const location = useLocation();
    const { nodes: graphNodes, edges: graphEdges, setSelectedNode, setSelectedNodeId, selectedNodeId, setGraphData } = useStore();

    // Determine nodeId: for file routes, extract from location pathname
    const nodeId = location.pathname.startsWith('/graph/file/')
        ? 'file/' + location.pathname.substring('/graph/file/'.length)
        : paramNodeId;
    const [isLoadingSubgraph, setIsLoadingSubgraph] = useState(false);
    const [fetchError, setFetchError] = useState(null);

    // 🔍 DEBUG: Add logging to track data changes
    useEffect(() => {
        console.log('🔍 GraphPanel - graphNodes changed:', graphNodes?.length || 0);
        console.log('🔍 GraphPanel - graphEdges changed:', graphEdges?.length || 0);
        console.log('🔍 GraphPanel - graphNodes sample:', graphNodes?.[0]);
        console.log('🔍 GraphPanel - nodeId from URL:', nodeId);
    }, [graphNodes, graphEdges, nodeId]);

    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const { fitView } = useReactFlow();
    const containerRef = useRef(null);
    const [containerSize, setContainerSize] = useState({ width: 800, height: 600 });
    const [isTrunkHighlighted, setIsTrunkHighlighted] = useState(false);
    const [heatmapMode, setHeatmapMode] = useState('hotness'); // 'hotness' | 'performance'

    // 🔍 DEBUG: Log initial state
    useEffect(() => {
        console.log('🎯 GraphPanel MOUNTED - isTrunkHighlighted initial state:', isTrunkHighlighted);
    }, []);

    // On-demand subgraph loading: Fetch data when nodeId changes
    useEffect(() => {
        // Only fetch if we have a nodeId from the URL
        if (!nodeId) {
            console.log('🔍 GraphPanel - No nodeId in URL, skipping fetch');
            return;
        }

        const fetchSubgraph = async () => {
            try {
                setIsLoadingSubgraph(true);
                setFetchError(null);

                const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

                // Check if this is a file query (nodeId starts with "file/")
                if (nodeId.startsWith('file/')) {
                    const filePath = decodeURIComponent(nodeId.substring(5)); // Remove "file/" prefix
                    console.log(`🔍 GraphPanel - Fetching file subgraph for: ${filePath}`);

                    const response = await fetch(`${apiBaseUrl}/api/v1/graph/file/${encodeURIComponent(filePath)}`);
                    if (!response.ok) {
                        throw new Error(`Failed to fetch file: ${filePath}`);
                    }

                    const subgraphData = await response.json();
                    console.log('🔍 GraphPanel - File subgraph data:', {
                        nodes: subgraphData.nodes?.length || 0,
                        edges: subgraphData.edges?.length || 0
                    });

                    // Validate with Zod schema
                    try {
                        const validatedData = GraphDataSchema.parse(subgraphData);
                        console.log('✅ GraphPanel - File subgraph validation passed!');
                        setGraphData(validatedData);

                        // --- NEW: INTELLIGENT SELECTION FOR FILE QUERIES ---
                        // File queries return all functions in the file.
                        // Default to selecting the FIRST node to provide a sensible starting point.
                        if (validatedData.nodes.length > 0) {
                            const firstNodeId = validatedData.nodes[0].id;
                            console.log(`✅ File query loaded. Auto-selecting first function: ${firstNodeId}`);
                            console.log(`ℹ️ Total functions in file: ${validatedData.nodes.length}`);

                            // Use setTimeout to ensure store update completes before selection
                            setTimeout(() => {
                                setSelectedNodeId(firstNodeId);
                            }, 0);
                        } else {
                            console.log(`⚠️ File query returned no nodes.`);
                        }
                    } catch (validationError) {
                        console.error('❌ GraphPanel - File subgraph validation failed:', validationError);
                        setFetchError(`Data validation failed: ${validationError.message}`);
                    }

                    return;
                }

                // Check if nodeId contains multiple IDs (comma-separated for multi-node queries)
                const nodeIds = nodeId.includes(',') ? nodeId.split(',') : [nodeId];
                const isMultiNode = nodeIds.length > 1;

                // For multi-node queries: use depth=1 for reasonable neighborhood
                // For single node queries: use depth=2 to show broader context
                const depth = isMultiNode ? 1 : 2;

                console.log(`🔍 GraphPanel - Fetching ${isMultiNode ? 'multi-node' : 'single-node'} subgraph for ${nodeIds.length} node(s) with depth=${depth}:`, nodeIds);

                // Fetch subgraphs for all nodes
                const fetchPromises = nodeIds.map(id =>
                    fetch(`${apiBaseUrl}/api/v1/graph/neighborhood/${id}?depth=${depth}`)
                        .then(res => res.ok ? res.json() : Promise.reject(new Error(`Failed to fetch node ${id}`)))
                );

                const subgraphs = await Promise.all(fetchPromises);
                console.log(`🔍 GraphPanel - Fetched ${subgraphs.length} subgraphs`);

                // Merge all subgraphs into one
                const mergedNodes = new Map();
                const mergedEdges = new Map();

                for (const subgraph of subgraphs) {
                    // Add nodes (avoid duplicates)
                    for (const node of subgraph.nodes || []) {
                        if (!mergedNodes.has(node.id)) {
                            mergedNodes.set(node.id, node);
                        }
                    }
                    // Add edges (avoid duplicates)
                    for (const edge of subgraph.edges || []) {
                        const edgeKey = `${edge.from}-${edge.to}`;
                        if (!mergedEdges.has(edgeKey)) {
                            mergedEdges.set(edgeKey, edge);
                        }
                    }
                }

                const mergedSubgraphData = {
                    nodes: Array.from(mergedNodes.values()),
                    edges: Array.from(mergedEdges.values())
                };

                console.log('🔍 GraphPanel - Merged subgraph data:', {
                    nodes: mergedSubgraphData.nodes.length,
                    edges: mergedSubgraphData.edges.length
                });

                // Validate with Zod schema
                try {
                    const validatedData = GraphDataSchema.parse(mergedSubgraphData);
                    console.log('✅ GraphPanel - Subgraph validation passed!');
                    console.log('🔍 GraphPanel - Validated nodes:', validatedData.nodes.length);
                    console.log('🔍 GraphPanel - Validated edges:', validatedData.edges.length);

                    // Update the Zustand store with the validated subgraph
                    setGraphData(validatedData);

                    // --- NEW: ROBUST SELECTION LOGIC FOR NODE QUERIES ---
                    let targetNodeId = null;

                    if (validatedData.nodes.some(n => n.id === nodeIds[0])) {
                        // This is a Node Query, and the entry node exists in the data
                        targetNodeId = nodeIds[0];
                        console.log(`✅ Node query loaded. Target node: ${targetNodeId}`);
                    } else if (validatedData.nodes.length > 0) {
                        // Entry node wasn't in the neighborhood, default to first node
                        targetNodeId = validatedData.nodes[0].id;
                        console.log(`ℹ️ Entry node not found in neighborhood. Defaulting to first node: ${targetNodeId}`);
                    }

                    if (targetNodeId) {
                        // Use setTimeout to ensure store update completes before selection
                        setTimeout(() => {
                            setSelectedNodeId(targetNodeId);
                        }, 0);
                    } else {
                        console.warn(`⚠️ No nodes available for selection.`);
                    }

                } catch (validationError) {
                    console.error('❌ GraphPanel - Subgraph validation failed:', validationError);
                    setFetchError(`Data validation failed: ${validationError.message}`);
                }

            } catch (error) {
                console.error('❌ GraphPanel - Error fetching subgraph:', error);
                setFetchError(error.message);
            } finally {
                setIsLoadingSubgraph(false);
            }
        };

        fetchSubgraph();
    }, [nodeId, setGraphData])

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


    // Memoize the converted ReactFlow data to avoid unnecessary recalculations
    // NOTE: This NO LONGER depends on isTrunkHighlighted - trunk highlighting is applied separately
    const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
        if (!graphNodes || graphNodes.length === 0) {
            return { nodes: [], edges: [] };
        }

        // 🔍 DEBUG: Check data size
        console.log('🔍 GraphPanel - Data size check:', {
            totalNodes: graphNodes.length,
            totalEdges: graphEdges?.length || 0
        });

        // Limit data size for performance (React Flow can struggle with very large graphs)
        const MAX_NODES = 100;
        const MAX_EDGES = 200;

        let limitedNodes = graphNodes;
        let limitedEdges = graphEdges || [];

        if (graphNodes.length > MAX_NODES) {
            console.warn(`🔍 GraphPanel - Limiting nodes from ${graphNodes.length} to ${MAX_NODES} for performance`);
            limitedNodes = graphNodes.slice(0, MAX_NODES);
            // Also limit edges to only those connecting the limited nodes
            const limitedNodeIds = new Set(limitedNodes.map(n => n.id));
            limitedEdges = (graphEdges || []).filter(e =>
                limitedNodeIds.has(e.from) && limitedNodeIds.has(e.to)
            ).slice(0, MAX_EDGES);
        }

        const converted = convertToReactFlowData(limitedNodes, limitedEdges);

        // 🔍 DEBUG: Verify conversion produces nodes with empty className
        console.log('🎯 CONVERSION CHECK - All nodes have empty className:',
            converted.nodes.every(n => n.className === ''));
        console.log('🎯 CONVERSION CHECK - Sample node classNames:',
            converted.nodes.slice(0, 3).map(n => ({ id: n.id, className: n.className })));

        return converted;
    }, [graphNodes, graphEdges]);

    // Create display nodes with selection state
    const displayNodes = useMemo(() => {
        return initialNodes.map(node => ({
            ...node,
            // This is the magic line: set 'selected' if the ID matches our store
            selected: node.id === selectedNodeId,
            // Inject heatmap mode into node data for CustomNode and MiniMap
            data: { ...(node.data || {}), heatmapMode },
        }));
    }, [initialNodes, selectedNodeId, heatmapMode]); // Re-compute when nodes, selection, or heatmap mode changes

    // Main layout effect: layout → setNodes/setEdges → fitView
    useEffect(() => {
        if (displayNodes && displayNodes.length > 0) {
            // Apply ELK layout with container awareness
            const widthHint = containerSize.width > 0 ? containerSize.width / containerSize.height : undefined;

            layoutWithElk(displayNodes, initialEdges, {
                direction: LAYOUT_CONFIG.DIRECTION,
                nodeSpacing: LAYOUT_CONFIG.NODE_SPACING,
                layerSpacing: LAYOUT_CONFIG.LAYER_SPACING,
                widthHint
            }).then(({ nodes: layoutedNodes, edges: layoutedEdges }) => {
                // 🔍 DEBUG: Log layouted data
                console.log('🔍 GraphPanel - Layout completed:', {
                    layoutedNodes: layoutedNodes.length,
                    layoutedEdges: layoutedEdges.length,
                    firstNode: layoutedNodes[0]
                });

                // 🔍 DEBUG: Verify NO trunk highlighting on initial render
                console.log('🎯 VERIFICATION - First node className:', layoutedNodes[0]?.className);
                console.log('🎯 VERIFICATION - Sample node classes:', layoutedNodes.slice(0, 3).map(n => ({ id: n.id, className: n.className })));

                // Set ReactFlow state
                setNodes(layoutedNodes);
                setEdges(layoutedEdges);

                // Auto-fit view after layout
                setTimeout(() => {
                    fitView({ padding: LAYOUT_CONFIG.FIT_PADDING });
                }, 100);
            }).catch((error) => {
                console.error('❌ Layout error:', error);
                // Fallback: set nodes without layout
                setNodes(displayNodes);
                setEdges(initialEdges);
            });
        }
    }, [displayNodes, initialEdges, setNodes, setEdges, fitView, containerSize]);

    // 🎯 CRITICAL FIX: Apply/Remove Main Trunk highlighting ONLY when button is clicked
    // This effect MUST ONLY depend on isTrunkHighlighted state to prevent zombie highlighting
    // We use a ref to store graphNodes/graphEdges to access them without triggering re-runs
    const graphDataRef = useRef({ nodes: graphNodes, edges: graphEdges });

    // Keep ref updated without triggering effects
    useEffect(() => {
        graphDataRef.current = { nodes: graphNodes, edges: graphEdges };
    }, [graphNodes, graphEdges]);

    useEffect(() => {
        // CRITICAL: This effect ONLY runs when isTrunkHighlighted changes (button click)
        // It does NOT run when data changes, preventing zombie highlighting

        console.log('🎯 TRUNK HIGHLIGHTING EFFECT TRIGGERED - isTrunkHighlighted:', isTrunkHighlighted);

        setNodes((currentNodes) => {
            if (currentNodes.length === 0) return currentNodes;

            if (isTrunkHighlighted) {
                // ✅ APPLY trunk highlighting - find and highlight main trunk nodes/edges
                console.log('🎨 [USER ACTION] Applying Main Trunk highlighting to nodes');

                return currentNodes.map(node => {
                    // Check if this node is part of the main trunk
                    const originalNode = graphDataRef.current.nodes.find(n => n.id === node.id);
                    const isTrunk = originalNode?.data?.is_main_trunk === true;

                    return {
                        ...node,
                        className: isTrunk ? 'main-trunk' : 'faded',
                        // Non-destructive style merge; use CSS var to control inner background
                        style: isTrunk
                            ? { ...node.style, '--node-bg': '#D97706' }
                            : { ...node.style },
                    };
                });
            } else {
                // --- 🔥 SCORCHED-EARTH RESET ---
                // Force-reset EVERY node to pristine state
                console.log('🔥 [SYSTEM] Performing total reset of trunk highlighting on nodes...');

                return currentNodes.map(node => {
                    const newStyle = { ...(node.style || {}) };
                    // Remove trunk-specific CSS variable without nuking other styles
                    delete newStyle['--node-bg'];

                    return {
                        ...node,
                        className: undefined,
                        style: newStyle,
                    };
                });
            }
        });

        setEdges((currentEdges) => {
            if (currentEdges.length === 0) return currentEdges;

            if (isTrunkHighlighted) {
                // ✅ APPLY trunk highlighting to edges
                console.log('🎨 [USER ACTION] Applying Main Trunk highlighting to edges');

                return currentEdges.map(edge => {
                    // Check if this edge is part of the main trunk
                    const originalEdge = graphDataRef.current.edges?.find(e =>
                        e.from === edge.source && e.to === edge.target
                    );
                    const isTrunk = originalEdge?.data?.is_main_trunk === true;

                    return {
                        ...edge,
                        className: isTrunk ? 'main-trunk' : 'faded',
                        style: {
                            ...edge.style,
                            stroke: isTrunk ? '#ff0072' : '#888',
                            strokeWidth: isTrunk ? 3 : 2,
                        },
                    };
                });
            } else {
                // --- 🔥 SCORCHED-EARTH RESET ---
                // Force-reset EVERY edge to pristine state
                console.log('🔥 [SYSTEM] Performing total reset of trunk highlighting on edges...');

                return currentEdges.map(edge => ({
                    ...edge,
                    className: undefined, // Explicitly remove any CSS classes
                    style: {              // Explicitly reset to default React Flow styles
                        stroke: '#b1b1b7',    // Default edge color
                        strokeWidth: 1,       // Default edge width
                    },
                    animated: false,      // Explicitly turn off animation
                }));
            }
        });
    }, [isTrunkHighlighted]); // CRITICAL: ONLY depends on isTrunkHighlighted toggle (setNodes/setEdges are stable refs)

    // Handle node click
    const onNodeClick = useCallback((event, clickedNode) => {
        console.log('Node clicked:', clickedNode);

        // 1. Extract the ID from the React Flow node
        const nodeId = clickedNode.id;

        // 2. Find the complete, original node from our source data
        const originalNode = graphNodes.find(node => node.id === nodeId);

        // 3. Pass the complete object to the store
        if (originalNode) {
            console.log('Setting selected node:', originalNode);
            setSelectedNode(originalNode.id); // Pass the ID, not the full object
        } else {
            console.warn('Could not find original node for ID:', nodeId);
        }
    }, [setSelectedNode, graphNodes]);

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
                        className={`heatmap-toggle-btn ${heatmapMode === 'performance' ? 'active' : ''}`}
                        onClick={() => setHeatmapMode(heatmapMode === 'hotness' ? 'performance' : 'hotness')}
                        style={{ marginRight: '8px' }}
                    >
                        {heatmapMode === 'hotness' ? 'Switch to Performance Heatmap' : 'Switch to Hotness Heatmap'}
                    </button>
                    <button
                        className={`trunk-toggle-btn ${isTrunkHighlighted ? 'active' : ''}`}
                        onClick={() => {
                            setIsTrunkHighlighted(!isTrunkHighlighted);
                        }}
                    >
                        {isTrunkHighlighted ? 'Hide Main Trunk' : 'Highlight Main Trunk'}
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
                {isLoadingSubgraph ? (
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