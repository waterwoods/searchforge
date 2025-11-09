// frontend/src/pages/GraphViewerPage.tsx
import React, { useState, useEffect, useRef } from 'react';
import { ConfigProvider, theme, App as AntdApp, Card, Button, Typography, Spin, Alert, message } from 'antd';
import { CopyOutlined, ReloadOutlined } from '@ant-design/icons';
import { useSearchParams } from 'react-router-dom';
import mermaid from 'mermaid';
import svgPanZoom from 'svg-pan-zoom';

const { Title, Text } = Typography;

interface GraphViewerPageProps { }

interface GraphData {
    mermaidText: string;
    nodeDetails: Record<string, any>;
}

interface NodeDetails {
    code: string;
    filePath: string;
}

// Make sure the window object knows about our function
declare global {
    interface Window {
        handleNodeClick: (nodeId: string) => void;
    }
}

export const GraphViewerPage: React.FC<GraphViewerPageProps> = () => {
    const [searchParams] = useSearchParams();
    const requestId = searchParams.get('requestId');
    const query = searchParams.get('query');
    const themeParam = searchParams.get('theme') || 'dark';

    const [graphData, setGraphData] = useState<GraphData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedNode, setSelectedNode] = useState<NodeDetails | null>(null);

    // Create a ref for the SVG container
    const svgRef = useRef<HTMLDivElement>(null);

    // Fetch data on component mount
    const fetchGraphData = async () => {
        if (!query) {
            setError('Missing query parameter');
            setLoading(false);
            return;
        }

        try {
            setLoading(true);
            setError(null);

            const response = await fetch('/api/graph/direct_from_query', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch data: ${response.status}`);
            }

            const data = await response.json();
            console.log('Received graph data from API:', data);
            console.log('Mermaid text:', data.mermaidText);
            console.log('Node details:', data.nodeDetails);
            setGraphData(data);

        } catch (err) {
            console.error('Failed to fetch graph data:', err);
            setError(err instanceof Error ? err.message : 'Failed to load graph data.');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchGraphData();
    }, [query]);

    // Initialize Mermaid and render graph with pan-zoom
    useEffect(() => {
        if (graphData && graphData.mermaidText && svgRef.current) {
            const renderMermaid = async () => {
                try {
                    // Log the final Mermaid string that is being passed to Mermaid component
                    console.log('Final Mermaid string:', graphData.mermaidText);

                    // Initialize Mermaid
                    mermaid.initialize({
                        startOnLoad: false,
                        theme: themeParam === 'dark' ? 'dark' : 'default',
                        securityLevel: 'loose'
                    });

                    // Clear the container and render the graph
                    svgRef.current!.innerHTML = '';
                    const graphId = `graph-${Date.now()}`;

                    // Render the graph
                    const { svg } = await mermaid.render(graphId, graphData.mermaidText);
                    svgRef.current!.innerHTML = svg;

                    // Find the SVG element that Mermaid created
                    const svgElement = svgRef.current!.querySelector('svg');
                    if (svgElement) {
                        // Add click event listeners to all nodes in the rendered SVG
                        const nodeElements = svgElement.querySelectorAll('[id*="node"], .node, rect[id], circle[id], ellipse[id]');

                        nodeElements.forEach((element) => {
                            element.style.cursor = 'pointer';
                            element.addEventListener('click', (event) => {
                                event.stopPropagation();
                                // Extract node ID from the element's ID or data attributes
                                const nodeId = element.id || element.getAttribute('data-node-id') || 'unknown';
                                console.log('Node clicked:', nodeId);
                                window.handleNodeClick(nodeId);
                            });
                        });

                        // Initialize svg-pan-zoom
                        const panZoomInstance = svgPanZoom(svgElement, {
                            zoomEnabled: true,
                            controlIconsEnabled: true, // This adds the +/- zoom buttons!
                            fit: true,                 // This makes it fit to screen on load!
                            center: true,              // This centers it on load!
                            minZoom: 0.5,
                            maxZoom: 10,
                        });

                        // Handle window resize
                        const handleResize = () => {
                            panZoomInstance.resize();
                            panZoomInstance.fit();
                            panZoomInstance.center();
                        };
                        window.addEventListener('resize', handleResize);

                        // Store the instance for cleanup
                        (svgRef.current as any).panZoomInstance = panZoomInstance;
                        (svgRef.current as any).handleResize = handleResize;

                        console.log('Mermaid graph rendered successfully with pan-zoom');
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
            if (svgRef.current) {
                const panZoomInstance = (svgRef.current as any).panZoomInstance;
                const handleResize = (svgRef.current as any).handleResize;

                if (panZoomInstance) {
                    panZoomInstance.destroy();
                }
                if (handleResize) {
                    window.removeEventListener('resize', handleResize);
                }
            }
        };
    }, [graphData, themeParam]);

    // Set up global node click handler
    useEffect(() => {
        window.handleNodeClick = (nodeId: string) => {
            console.log('handleNodeClick called with nodeId:', nodeId);
            const details = graphData?.nodeDetails[nodeId];
            if (details) {
                console.log('Found node details:', details);
                setSelectedNode(details);
            } else {
                console.log('No details found for node:', nodeId);
                // Set a fallback node details object
                setSelectedNode({
                    code: `Node ID: ${nodeId}`,
                    filePath: 'No details available'
                });
            }
        };

        // Cleanup function to remove it when component unmounts
        return () => {
            delete window.handleNodeClick;
        };
    }, [graphData]);

    // Copy Query to clipboard
    const copyQuery = () => {
        if (query) {
            navigator.clipboard.writeText(query);
            message.success('Query copied to clipboard');
        }
    };

    // Retry loading
    const retry = () => {
        fetchGraphData();
    };

    if (loading) {
        return (
            <ConfigProvider
                theme={{
                    algorithm: themeParam === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
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
                        <Text>Loading graph data...</Text>
                    </div>
                </AntdApp>
            </ConfigProvider>
        );
    }

    if (error) {
        return (
            <ConfigProvider
                theme={{
                    algorithm: themeParam === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
                }}
            >
                <AntdApp>
                    <div style={{
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        height: '100vh',
                        flexDirection: 'column',
                        gap: '16px',
                        padding: '20px'
                    }}>
                        <Alert
                            message="Failed to load graph"
                            description={error}
                            type="error"
                            showIcon
                            style={{ maxWidth: '500px' }}
                        />
                        <div style={{ display: 'flex', gap: '8px' }}>
                            <Button icon={<ReloadOutlined />} onClick={retry}>
                                Retry
                            </Button>
                            {query && (
                                <Button icon={<CopyOutlined />} onClick={copyQuery}>
                                    Copy Query
                                </Button>
                            )}
                        </div>
                    </div>
                </AntdApp>
            </ConfigProvider>
        );
    }

    return (
        <ConfigProvider
            theme={{
                algorithm: themeParam === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
            }}
        >
            <AntdApp>
                <div style={{
                    display: 'flex',
                    height: '100vh',
                    backgroundColor: themeParam === 'dark' ? '#141414' : '#ffffff'
                }}>
                    {/* Left side - Graph */}
                    <div style={{
                        flex: 1,
                        padding: '16px',
                        display: 'flex',
                        flexDirection: 'column'
                    }}>
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            marginBottom: '16px'
                        }}>
                            <Title level={4} style={{ margin: 0 }}>
                                Code Flow Graph
                            </Title>
                            <div style={{ display: 'flex', gap: '8px' }}>
                                <Text type="secondary" style={{ fontSize: '12px' }}>
                                    Query: {query}
                                </Text>
                                <Button
                                    size="small"
                                    icon={<CopyOutlined />}
                                    onClick={copyQuery}
                                >
                                    Copy Query
                                </Button>
                            </div>
                        </div>

                        <Card style={{ flex: 1, overflow: 'hidden' }}>
                            {graphData?.mermaidText ? (
                                <div ref={svgRef} className="mermaid-container" style={{
                                    width: '100%',
                                    height: '100%',
                                    display: 'flex',
                                    justifyContent: 'center',
                                    alignItems: 'center'
                                }}>
                                </div>
                            ) : (
                                <div
                                    data-testid="empty-graph-msg"
                                    style={{
                                        display: 'flex',
                                        justifyContent: 'center',
                                        alignItems: 'center',
                                        height: '100%',
                                        flexDirection: 'column',
                                        gap: '16px'
                                    }}
                                >
                                    <Text type="secondary">No graph data available</Text>
                                    <Button onClick={retry}>
                                        Retry
                                    </Button>
                                </div>
                            )}
                        </Card>
                    </div>

                    {/* Right side - Details Panel */}
                    <div style={{
                        width: '300px',
                        borderLeft: `1px solid ${themeParam === 'dark' ? '#303030' : '#d9d9d9'}`,
                        padding: '16px',
                        backgroundColor: themeParam === 'dark' ? '#1f1f1f' : '#fafafa',
                        overflowY: 'auto'
                    }}>
                        <Title level={5} style={{ marginBottom: '16px' }}>
                            Node Details
                        </Title>

                        {selectedNode ? (
                            <Card size="small" style={{ marginBottom: '16px' }} data-testid="node-detail">
                                <div style={{ marginBottom: '8px' }}>
                                    <Text strong style={{ fontSize: '12px', color: themeParam === 'dark' ? '#1890ff' : '#1890ff' }}>
                                        Selected Node: {selectedNode.code.includes('Node ID:') ? selectedNode.code.split(': ')[1] : 'Unknown'}
                                    </Text>
                                </div>
                                <div style={{ marginBottom: '8px' }}>
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                        📁 {selectedNode.filePath}
                                    </Text>
                                </div>
                                <div>
                                    <Text strong style={{ fontSize: '12px' }}>
                                        Details:
                                    </Text>
                                    <pre style={{
                                        fontSize: '11px',
                                        backgroundColor: themeParam === 'dark' ? '#2a2a2a' : '#f5f5f5',
                                        padding: '8px',
                                        borderRadius: '4px',
                                        marginTop: '4px',
                                        maxHeight: '200px',
                                        overflow: 'auto'
                                    }}>
                                        {selectedNode.code}
                                    </pre>
                                </div>
                            </Card>
                        ) : (
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                                Click on a node in the graph to see details
                            </Text>
                        )}
                    </div>
                </div>
            </AntdApp>
        </ConfigProvider>
    );
};

export default GraphViewerPage;
