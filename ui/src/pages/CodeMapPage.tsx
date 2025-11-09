// frontend/src/pages/CodeMapPage.tsx
import React, { useState, useEffect, useRef } from 'react';
import { ConfigProvider, theme, App as AntdApp, Card, Button, Typography, Spin, Alert, Tabs, Input, Space } from 'antd';
import { CodeOutlined, FileTextOutlined, InfoCircleOutlined, SearchOutlined, NodeIndexOutlined, MenuFoldOutlined, MenuUnfoldOutlined, CloseOutlined } from '@ant-design/icons';
import mermaid from 'mermaid';
import svgPanZoom from 'svg-pan-zoom';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;

interface CodeMapPageProps { }

interface GraphNode {
    id: string;
    file_path: string;
    name: string;
    kind: string;
    start_line: number;
    end_line: number;
    text: string;
    language: string;
}

interface GraphEdge {
    src: string;
    dst: string;
    type: string;
    file_path: string;
}

interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

interface NodeDetails {
    id: string;
    name: string;
    file_path: string;
    kind: string;
    start_line: number;
    end_line: number;
    text: string;
    language: string;
}

// Make sure the window object knows about our function
declare global {
    interface Window {
        handleNodeClick: (nodeId: string) => void;
    }
}

export const CodeMapPage: React.FC<CodeMapPageProps> = () => {
    const [graphData, setGraphData] = useState<GraphData | null>(null);
    const [mermaidString, setMermaidString] = useState<string>('');
    const [selectedNode, setSelectedNode] = useState<NodeDetails | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState<string>('');
    const [hasSearched, setHasSearched] = useState(false);

    // Panel visibility state
    const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState(false);
    const [isRightPanelCollapsed, setIsRightPanelCollapsed] = useState(true); // Right panel starts collapsed

    // Create a ref for the SVG container
    const svgRef = useRef<HTMLDivElement>(null);

    // Search functionality
    const handleSearch = async () => {
        if (!searchQuery.trim()) {
            setError('Please enter a search query');
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            setSelectedNode(null);

            const response = await fetch(`/api/codemap/local_graph?query=${encodeURIComponent(searchQuery.trim())}`);
            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.status}`);
            }

            const data = await response.json();
            console.log('Received local graph data from API:', data);
            setGraphData(data);
            setHasSearched(true);

        } catch (err) {
            console.error('Failed to fetch local graph data:', err);
            setError(err instanceof Error ? err.message : 'Failed to load graph data.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSearch();
        }
    };

    // Graph generation logic with three-level layout
    useEffect(() => {
        if (graphData && graphData.nodes && graphData.edges) {
            const generateMermaidString = () => {
                let mermaidStr = 'graph LR\n';

                // Define node styles
                mermaidStr += '    classDef highLevel fill:#ff6b6b,stroke:#d63031,stroke-width:2px,color:#fff\n';
                mermaidStr += '    classDef midLevel fill:#4ecdc4,stroke:#00b894,stroke-width:2px,color:#fff\n';
                mermaidStr += '    classDef lowLevel fill:#45b7d1,stroke:#0984e3,stroke-width:2px,color:#fff\n';
                mermaidStr += '    classDef default fill:#f8f9fa,stroke:#6c757d,stroke-width:1px\n\n';

                // Create three subgraphs
                mermaidStr += '    subgraph "High-Level 入口/API"\n';
                mermaidStr += '        direction LR\n';

                // Categorize nodes based on file path and kind
                const highLevelNodes: GraphNode[] = [];
                const midLevelNodes: GraphNode[] = [];
                const lowLevelNodes: GraphNode[] = [];

                graphData.nodes.forEach(node => {
                    const filePath = node.file_path.toLowerCase();
                    const kind = node.kind.toLowerCase();

                    if (filePath.includes('routes') || filePath.includes('api') ||
                        kind.includes('route') || kind.includes('endpoint') ||
                        kind.includes('controller')) {
                        highLevelNodes.push(node);
                    } else if (filePath.includes('services') || filePath.includes('business') ||
                        kind.includes('service') || kind.includes('business') ||
                        kind.includes('handler')) {
                        midLevelNodes.push(node);
                    } else {
                        lowLevelNodes.push(node);
                    }
                });

                // Add high-level nodes
                highLevelNodes.forEach(node => {
                    const nodeId = `node_${node.id}`;
                    const nodeLabel = `${node.name}\\n(${node.kind})`;
                    mermaidStr += `        ${nodeId}["${nodeLabel}"]\n`;
                });
                mermaidStr += '    end\n\n';

                mermaidStr += '    subgraph "Mid-Level 服务/业务"\n';
                mermaidStr += '        direction LR\n';

                // Add mid-level nodes
                midLevelNodes.forEach(node => {
                    const nodeId = `node_${node.id}`;
                    const nodeLabel = `${node.name}\\n(${node.kind})`;
                    mermaidStr += `        ${nodeId}["${nodeLabel}"]\n`;
                });
                mermaidStr += '    end\n\n';

                mermaidStr += '    subgraph "Low-Level 工具/适配"\n';
                mermaidStr += '        direction LR\n';

                // Add low-level nodes
                lowLevelNodes.forEach(node => {
                    const nodeId = `node_${node.id}`;
                    const nodeLabel = `${node.name}\\n(${node.kind})`;
                    mermaidStr += `        ${nodeId}["${nodeLabel}"]\n`;
                });
                mermaidStr += '    end\n\n';

                // Add edges
                graphData.edges.forEach(edge => {
                    const srcId = `node_${edge.src}`;
                    const dstId = `node_${edge.dst}`;
                    mermaidStr += `    ${srcId} --> ${dstId}\n`;
                });

                // Apply styles
                mermaidStr += '\n';
                highLevelNodes.forEach(node => {
                    mermaidStr += `    class node_${node.id} highLevel\n`;
                });
                midLevelNodes.forEach(node => {
                    mermaidStr += `    class node_${node.id} midLevel\n`;
                });
                lowLevelNodes.forEach(node => {
                    mermaidStr += `    class node_${node.id} lowLevel\n`;
                });

                return mermaidStr;
            };

            const mermaidStr = generateMermaidString();
            console.log('Generated Mermaid string:', mermaidStr);
            setMermaidString(mermaidStr);
        }
    }, [graphData]);

    // Initialize Mermaid and render graph with pan-zoom
    useEffect(() => {
        if (mermaidString && graphData) {
            // 1. Define the click handler that the SVG nodes will call
            window.handleNodeClick = (nodeId: string) => {
                console.log('handleNodeClick called with nodeId:', nodeId);

                // 尝试多种方式提取节点ID
                let actualNodeId = nodeId;

                // 处理不同的节点ID格式
                if (nodeId.startsWith('node_')) {
                    actualNodeId = nodeId.replace('node_', '');
                } else if (nodeId.startsWith('flowchart-')) {
                    // 从flowchart-xxx格式中提取ID
                    const parts = nodeId.split('-');
                    if (parts.length > 1) {
                        actualNodeId = parts.slice(1).join('-');
                    }
                } else if (nodeId.includes('::')) {
                    // 处理包含::的节点ID
                    actualNodeId = nodeId;
                }

                console.log('Extracted node ID:', actualNodeId);

                // 尝试多种方式查找节点
                let node = graphData.nodes.find(n => n.id === actualNodeId);

                // 如果直接匹配失败，尝试通过名称匹配
                if (!node) {
                    node = graphData.nodes.find(n => n.name === actualNodeId);
                }

                // 如果还是找不到，尝试部分匹配
                if (!node) {
                    node = graphData.nodes.find(n =>
                        n.name.includes(actualNodeId) ||
                        actualNodeId.includes(n.name) ||
                        n.file_path.includes(actualNodeId) ||
                        actualNodeId.includes(n.file_path)
                    );
                }

                // 如果仍然找不到，尝试从节点ID中提取函数名进行匹配
                if (!node && actualNodeId.includes('::')) {
                    const functionName = actualNodeId.split('::').pop();
                    if (functionName) {
                        node = graphData.nodes.find(n => n.name === functionName);
                    }
                }

                if (node) {
                    console.log('Found node details:', node);
                    setSelectedNode({
                        id: node.id,
                        name: node.name,
                        file_path: node.file_path,
                        kind: node.kind,
                        start_line: node.start_line,
                        end_line: node.end_line,
                        text: node.text,
                        language: node.language
                    });
                    // Auto-expand right panel when node is selected
                    setIsRightPanelCollapsed(false);
                } else {
                    console.log('No details found for node:', nodeId);
                    console.log('Extracted node ID:', actualNodeId);
                    console.log('Available nodes:', graphData.nodes.map(n => ({ id: n.id, name: n.name })));

                    // 创建一个临时的节点对象用于显示基本信息
                    const tempNode = {
                        id: actualNodeId,
                        name: actualNodeId.split('::').pop() || actualNodeId,
                        file_path: actualNodeId.includes('::') ? actualNodeId.split('::')[0] : 'Unknown',
                        kind: 'unknown',
                        start_line: 0,
                        end_line: 0,
                        text: 'No detailed information available',
                        language: 'unknown'
                    };

                    console.log('Creating temporary node:', tempNode);
                    setSelectedNode(tempNode);
                    setIsRightPanelCollapsed(false);
                }
            };

            const renderMermaid = async () => {
                try {
                    // Initialize Mermaid
                    mermaid.initialize({
                        startOnLoad: false,
                        theme: 'dark',
                        securityLevel: 'loose'
                    });

                    // 2. Find the container and render the graph
                    const mermaidContainer = document.getElementById('mermaid-container');
                    if (mermaidContainer) {
                        // Clear the container
                        mermaidContainer.innerHTML = '';
                        const graphId = `graph-${Date.now()}`;

                        // 3. Render the graph and attach pan-zoom AFTER rendering
                        const { svg } = await mermaid.render(graphId, mermaidString);
                        mermaidContainer.innerHTML = svg;

                        // 4. Attach pan-zoom AFTER the SVG is in the DOM
                        const svgElement = mermaidContainer.querySelector('svg');
                        if (svgElement) {
                            // 强制SVG填充整个容器
                            svgElement.style.width = '100%';
                            svgElement.style.height = '100%';
                            svgElement.style.minHeight = '400px';
                            svgElement.style.display = 'block';

                            // 确保SVG的viewBox正确设置以填充容器
                            const adjustSVGSize = () => {
                                const containerRect = mermaidContainer.getBoundingClientRect();
                                if (containerRect.width > 0 && containerRect.height > 0) {
                                    svgElement.setAttribute('viewBox', `0 0 ${containerRect.width} ${containerRect.height}`);
                                    svgElement.style.width = '100%';
                                    svgElement.style.height = '100%';
                                }
                            };

                            // 立即调整一次
                            adjustSVGSize();

                            // 延迟调整，确保容器完全渲染
                            setTimeout(adjustSVGSize, 100);
                            setTimeout(adjustSVGSize, 500);

                            // Add click event listeners to all nodes in the rendered SVG
                            // 更全面的节点选择器，包括所有可能的节点元素
                            const nodeElements = svgElement.querySelectorAll(`
                                [id*="node"], 
                                [id*="flowchart"], 
                                .node, 
                                rect[id], 
                                circle[id], 
                                ellipse[id],
                                g[id*="node"],
                                g[id*="flowchart"],
                                text[id*="node"],
                                text[id*="flowchart"]
                            `);

                            console.log('Found node elements:', nodeElements.length);

                            nodeElements.forEach((element) => {
                                (element as HTMLElement).style.cursor = 'pointer';

                                // 为节点添加视觉反馈
                                element.addEventListener('mouseenter', () => {
                                    (element as HTMLElement).style.opacity = '0.8';
                                });

                                element.addEventListener('mouseleave', () => {
                                    (element as HTMLElement).style.opacity = '1';
                                });

                                element.addEventListener('click', (event) => {
                                    event.stopPropagation();
                                    // Extract node ID from the element's ID or data attributes
                                    const nodeId = element.id || element.getAttribute('data-node-id') || 'unknown';
                                    console.log('Node clicked:', nodeId);
                                    console.log('Element:', element);
                                    window.handleNodeClick(nodeId);
                                });
                            });

                            // Initialize svg-pan-zoom
                            const panZoomInstance = svgPanZoom(svgElement, {
                                zoomEnabled: true,
                                controlIconsEnabled: true,
                                fit: true,
                                center: true,
                                minZoom: 0.5,
                                maxZoom: 10,
                            });

                            // Handle window resize
                            const handleResize = () => {
                                // 重新调整SVG大小
                                const containerRect = mermaidContainer.getBoundingClientRect();
                                if (containerRect.width > 0 && containerRect.height > 0) {
                                    svgElement.setAttribute('viewBox', `0 0 ${containerRect.width} ${containerRect.height}`);
                                    svgElement.style.width = '100%';
                                    svgElement.style.height = '100%';
                                }

                                panZoomInstance.resize();
                                panZoomInstance.fit();
                                panZoomInstance.center();
                            };
                            window.addEventListener('resize', handleResize);

                            // Store the instance for cleanup
                            (mermaidContainer as any).panZoomInstance = panZoomInstance;
                            (mermaidContainer as any).handleResize = handleResize;

                            console.log('Mermaid graph rendered successfully with pan-zoom');
                        }
                    }
                } catch (err) {
                    console.error('Mermaid rendering error:', err);
                    setError(`Graph rendering failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
                }
            };

            renderMermaid();
        }

        // Cleanup function
        return () => {
            const mermaidContainer = document.getElementById('mermaid-container');
            if (mermaidContainer) {
                const panZoomInstance = (mermaidContainer as any).panZoomInstance;
                const handleResize = (mermaidContainer as any).handleResize;

                if (panZoomInstance) {
                    panZoomInstance.destroy();
                }
                if (handleResize) {
                    window.removeEventListener('resize', handleResize);
                }
            }
            // Cleanup global click handler
            delete (window as any).handleNodeClick;
        };
    }, [mermaidString, graphData]);


    if (isLoading) {
        return (
            <ConfigProvider
                theme={{
                    algorithm: theme.darkAlgorithm,
                }}
            >
                <AntdApp>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        height: '100vh',
                        flexDirection: 'column',
                        gap: '16px'
                    }}>
                        <Spin size="large" />
                        <Text>Searching for connections...</Text>
                    </div>
                </AntdApp>
            </ConfigProvider>
        );
    }

    return (
        <ConfigProvider
            theme={{
                algorithm: theme.darkAlgorithm,
            }}
        >
            <AntdApp>
                <div style={{
                    display: 'flex',
                    flex: 1,
                    height: '100vh',
                    backgroundColor: '#141414'
                }}>
                    {/* Left Panel - Search and Controls */}
                    <div style={{
                        width: isLeftPanelCollapsed ? '0px' : '300px',
                        minWidth: isLeftPanelCollapsed ? '0px' : '300px',
                        overflow: 'hidden',
                        transition: 'width 0.3s ease',
                        borderRight: isLeftPanelCollapsed ? 'none' : '1px solid #303030',
                        backgroundColor: '#1f1f1f',
                        display: 'flex',
                        flexDirection: 'column'
                    }}>
                        {!isLeftPanelCollapsed && (
                            <>
                                <div style={{
                                    padding: '16px',
                                    borderBottom: '1px solid #303030'
                                }}>
                                    <div style={{
                                        display: 'flex',
                                        justifyContent: 'space-between',
                                        alignItems: 'center',
                                        marginBottom: '16px'
                                    }}>
                                        <Title level={5} style={{ margin: 0, color: '#fff' }}>
                                            Search & Controls
                                        </Title>
                                        <Button
                                            type="text"
                                            icon={<MenuFoldOutlined />}
                                            onClick={() => setIsLeftPanelCollapsed(true)}
                                            style={{ color: '#8c8c8c' }}
                                        />
                                    </div>

                                    {/* Search Bar */}
                                    <Space.Compact style={{ width: '100%' }}>
                                        <Input
                                            placeholder="Search for a function or file..."
                                            value={searchQuery}
                                            onChange={(e) => setSearchQuery(e.target.value)}
                                            onKeyPress={handleKeyPress}
                                            prefix={<SearchOutlined />}
                                            size="middle"
                                            style={{ backgroundColor: '#2a2a2a', borderColor: '#404040', color: '#fff' }}
                                        />
                                        <Button
                                            type="primary"
                                            onClick={handleSearch}
                                            size="middle"
                                            icon={<SearchOutlined />}
                                        >
                                            Search
                                        </Button>
                                    </Space.Compact>
                                    {error && (
                                        <Alert
                                            message={error}
                                            type="error"
                                            showIcon
                                            style={{ marginTop: '12px' }}
                                            closable
                                            onClose={() => setError(null)}
                                        />
                                    )}
                                </div>

                                <div style={{ padding: '16px', flex: 1, overflow: 'auto' }}>
                                    {graphData && (
                                        <Card size="small" style={{ marginBottom: '16px', backgroundColor: '#2a2a2a' }}>
                                            <Text type="secondary" style={{ fontSize: '12px', color: '#8c8c8c' }}>
                                                {graphData.nodes.length} nodes, {graphData.edges.length} edges
                                            </Text>
                                        </Card>
                                    )}
                                </div>
                            </>
                        )}
                    </div>

                    {/* Center Panel - Graph */}
                    <div style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        position: 'relative'
                    }}>
                        {/* Top bar with title and controls */}
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: '16px',
                            borderBottom: '1px solid #303030',
                            backgroundColor: '#1f1f1f'
                        }}>
                            <Title level={4} style={{ margin: 0, color: '#fff' }}>
                                Code Map Explorer
                            </Title>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <Button
                                    type="text"
                                    icon={isLeftPanelCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                                    onClick={() => setIsLeftPanelCollapsed(!isLeftPanelCollapsed)}
                                    style={{ color: '#8c8c8c' }}
                                    title={isLeftPanelCollapsed ? 'Show left panel' : 'Hide left panel'}
                                />
                                {selectedNode && !isRightPanelCollapsed && (
                                    <Button
                                        type="text"
                                        icon={<MenuFoldOutlined />}
                                        onClick={() => setIsRightPanelCollapsed(true)}
                                        style={{ color: '#8c8c8c' }}
                                        title="Hide right panel"
                                    />
                                )}
                            </div>
                        </div>

                        {/* Graph container */}
                        <div style={{
                            flex: 1,
                            overflow: 'hidden',
                            backgroundColor: '#1f1f1f',
                            display: 'flex',
                            flexDirection: 'column',
                            minHeight: 'calc(100vh - 120px)' // 确保最小高度
                        }}>
                            {mermaidString ? (
                                <div style={{
                                    flex: 1,
                                    display: 'flex',
                                    flexDirection: 'column',
                                    overflow: 'hidden',
                                    position: 'relative',
                                    width: '100%',
                                    minHeight: 'calc(100vh - 200px)' // 为图表设置最小高度
                                }}>
                                    <div ref={svgRef} id="mermaid-container" style={{
                                        width: '100%',
                                        height: '100%',
                                        flex: 1,
                                        position: 'relative',
                                        minHeight: '400px', // 确保图表容器有足够的最小高度
                                        display: 'flex',
                                        alignItems: 'stretch',
                                        justifyContent: 'stretch'
                                    }}>
                                    </div>
                                </div>
                            ) : (
                                <div
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        height: '100%',
                                        flexDirection: 'column',
                                        gap: '16px',
                                        textAlign: 'center',
                                        padding: '40px',
                                        flex: 1
                                    }}
                                >
                                    <NodeIndexOutlined style={{ fontSize: '64px', color: '#8c8c8c' }} />
                                    <Title level={3} style={{ color: '#fff', margin: 0 }}>
                                        Search for a function or file
                                    </Title>
                                    <Paragraph style={{ color: '#8c8c8c', fontSize: '16px', maxWidth: '500px' }}>
                                        Enter the name or ID of a function, class, or file to visualize its connections and dependencies.
                                        This will show you a focused, local graph centered around your search term.
                                    </Paragraph>
                                    <Text type="secondary" style={{ fontSize: '14px' }}>
                                        Example: Try searching for a function name, class name, or file path
                                    </Text>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Right Panel - Node Details */}
                    {selectedNode && !isRightPanelCollapsed && (
                        <div style={{
                            width: '400px',
                            borderLeft: '1px solid #303030',
                            backgroundColor: '#1f1f1f',
                            display: 'flex',
                            flexDirection: 'column'
                        }}>
                            <div style={{
                                padding: '16px',
                                borderBottom: '1px solid #303030',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <Title level={5} style={{ margin: 0, color: '#fff' }}>
                                    Node Details
                                </Title>
                                <Button
                                    type="text"
                                    icon={<CloseOutlined />}
                                    onClick={() => {
                                        setSelectedNode(null);
                                        setIsRightPanelCollapsed(true);
                                    }}
                                    style={{ color: '#8c8c8c' }}
                                    title="Close details panel"
                                />
                            </div>

                            <div style={{ flex: 1, overflow: 'auto', padding: '16px' }}>
                                <Card size="small" style={{ marginBottom: '16px', backgroundColor: '#2a2a2a' }}>
                                    <Tabs defaultActiveKey="overview" size="small">
                                        <TabPane tab={<span><InfoCircleOutlined />Overview</span>} key="overview">
                                            <div style={{ marginBottom: '16px' }}>
                                                <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
                                                    {selectedNode.name}
                                                </Text>
                                            </div>

                                            {/* 函数主要介绍 */}
                                            <div style={{
                                                marginBottom: '16px',
                                                padding: '12px',
                                                backgroundColor: '#1a1a1a',
                                                borderRadius: '6px',
                                                border: '1px solid #404040'
                                            }}>
                                                <Text strong style={{ fontSize: '13px', color: '#fff', display: 'block', marginBottom: '8px' }}>
                                                    📋 Function Overview
                                                </Text>
                                                <Text style={{ fontSize: '12px', color: '#d9d9d9', lineHeight: '1.5' }}>
                                                    {selectedNode.kind === 'function' || selectedNode.kind === 'method'
                                                        ? `This ${selectedNode.kind} is located in ${selectedNode.file_path.split('/').pop()} and spans from line ${selectedNode.start_line} to ${selectedNode.end_line}. It's written in ${selectedNode.language}.`
                                                        : `This ${selectedNode.kind} is part of the codebase structure.`
                                                    }
                                                </Text>
                                            </div>

                                            <div style={{ marginBottom: '8px' }}>
                                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                                    📁 {selectedNode.file_path}
                                                </Text>
                                            </div>
                                            <div style={{ marginBottom: '8px' }}>
                                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                                    🏷️ Type: {selectedNode.kind}
                                                </Text>
                                            </div>
                                            <div style={{ marginBottom: '8px' }}>
                                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                                    📍 Lines: {selectedNode.start_line}-{selectedNode.end_line}
                                                </Text>
                                            </div>
                                            <div>
                                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                                    🔤 Language: {selectedNode.language}
                                                </Text>
                                            </div>
                                        </TabPane>
                                        <TabPane tab={<span><FileTextOutlined />Description</span>} key="description">
                                            <div>
                                                <Text strong style={{ fontSize: '13px', color: '#fff', display: 'block', marginBottom: '12px' }}>
                                                    📝 Function Description
                                                </Text>

                                                {/* 函数详细描述 */}
                                                <div style={{
                                                    marginBottom: '16px',
                                                    padding: '12px',
                                                    backgroundColor: '#1a1a1a',
                                                    borderRadius: '6px',
                                                    border: '1px solid #404040'
                                                }}>
                                                    <Text style={{ fontSize: '12px', color: '#d9d9d9', lineHeight: '1.6' }}>
                                                        {selectedNode.kind === 'function' || selectedNode.kind === 'method'
                                                            ? `The function "${selectedNode.name}" is a ${selectedNode.kind} that plays an important role in the codebase. It's implemented in ${selectedNode.language} and located in the file ${selectedNode.file_path.split('/').pop()}. The function spans ${selectedNode.end_line - selectedNode.start_line + 1} lines of code (from line ${selectedNode.start_line} to ${selectedNode.end_line}), indicating it's a ${selectedNode.end_line - selectedNode.start_line + 1 > 20 ? 'substantial' : 'concise'} implementation.`
                                                            : `This ${selectedNode.kind} "${selectedNode.name}" is an important component of the codebase structure. It's defined in ${selectedNode.file_path.split('/').pop()} and spans from line ${selectedNode.start_line} to ${selectedNode.end_line}.`
                                                        }
                                                    </Text>
                                                </div>

                                                {/* 技术细节 */}
                                                <div style={{
                                                    marginBottom: '16px',
                                                    padding: '12px',
                                                    backgroundColor: '#1a1a1a',
                                                    borderRadius: '6px',
                                                    border: '1px solid #404040'
                                                }}>
                                                    <Text strong style={{ fontSize: '12px', color: '#fff', display: 'block', marginBottom: '8px' }}>
                                                        🔧 Technical Details
                                                    </Text>
                                                    <div style={{ marginBottom: '6px' }}>
                                                        <Text style={{ fontSize: '11px', color: '#8c8c8c' }}>
                                                            <strong>File:</strong> {selectedNode.file_path}
                                                        </Text>
                                                    </div>
                                                    <div style={{ marginBottom: '6px' }}>
                                                        <Text style={{ fontSize: '11px', color: '#8c8c8c' }}>
                                                            <strong>Language:</strong> {selectedNode.language}
                                                        </Text>
                                                    </div>
                                                    <div style={{ marginBottom: '6px' }}>
                                                        <Text style={{ fontSize: '11px', color: '#8c8c8c' }}>
                                                            <strong>Type:</strong> {selectedNode.kind}
                                                        </Text>
                                                    </div>
                                                    <div>
                                                        <Text style={{ fontSize: '11px', color: '#8c8c8c' }}>
                                                            <strong>Lines:</strong> {selectedNode.start_line}-{selectedNode.end_line} ({selectedNode.end_line - selectedNode.start_line + 1} lines)
                                                        </Text>
                                                    </div>
                                                </div>
                                            </div>
                                        </TabPane>
                                        <TabPane tab={<span><CodeOutlined />Code</span>} key="code">
                                            <div>
                                                <Text strong style={{ fontSize: '12px', color: '#fff' }}>
                                                    Code Snippet:
                                                </Text>
                                                <pre style={{
                                                    fontSize: '11px',
                                                    backgroundColor: '#1a1a1a',
                                                    padding: '8px',
                                                    borderRadius: '4px',
                                                    marginTop: '8px',
                                                    maxHeight: '300px',
                                                    overflow: 'auto',
                                                    color: '#fff',
                                                    border: '1px solid #404040'
                                                }}>
                                                    {selectedNode.text || 'No code snippet available'}
                                                </pre>
                                            </div>
                                        </TabPane>
                                    </Tabs>
                                </Card>
                            </div>
                        </div>
                    )}

                    {/* Right panel placeholder when no node is selected */}
                    {!selectedNode && !isRightPanelCollapsed && (
                        <div style={{
                            width: '400px',
                            borderLeft: '1px solid #303030',
                            backgroundColor: '#1f1f1f',
                            display: 'flex',
                            flexDirection: 'column'
                        }}>
                            <div style={{
                                padding: '16px',
                                borderBottom: '1px solid #303030',
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center'
                            }}>
                                <Title level={5} style={{ margin: 0, color: '#fff' }}>
                                    Node Details
                                </Title>
                                <Button
                                    type="text"
                                    icon={<MenuFoldOutlined />}
                                    onClick={() => setIsRightPanelCollapsed(true)}
                                    style={{ color: '#8c8c8c' }}
                                    title="Hide right panel"
                                />
                            </div>

                            <div style={{
                                flex: 1,
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '16px',
                                padding: '20px',
                                textAlign: 'center'
                            }}>
                                <FileTextOutlined style={{ fontSize: '48px', color: '#8c8c8c' }} />
                                <div>
                                    <Text type="secondary" style={{ fontSize: '14px', color: '#8c8c8c' }}>
                                        {hasSearched ? 'Click on a node in the graph to see details' : 'Search for a function or file to see its connections'}
                                    </Text>
                                </div>
                                <Paragraph style={{ fontSize: '12px', color: '#666', margin: 0 }}>
                                    {hasSearched
                                        ? 'This local graph shows the connections around your searched term. Click on any node to explore its details.'
                                        : 'The Code Map Explorer lets you search for specific functions, classes, or files to visualize their connections and dependencies. This focused approach helps you understand code relationships without overwhelming detail.'
                                    }
                                </Paragraph>
                            </div>
                        </div>
                    )}
                </div>
            </AntdApp>
        </ConfigProvider>
    );
};

export default CodeMapPage;
