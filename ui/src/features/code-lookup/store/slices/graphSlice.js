import { create } from 'zustand';

// Graph slice - manages graph data and node selection
export const createGraphSlice = (set, get) => ({
    // Graph data
    graphData: null,
    nodes: [],
    edges: [],

    // Selected node
    selectedNode: null,
    selectedNodeEvidence: null,
    selectedNodeId: null, // Track which node is currently selected by ID

    // Actions
    setGraphData: (data) => {
        if (data && typeof data === 'object') {
            if (data.nodes && data.edges) {
                set({
                    graphData: data,
                    nodes: data.nodes,
                    edges: data.edges
                });
            } else if (Array.isArray(data)) {
                set({
                    graphData: { nodes: data, edges: [] },
                    nodes: data,
                    edges: []
                });
            } else if (data.total_nodes) {
                set({
                    graphData: data,
                    nodes: [],
                    edges: []
                });
            } else {
                set({ graphData: data, nodes: [], edges: [] });
            }
        } else {
            set({ graphData: data, nodes: [], edges: [] });
        }
    },

    setSelectedNode: (nodeId) => {
        const { nodes } = get();
        const node = nodes.find(n => n.id === nodeId);
        set({
            selectedNode: node,
            selectedNodeEvidence: node ? node.evidence : null,
            selectedNodeId: nodeId
        });
    },

    setSelectedNodeId: (nodeId) => {
        const { nodes } = get();
        const node = nodes.find(n => n.id === nodeId);
        set({
            selectedNodeId: nodeId,
            selectedNode: node,
            selectedNodeEvidence: node ? node.evidence : null
        });
    },

    // Reset graph state
    resetGraph: () => set({
        graphData: null,
        nodes: [],
        edges: [],
        selectedNode: null,
        selectedNodeEvidence: null,
        selectedNodeId: null
    })
});
