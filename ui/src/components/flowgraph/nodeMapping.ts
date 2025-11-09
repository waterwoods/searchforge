/**
 * Node mapping utilities for FlowGraph click handling
 * Maps Mermaid node labels to backend symbols with intelligent resolution
 */

export interface FullNode {
    node_id: string;
    name: string;
    file_path: string;
    type?: 'calls' | 'imports' | 'inherits';
}

export interface NodeMapping {
    [shortLabel: string]: FullNode[];
}

export interface NodeResolutionResult {
    resolved: boolean;
    node?: FullNode;
    candidates?: FullNode[];
    fallbackAction?: {
        symbol: string;
        file_hint: string;
    };
}

/**
 * Build node lookup mapping from edges_json and files
 */
export function buildNodeMapping(
    edgesJson: Array<{ src: string; dst: string; type: string }>,
    files: Array<{ path: string;[key: string]: any }>
): NodeMapping {
    const mapping: NodeMapping = {};

    console.debug('[NodeMapping] Building mapping from', edgesJson.length, 'edges and', files.length, 'files');

    // Extract all unique nodes from edges
    const allNodes = new Set<string>();
    edgesJson.forEach(edge => {
        allNodes.add(edge.src);
        allNodes.add(edge.dst);
    });

    // Build file path set for quick lookup
    const filePaths = new Set(files.map(f => f.path));

    // Process each node
    allNodes.forEach(nodeId => {
        const [filePath, functionName] = nodeId.split('::');
        const shortLabel = functionName || filePath.split('/').pop() || nodeId;

        if (!mapping[shortLabel]) {
            mapping[shortLabel] = [];
        }

        const fullNode: FullNode = {
            node_id: nodeId,
            name: functionName || 'unknown',
            file_path: filePath,
            type: edgesJson.find(e => e.src === nodeId || e.dst === nodeId)?.type as any
        };

        mapping[shortLabel].push(fullNode);

        console.debug('[NodeMapping] Mapped', shortLabel, '->', fullNode);
    });

    console.debug('[NodeMapping] Built mapping with', Object.keys(mapping).length, 'unique labels');
    return mapping;
}

/**
 * Resolve node from short label with intelligent fallback
 */
export function resolveNode(
    shortLabel: string,
    mapping: NodeMapping,
    currentFiles: Array<{ path: string;[key: string]: any }>,
    highlightedNodes: string[] = []
): NodeResolutionResult {
    console.debug('[NodeMapping] Resolving node:', shortLabel);

    const candidates = mapping[shortLabel];
    if (!candidates || candidates.length === 0) {
        console.debug('[NodeMapping] No candidates found for:', shortLabel);
        return {
            resolved: false,
            fallbackAction: {
                symbol: shortLabel,
                file_hint: currentFiles[0]?.path || 'unknown'
            }
        };
    }

    console.debug('[NodeMapping] Found', candidates.length, 'candidates for:', shortLabel);

    // If single candidate, return it
    if (candidates.length === 1) {
        console.debug('[NodeMapping] Single candidate resolved:', candidates[0]);
        return {
            resolved: true,
            node: candidates[0]
        };
    }

    // Multiple candidates - apply resolution strategy
    const currentFilePaths = new Set(currentFiles.map(f => f.path));

    // Step 1: Prefer candidates whose file_path exists in current hits
    const fileMatchedCandidates = candidates.filter(candidate =>
        currentFilePaths.has(candidate.file_path)
    );

    if (fileMatchedCandidates.length === 1) {
        console.debug('[NodeMapping] Resolved by file match:', fileMatchedCandidates[0]);
        return {
            resolved: true,
            node: fileMatchedCandidates[0]
        };
    }

    if (fileMatchedCandidates.length > 1) {
        // Step 2: Among file-matched candidates, prefer highlighted nodes
        const highlightedCandidates = fileMatchedCandidates.filter(candidate =>
            highlightedNodes.includes(candidate.node_id)
        );

        if (highlightedCandidates.length > 0) {
            console.debug('[NodeMapping] Resolved by highlight match:', highlightedCandidates[0]);
            return {
                resolved: true,
                node: highlightedCandidates[0]
            };
        }

        // Return first file-matched candidate
        console.debug('[NodeMapping] Resolved by first file match:', fileMatchedCandidates[0]);
        return {
            resolved: true,
            node: fileMatchedCandidates[0]
        };
    }

    // No file matches - prefer highlighted nodes
    const highlightedCandidates = candidates.filter(candidate =>
        highlightedNodes.includes(candidate.node_id)
    );

    if (highlightedCandidates.length > 0) {
        console.debug('[NodeMapping] Resolved by highlight match (no file match):', highlightedCandidates[0]);
        return {
            resolved: true,
            node: highlightedCandidates[0]
        };
    }

    // Return first candidate as fallback
    console.debug('[NodeMapping] Resolved by first candidate:', candidates[0]);
    return {
        resolved: true,
        node: candidates[0],
        candidates: candidates
    };
}
