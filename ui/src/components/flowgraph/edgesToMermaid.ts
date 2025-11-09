/**
 * Pure function to convert edges JSON to Mermaid graph string
 */

export interface EdgeData {
    src: string;
    dst: string;
    type: 'calls' | 'imports' | 'inherits';
}

export interface MermaidOptions {
    maxNodes?: number;
}

/**
 * Sanitize node ID for Mermaid compatibility
 * Replace non-alphanumeric characters with underscores
 */
function sanitizeNodeId(nodeId: string): string {
    return nodeId.replace(/[^a-zA-Z0-9_]/g, '_');
}

/**
 * Extract short label from full node ID
 * "file.py::function_name" -> "function_name"
 */
function getShortLabel(nodeId: string): string {
    const parts = nodeId.split('::');
    return parts.length > 1 ? parts[parts.length - 1] : nodeId;
}

/**
 * Identify entry nodes (main, start, init, etc.)
 */
function identifyEntryNodes(allNodes: string[]): string[] {
    const entryPatterns = ['main', 'start', 'init', 'run', 'execute', 'begin'];
    return allNodes.filter(node => {
        const nodeName = node.toLowerCase();
        return entryPatterns.some(pattern => nodeName.includes(pattern));
    });
}

/**
 * Identify main call path (most connected nodes)
 */
function identifyMainCallPath(edges: EdgeData[]): string[] {
    const nodeConnections = new Map<string, number>();

    // Count connections for each node
    edges.forEach(edge => {
        nodeConnections.set(edge.src, (nodeConnections.get(edge.src) || 0) + 1);
        nodeConnections.set(edge.dst, (nodeConnections.get(edge.dst) || 0) + 1);
    });

    // Get top 3 most connected nodes
    return Array.from(nodeConnections.entries())
        .sort((a, b) => b[1] - a[1])
        .slice(0, 3)
        .map(([node]) => node);
}

// Cache for fingerprint-based optimization
let lastFingerprint: string | null = null;
let lastResult: string | null = null;

/**
 * Convert edges JSON to Mermaid graph string
 */
export function edgesToMermaid(
    edgesJson: EdgeData[],
    options: MermaidOptions = {}
): string {
    const { maxNodes = 60 } = options;

    // Create fingerprint for caching
    const currentFingerprint = edgesJson.length > 0
        ? `${edgesJson.length}-${edgesJson.slice(0, 5).map(edge => `${edge.src}-${edge.dst}-${edge.type}`).join('|')}-${maxNodes}`
        : 'empty';

    // Return cached result if fingerprint unchanged
    if (lastFingerprint === currentFingerprint && lastResult !== null) {
        return lastResult;
    }

    // Handle empty/invalid edges
    if (!edgesJson || edgesJson.length === 0) {
        const emptyResult = `graph TD
      A["No relations found"]
      style A fill:#f9f9f9,stroke:#999,stroke-width:1px`;

        // Cache the empty result
        lastFingerprint = currentFingerprint;
        lastResult = emptyResult;

        return emptyResult;
    }

    // Collect all unique nodes
    const nodeSet = new Set<string>();
    edgesJson.forEach(edge => {
        nodeSet.add(edge.src);
        nodeSet.add(edge.dst);
    });

    const allNodes = Array.from(nodeSet);

    // Handle large graphs
    let nodesToInclude = allNodes;
    let trimmed = false;

    if (allNodes.length > maxNodes) {
        // Keep the most connected nodes (simple heuristic)
        const nodeConnections = new Map<string, number>();
        allNodes.forEach(node => nodeConnections.set(node, 0));

        edgesJson.forEach(edge => {
            nodeConnections.set(edge.src, (nodeConnections.get(edge.src) || 0) + 1);
            nodeConnections.set(edge.dst, (nodeConnections.get(edge.dst) || 0) + 1);
        });

        nodesToInclude = allNodes
            .sort((a, b) => (nodeConnections.get(b) || 0) - (nodeConnections.get(a) || 0))
            .slice(0, maxNodes);

        trimmed = true;
    }

    // Create node mapping for sanitized IDs
    const nodeMap = new Map<string, string>();
    nodesToInclude.forEach(node => {
        nodeMap.set(node, sanitizeNodeId(node));
    });

    // Identify special nodes for highlighting
    const entryNodes = identifyEntryNodes(nodesToInclude);
    const mainPathNodes = identifyMainCallPath(edgesJson);

    // Build Mermaid string
    let mermaidString = 'graph TD\n';

    // Add nodes with short labels
    nodesToInclude.forEach(node => {
        const sanitizedId = nodeMap.get(node)!;
        const shortLabel = getShortLabel(node);
        mermaidString += `  ${sanitizedId}["${shortLabel}"]\n`;
    });

    // Add edges with different styles
    edgesJson.forEach(edge => {
        const srcId = nodeMap.get(edge.src);
        const dstId = nodeMap.get(edge.dst);

        // Only include edges where both nodes are in our subset
        if (srcId && dstId) {
            let edgeStyle = '';

            switch (edge.type) {
                case 'calls':
                    edgeStyle = '-->';
                    break;
                case 'imports':
                    edgeStyle = '-.->';
                    break;
                case 'inherits':
                    edgeStyle = '==>';
                    break;
                default:
                    edgeStyle = '-->';
            }

            mermaidString += `  ${srcId}${edgeStyle}${dstId}\n`;
        }
    });

    // Add trimmed notice if needed
    if (trimmed) {
        const noticeId = sanitizeNodeId('_trimmed_notice');
        mermaidString += `  ${noticeId}["Graph trimmed to ${maxNodes} nodes"]\n`;
        mermaidString += `  style ${noticeId} fill:#fff3cd,stroke:#856404,stroke-width:1px\n`;
    }

    // Add highlighting styles for entry nodes
    entryNodes.forEach(node => {
        const sanitizedId = nodeMap.get(node);
        if (sanitizedId) {
            mermaidString += `  style ${sanitizedId} fill:#e6f7ff,stroke:#1890ff,stroke-width:2px\n`;
        }
    });

    // Add highlighting styles for main path nodes
    mainPathNodes.forEach(node => {
        const sanitizedId = nodeMap.get(node);
        if (sanitizedId && !entryNodes.includes(node)) {
            mermaidString += `  style ${sanitizedId} fill:#f6ffed,stroke:#52c41a,stroke-width:1px\n`;
        }
    });

    // Cache the result
    lastFingerprint = currentFingerprint;
    lastResult = mermaidString;

    return mermaidString;
}

/**
 * Get display label for a node (short version)
 */
export function getDisplayLabel(nodeId: string): string {
    return getShortLabel(nodeId);
}

/**
 * Get full node ID from sanitized ID
 */
export function getFullNodeId(sanitizedId: string, nodeMap: Map<string, string>): string | undefined {
    for (const [fullId, sanitized] of nodeMap.entries()) {
        if (sanitized === sanitizedId) {
            return fullId;
        }
    }
    return undefined;
}
