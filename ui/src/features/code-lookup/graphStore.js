import { create } from 'zustand';

// Central store for graph streaming search results
const useGraphStore = create((set, get) => ({
    graphData: null,
    isLoading: false,
    selectedNodeId: null,
    setSelectedNodeId: (nodeId) => set({ selectedNodeId: nodeId }),
    clearGraphData: () => set({ graphData: null, selectedNodeId: null }),

    // Fetch graph data via SSE and populate store when final payload arrives
    fetchGraphData: (query) => {
        const q = String(query || '').trim();
        if (!q) return;

        // Reset state and start loading
        set({ isLoading: true, graphData: null });

        const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';
        const source = new EventSource(`${apiBaseUrl}/api/v1/graph/stream-search?q=${encodeURIComponent(q)}`);

        source.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.event === 'final' && data.final_data) {
                    // Expecting a payload that either already contains nodes/edges
                    // or identifiers which the UI can use. We pass through as-is.
                    const finalData = data.final_data;
                    set({ graphData: finalData });
                    source.close();
                    set({ isLoading: false });
                }
                if (event.data === '[DONE]') {
                    try { source.close(); } catch { }
                    set({ isLoading: false });
                }
            } catch (e) {
                // Non-JSON keepalive or diagnostic messages are ignored
            }
        };

        source.onerror = () => {
            try { source.close(); } catch { }
            set({ isLoading: false });
        };

        return () => {
            try { source.close(); } catch { }
        };
    }
}));

export default useGraphStore;


