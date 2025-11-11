import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import useGraphStore from '../graphStore';
import WorkflowPanel from './WorkflowPanel';
import RiskIndicator from './RiskIndicator';
import './EvidencePane.css';

const getApiBaseUrl = () => (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

const EvidencePane = () => {
    // Subscribe to selection and graph data from the shared store
    const { selectedNodeId, graphData } = useGraphStore();

    // Derive selected node from graph data
    const selectedNode = React.useMemo(() => {
        const nodes = graphData?.nodes || graphData?.results?.nodes || [];
        return nodes.find((n) => n.id === selectedNodeId) || null;
    }, [graphData, selectedNodeId]);

    // Derive basic evidence model if present on node data
    const selectedNodeEvidence = React.useMemo(() => {
        const ev = selectedNode?.data?.evidence;
        if (!ev || typeof ev !== 'object') return null;
        return {
            file: ev.file || null,
            span: ev.span || null,
            snippet: ev.snippet || null,
        };
    }, [selectedNode]);
    const [activeTab, setActiveTab] = useState('evidence');
    const [ragEvidence, setRagEvidence] = useState(null);
    const [ragLoading, setRagLoading] = useState(false);
    const [aiSummaryData, setAiSummaryData] = useState(null);
    const [aiSummaryLoading, setAiSummaryLoading] = useState(false);
    const [aiSummaryOpen, setAiSummaryOpen] = useState(true);
    const [analysis, setAnalysis] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [eventSource, setEventSource] = useState(null);
    // Markdown plugins loaded dynamically to avoid hard dependency
    const [markdownPlugins, setMarkdownPlugins] = useState([]);

    // Normalize streamed markdown that may be concatenated without newlines
    const normalizeMarkdown = (text) => {
        if (!text || typeof text !== 'string') return '';
        let t = text;
        // Ensure headings start on a new line
        t = t.replace(/([^\n])((?:#{2,6})\s)/g, '$1\n\n$2');
        // Ensure list items start on a new line
        t = t.replace(/([^\n])\s-\s/g, '$1\n- ');
        // Normalize multiple hashes stuck to text like 'details.###'
        t = t.replace(/\.(\s*)((?:#{2,6})\s)/g, '.\n\n$2');
        return t;
    };

    // Chat-related state
    const [chatMessages, setChatMessages] = useState([]);
    const [chatInput, setChatInput] = useState('');
    const [isChatting, setIsChatting] = useState(false);
    const chatMessagesEndRef = useRef(null);
    const messagesContainerRef = useRef(null);

    // Mock RAG API call simulation
    const fetchRAGEvidence = async (nodeId) => {
        setRagLoading(true);
        setRagEvidence(null);

        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Mock evidence based on node ID
        const mockEvidence = {
            'F211': "Commit #af8c: 'Refactored to handle legacy API. TODO: Optimize this in Q4.' - This function has been identified as a performance bottleneck in recent monitoring.",
            'F117': "Commit #b2d1: 'Added caching layer for improved performance.' - Recent optimization reduced latency by 40%.",
            'F391': "Commit #c3e2: 'Fixed memory leak in configuration parser.' - Critical bug fix that resolved production issues.",
            'F23': "Commit #d4f3: 'Implemented async processing for better scalability.' - Performance improvement for high-load scenarios.",
            'F50': "Commit #e5g4: 'Added comprehensive error handling and logging.' - Enhanced reliability and debugging capabilities.",
            'F87': "Commit #f6h5: 'Optimized database queries and connection pooling.' - Significant performance gains in data access layer."
        };

        const evidence = mockEvidence[nodeId] || `Commit #${Math.random().toString(16).substr(2, 4)}: 'Function ${nodeId} - Historical context and performance notes from codebase analysis.'`;

        setRagEvidence(evidence);
        setRagLoading(false);
    };

    // Fetch RAG evidence when node changes
    useEffect(() => {
        if (selectedNode?.id) {
            fetchRAGEvidence(selectedNode.id);
        } else {
            setRagEvidence(null);
            setRagLoading(false);
        }
    }, [selectedNode?.id]);

    // Fetch AI summary when node changes
    useEffect(() => {
        const fetchAiSummary = async (nodeId) => {
            setAiSummaryLoading(true);
            setAiSummaryData(null);
            try {
                const apiBaseUrl = getApiBaseUrl();
                const res = await fetch(`${apiBaseUrl}/api/v1/intelligence/summary/${encodeURIComponent(nodeId)}`);
                if (!res.ok) throw new Error('Failed to load AI summary');
                const data = await res.json();
                // Expected shape: { aiSummary: string, aiTags: string[] | null, aiImportance: number }
                setAiSummaryData({
                    aiSummary: data.aiSummary ?? '',
                    aiTags: Array.isArray(data.aiTags) ? data.aiTags : [],
                    aiImportance: typeof data.aiImportance === 'number' ? data.aiImportance : null
                });
            } catch (e) {
                setAiSummaryData(null);
            } finally {
                setAiSummaryLoading(false);
            }
        };

        if (selectedNode?.id) {
            fetchAiSummary(selectedNode.id);
        } else {
            setAiSummaryData(null);
            setAiSummaryLoading(false);
        }
    }, [selectedNode?.id]);

    // Clear previous analysis when selection changes
    useEffect(() => {
        setAnalysis('');
        setIsLoading(false);
        if (eventSource) {
            try { eventSource.close(); } catch { }
        }
    }, [selectedNodeId]);

    useEffect(() => {
        return () => {
            if (eventSource) {
                try { eventSource.close(); } catch { }
            }
        };
    }, [eventSource]);

    // Dynamically load remark plugins (GFM for lists/tables, breaks for single-line breaks)
    useEffect(() => {
        let isMounted = true;
        Promise.allSettled([
            import('remark-gfm').then(mod => mod.default || mod).catch(() => null),
            import('remark-breaks').then(mod => mod.default || mod).catch(() => null),
        ]).then((results) => {
            if (!isMounted) return;
            const plugins = results
                .map(r => (r.status === 'fulfilled' ? r.value : null))
                .filter(Boolean);
            setMarkdownPlugins(plugins);
        });
        return () => { isMounted = false; };
    }, []);

    // Clear chat messages when node changes
    useEffect(() => {
        setChatMessages([]);
        setChatInput('');
        setIsChatting(false);
    }, [selectedNodeId]);

    // Smart auto-scroll: only scroll if user is already at/near bottom
    useEffect(() => {
        const chatContainer = messagesContainerRef.current;
        if (chatContainer) {
            const { scrollHeight, scrollTop, clientHeight } = chatContainer;
            // Set a threshold (100px) to determine if user is at the bottom
            const isScrolledToBottom = scrollHeight - scrollTop - clientHeight < 100;

            if (isScrolledToBottom) {
                // Only auto-scroll if user is already at the bottom
                chatContainer.scrollTop = chatContainer.scrollHeight;
            }
        }
    }, [chatMessages, isChatting]);

    const handleAnalyzeClick = () => {
        if (!selectedNode?.id || isLoading) return;
        setIsLoading(true);
        setAnalysis('');
        const apiBaseUrl = getApiBaseUrl();
        const es = new EventSource(`${apiBaseUrl}/api/v1/analyze-node/${encodeURIComponent(selectedNode.id)}`);
        es.onmessage = (event) => {
            if (event.data === '[DONE]') {
                setIsLoading(false);
                es.close();
                return;
            }
            setAnalysis(prev => prev + event.data);
        };
        es.onerror = () => {
            setIsLoading(false);
            try { es.close(); } catch { }
        };
        setEventSource(es);
    };

    // Handle sending chat messages
    const handleSendMessage = (messageText) => {
        if (!selectedNode?.id || isChatting || !messageText.trim()) return;

        const userMessage = {
            role: 'user',
            content: messageText.trim(),
            timestamp: new Date()
        };

        setChatMessages(prev => [...prev, userMessage]);
        setChatInput('');
        setIsChatting(true);

        const apiBaseUrl = getApiBaseUrl();

        // Start building the assistant's response in state
        const assistantMessage = {
            role: 'assistant',
            content: '',
            timestamp: new Date()
        };
        setChatMessages(prev => [...prev, assistantMessage]);

        // Prepare conversation history (convert chatMessages to format expected by backend)
        const conversationHistory = chatMessages.map(msg => ({
            role: msg.role,
            content: msg.content
        }));

        // Use fetch with POST for multi-turn conversation support
        fetch(`${apiBaseUrl}/api/v1/agent/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                node_id: selectedNode.id,
                message: messageText.trim(),
                conversation_history: conversationHistory
            }),
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const reader = response.body.getReader();
                const decoder = new TextDecoder();

                const readStream = () => {
                    reader.read().then(({ done, value }) => {
                        if (done) {
                            setIsChatting(false);
                            return;
                        }

                        const chunk = decoder.decode(value, { stream: true });
                        const lines = chunk.split('\n');

                        for (const line of lines) {
                            // Skip empty lines
                            if (!line.trim()) continue;

                            if (line.startsWith('data: ')) {
                                const data = line.slice(6); // Remove 'data: ' prefix

                                if (data === '[DONE]') {
                                    setIsChatting(false);
                                    return;
                                }

                                // Append streamed data to the last assistant message
                                setChatMessages(prev => {
                                    const newMessages = [...prev];
                                    const lastIndex = newMessages.length - 1;
                                    if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                                        newMessages[lastIndex] = {
                                            ...newMessages[lastIndex],
                                            content: newMessages[lastIndex].content + data
                                        };
                                    }
                                    return newMessages;
                                });
                            }
                        }

                        readStream(); // Continue reading
                    }).catch(error => {
                        console.error('[AI Chat] Stream read error:', error);
                        setIsChatting(false);

                        setChatMessages(prev => {
                            const newMessages = [...prev];
                            const lastIndex = newMessages.length - 1;
                            if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                                const currentContent = newMessages[lastIndex].content;
                                if (!currentContent || currentContent.trim() === '') {
                                    newMessages[lastIndex] = {
                                        ...newMessages[lastIndex],
                                        content: '⚠️ Failed to stream response. Please try again.'
                                    };
                                }
                            }
                            return newMessages;
                        });
                    });
                };

                readStream();
            })
            .catch(error => {
                console.error('[AI Chat] Request error:', error);
                setIsChatting(false);

                setChatMessages(prev => {
                    const newMessages = [...prev];
                    const lastIndex = newMessages.length - 1;
                    if (lastIndex >= 0 && newMessages[lastIndex].role === 'assistant') {
                        newMessages[lastIndex] = {
                            ...newMessages[lastIndex],
                            content: '⚠️ Failed to connect to chat service. Please check your connection and try again.'
                        };
                    }
                    return newMessages;
                });
            });
    };

    const handleQuickQuestion = (question) => {
        handleSendMessage(question);
    };

    const formatCode = (code) => {
        if (!code) return '';

        // Basic syntax highlighting for Python
        return code
            .replace(/(def|class|if|else|elif|for|while|try|except|finally|with|import|from|return|yield|async|await)\b/g, '<span class="keyword">$1</span>')
            .replace(/(\b\w+)\s*\(/g, '<span class="function">$1</span>(')
            .replace(/(["'].*?["'])/g, '<span class="string">$1</span>')
            .replace(/(#.*$)/gm, '<span class="comment">$1</span>')
            .replace(/\n/g, '<br>');
    };

    // Render chat UI
    const renderChat = () => {
        if (!selectedNode?.id) {
            return (
                <div className="no-selection">
                    <h3>No Node Selected</h3>
                    <p>Please select a node in the graph to start chatting.</p>
                </div>
            );
        }

        const quickQuestions = [
            "请用更简单的方式解释这段代码",
            "这段代码有什么潜在风险？",
            "这段代码的核心功能是什么？",
            "这段代码有哪些依赖关系？"
        ];

        return (
            <div className="chat-container">
                {/* Chat Messages Area */}
                <div className="chat-messages" ref={messagesContainerRef}>
                    {chatMessages.length === 0 ? (
                        <div style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            flex: 1,
                            minHeight: 0,
                            opacity: 0.6
                        }}>
                            <div style={{ fontSize: 48, marginBottom: 16 }}>💬</div>
                            <h3 style={{ marginBottom: 8 }}>Start a Conversation</h3>
                            <p style={{ textAlign: 'center', maxWidth: 400 }}>
                                Ask me anything about this code node: <strong>{selectedNode.id}</strong>
                            </p>

                            {/* Quick Questions */}
                            <div style={{
                                marginTop: 24,
                                display: 'flex',
                                flexDirection: 'column',
                                gap: 8,
                                width: '100%',
                                maxWidth: 400
                            }}>
                                <p style={{ fontSize: 12, opacity: 0.8, marginBottom: 4 }}>Quick questions:</p>
                                {quickQuestions.map((question, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleQuickQuestion(question)}
                                        style={{
                                            padding: '8px 12px',
                                            background: '#2a2a2a',
                                            border: '1px solid #444',
                                            borderRadius: '6px',
                                            color: '#fff',
                                            cursor: 'pointer',
                                            textAlign: 'left',
                                            fontSize: 13,
                                            transition: 'all 0.2s'
                                        }}
                                        onMouseEnter={(e) => {
                                            e.target.style.background = '#333';
                                            e.target.style.borderColor = '#6c5ce7';
                                        }}
                                        onMouseLeave={(e) => {
                                            e.target.style.background = '#2a2a2a';
                                            e.target.style.borderColor = '#444';
                                        }}
                                    >
                                        {question}
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        chatMessages.map((msg, idx) => (
                            <div
                                key={idx}
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: msg.role === 'user' ? 'flex-end' : 'flex-start'
                                }}
                            >
                                <div style={{
                                    maxWidth: '80%',
                                    padding: '10px 14px',
                                    borderRadius: '12px',
                                    background: msg.role === 'user' ? '#6c5ce7' : '#2a2a2a',
                                    border: msg.role === 'user' ? 'none' : '1px solid #444',
                                    color: '#fff',
                                    wordWrap: 'break-word'
                                }}>
                                    {msg.role === 'assistant' && msg.content ? (
                                        <ReactMarkdown remarkPlugins={markdownPlugins}>{normalizeMarkdown(msg.content)}</ReactMarkdown>
                                    ) : (
                                        <p style={{ margin: 0, whiteSpace: 'pre-wrap' }}>{msg.content}</p>
                                    )}
                                </div>
                                {msg.role === 'assistant' && idx === chatMessages.length - 1 && isChatting && (
                                    <div style={{
                                        marginTop: 4,
                                        marginLeft: 4,
                                        display: 'flex',
                                        gap: 4,
                                        alignItems: 'center',
                                        opacity: 0.6
                                    }}>
                                        <div className="loading-spinner-small"></div>
                                        <span style={{ fontSize: 11 }}>AI is thinking...</span>
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                    {/* Scroll anchor */}
                    <div ref={chatMessagesEndRef} />
                </div>

                {/* Chat Input Area */}
                <div className="chat-input">
                    <input
                        type="text"
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyPress={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSendMessage(chatInput);
                            }
                        }}
                        placeholder="Type your message... (Press Enter to send)"
                        disabled={isChatting}
                        style={{
                            flex: 1,
                            padding: '10px 14px',
                            background: '#2a2a2a',
                            border: '1px solid #444',
                            borderRadius: '8px',
                            color: '#fff',
                            fontSize: 14,
                            outline: 'none'
                        }}
                    />
                    <button
                        onClick={() => handleSendMessage(chatInput)}
                        disabled={isChatting || !chatInput.trim()}
                        style={{
                            padding: '10px 20px',
                            background: isChatting || !chatInput.trim() ? '#444' : '#6c5ce7',
                            color: '#fff',
                            border: 'none',
                            borderRadius: '8px',
                            cursor: isChatting || !chatInput.trim() ? 'not-allowed' : 'pointer',
                            fontSize: 14,
                            fontWeight: 500
                        }}
                    >
                        {isChatting ? 'Sending...' : 'Send'}
                    </button>
                </div>
            </div>
        );
    };

    const renderEvidence = () => {
        if (!selectedNode || !selectedNodeEvidence) {
            return (
                <div className="no-selection">
                    <h3>No Node Selected</h3>
                    <p>Click on a node in the graph to view its evidence details.</p>
                </div>
            );
        }

        const { file, span, snippet } = selectedNodeEvidence;

        return (
            <div className="evidence-content">
                <div className="node-header">
                    <h3>Node Details</h3>
                    <div className="node-id">{selectedNode.id}</div>
                </div>

                {/* AI Intelligence Summary */}
                {selectedNode?.id && (
                    <div className="ai-summary-section" style={{ border: '1px solid #2f2f2f', borderRadius: 8, padding: 12, marginBottom: 16, background: '#191919' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                                <span style={{ fontWeight: 600 }}>AI Summary</span>
                                {/* AI Tags */}
                                {aiSummaryLoading ? (
                                    <span style={{ opacity: 0.7, fontSize: 12 }}>Loading…</span>
                                ) : (
                                    (aiSummaryData?.aiTags || []).map((tag, idx) => (
                                        <span key={`${tag}-${idx}`} style={{
                                            display: 'inline-block',
                                            padding: '2px 6px',
                                            borderRadius: 6,
                                            border: '1px solid #444',
                                            background: '#222',
                                            fontSize: 12,
                                            color: '#ddd'
                                        }}>
                                            [{tag}]
                                        </span>
                                    ))
                                )}
                            </div>
                            {/* Importance badge / bar */}
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 140 }}>
                                <span style={{ fontSize: 12, opacity: 0.8 }}>Importance</span>
                                <div style={{ position: 'relative', width: 90, height: 8, background: '#2a2a2a', borderRadius: 6, overflow: 'hidden' }}>
                                    <div style={{ width: `${Math.max(0, Math.min(10, aiSummaryData?.aiImportance ?? 0)) * 10}%`, height: '100%', background: '#6c5ce7' }} />
                                </div>
                                <span style={{ fontSize: 12, fontWeight: 600 }}>{aiSummaryData?.aiImportance ?? '-'}/10</span>
                            </div>
                        </div>

                        {/* Collapsible body */}
                        <div style={{ marginTop: 10 }}>
                            <button
                                onClick={() => setAiSummaryOpen(v => !v)}
                                style={{
                                    background: 'transparent',
                                    border: 'none',
                                    color: '#9aa0a6',
                                    cursor: 'pointer',
                                    padding: 0,
                                    marginBottom: 6
                                }}
                            >
                                {aiSummaryOpen ? 'Hide details ▲' : 'Show details ▼'}
                            </button>
                            {aiSummaryOpen && (
                                <div style={{ borderTop: '1px solid #2a2a2a', paddingTop: 8 }}>
                                    {aiSummaryLoading && (
                                        <div className="rag-loading">
                                            <div className="loading-spinner-small"></div>
                                            <span>Loading summary…</span>
                                        </div>
                                    )}
                                    {!aiSummaryLoading && aiSummaryData?.aiSummary && (
                                        <ReactMarkdown remarkPlugins={markdownPlugins}>{normalizeMarkdown(aiSummaryData.aiSummary)}</ReactMarkdown>
                                    )}
                                    {!aiSummaryLoading && !aiSummaryData?.aiSummary && (
                                        <p style={{ opacity: 0.8, fontSize: 13 }}>No AI summary available for this node.</p>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                )}

                <div className="node-info">
                    <div className="info-section">
                        <h4>Function Name</h4>
                        <p className="fqname">{selectedNode.fqName || 'N/A'}</p>
                    </div>

                    <div className="info-section">
                        <h4>Kind</h4>
                        <p className="kind">{selectedNode.kind || 'N/A'}</p>
                    </div>

                    <div className="info-section">
                        <h4>Language</h4>
                        <p className="language">{selectedNode.language || 'N/A'}</p>
                    </div>

                    {selectedNode.signature && (
                        <div className="info-section">
                            <h4>Signature</h4>
                            <p className="signature">{selectedNode.signature}</p>
                        </div>
                    )}

                    {selectedNode.doc && (
                        <div className="info-section">
                            <h4>Documentation</h4>
                            <p className="doc">{selectedNode.doc}</p>
                        </div>
                    )}

                    {selectedNode.metrics && (
                        <div className="info-section">
                            <h4>Metrics</h4>
                            <div className="metrics">
                                {selectedNode.metrics.loc && (
                                    <span className="metric">LOC: {selectedNode.metrics.loc}</span>
                                )}
                                {selectedNode.metrics.complexity && (
                                    <span className="metric">Complexity: {selectedNode.metrics.complexity}</span>
                                )}
                            </div>
                        </div>
                    )}

                    {selectedNode.data?.risk_index !== undefined && (
                        <RiskIndicator riskIndex={selectedNode.data.risk_index} />
                    )}

                    {/* Performance Metrics */}
                    {(selectedNode.data?.p95_latency || selectedNode.data?.error_rate || selectedNode.data?.throughput) && (
                        <div className="info-section">
                            <h4>Performance Metrics</h4>
                            <div className="performance-metrics">
                                {selectedNode.data.p95_latency && (
                                    <div className="metric-item">
                                        <span className="metric-label">P95 Latency:</span>
                                        <span className={`metric-value ${parseInt(selectedNode.data.p95_latency.replace('ms', '')) > 300 ? 'bottleneck' : ''}`}>
                                            {selectedNode.data.p95_latency}
                                        </span>
                                    </div>
                                )}
                                {selectedNode.data.error_rate && (
                                    <div className="metric-item">
                                        <span className="metric-label">Error Rate:</span>
                                        <span className={`metric-value ${parseFloat(selectedNode.data.error_rate.replace('%', '')) > 3.0 ? 'bottleneck' : ''}`}>
                                            {selectedNode.data.error_rate}
                                        </span>
                                    </div>
                                )}
                                {selectedNode.data.throughput && (
                                    <div className="metric-item">
                                        <span className="metric-label">Throughput:</span>
                                        <span className="metric-value">{selectedNode.data.throughput}</span>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <div className="evidence-section">
                    <h3>Evidence</h3>

                    <div className="evidence-item">
                        <h4>File</h4>
                        <p className="file-path">{file || 'N/A'}</p>
                    </div>

                    {span && (
                        <div className="evidence-item">
                            <h4>Location</h4>
                            <p className="span-info">
                                Lines {span.start} - {span.end}
                                {span.start && span.end && (
                                    <span className="line-count">
                                        ({span.end - span.start + 1} lines)
                                    </span>
                                )}
                            </p>
                        </div>
                    )}

                    {snippet && (
                        <div className="evidence-item">
                            <h4>Code Snippet</h4>
                            <div className="code-container">
                                <pre className="code-block">
                                    <code
                                        dangerouslySetInnerHTML={{
                                            __html: formatCode(snippet)
                                        }}
                                    />
                                </pre>
                            </div>
                        </div>
                    )}
                </div>

                {/* RAG Evidence Section */}
                <div className="evidence-section">
                    <h3>Context & Evidence</h3>
                    <div className="rag-evidence-container">
                        {ragLoading ? (
                            <div className="rag-loading">
                                <div className="loading-spinner-small"></div>
                                <span>Loading evidence...</span>
                            </div>
                        ) : ragEvidence ? (
                            <div className="rag-evidence-content">
                                <div className="evidence-text">
                                    {ragEvidence}
                                </div>
                                <div className="evidence-source">
                                    <small>Source: RAG Knowledge Base</small>
                                </div>
                            </div>
                        ) : (
                            <div className="rag-evidence-empty">
                                <p>No contextual evidence available for this node.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div
            className="evidence-pane"
            style={{
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
            }}
        >
            <div className="tab-header" style={{ flex: 'none' }}>
                <button
                    className={`tab-button ${activeTab === 'evidence' ? 'active' : ''}`}
                    onClick={() => setActiveTab('evidence')}
                >
                    Evidence Details
                </button>
                <button
                    className={`tab-button ${activeTab === 'explanation' ? 'active' : ''}`}
                    onClick={() => setActiveTab('explanation')}
                >
                    AI Analysis
                    {analysis && <span className="tab-indicator">●</span>}
                </button>
                <button
                    className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
                    onClick={() => setActiveTab('chat')}
                >
                    AI Chat
                    {chatMessages.length > 0 && <span className="tab-indicator">●</span>}
                </button>
                <button
                    className={`tab-button ${activeTab === 'workflow' ? 'active' : ''}`}
                    onClick={() => setActiveTab('workflow')}
                >
                    Workflow
                </button>
            </div>

            <div
                className="tab-content"
                data-tab={activeTab}
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    flex: 1,
                    minHeight: 0,
                }}
            >
                {activeTab === 'evidence' && (
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        {renderEvidence()}
                    </div>
                )}
                {activeTab === 'explanation' && (
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        <div className="explanation-panel">
                            <div className="explanation-actions" style={{ marginBottom: '12px' }}>
                                <button
                                    onClick={handleAnalyzeClick}
                                    disabled={!selectedNode || isLoading}
                                    style={{
                                        padding: '8px 12px',
                                        background: '#6c5ce7',
                                        color: '#fff',
                                        border: 'none',
                                        borderRadius: '6px',
                                        cursor: isLoading ? 'not-allowed' : 'pointer'
                                    }}
                                >
                                    {isLoading ? 'Analyzing…' : '🤖 Ask AI to Analyze this Function'}
                                </button>
                            </div>
                            <div className="explanation-content" style={{
                                background: '#1f1f1f',
                                border: '1px solid #333',
                                borderRadius: '8px',
                                padding: '12px',
                                minHeight: '120px'
                            }}>
                                {!analysis && !isLoading && (
                                    <div className="no-explanation">
                                        <h3>No Analysis Yet</h3>
                                        <p>Click the button above to generate an AI analysis for the selected function.</p>
                                    </div>
                                )}
                                {isLoading && (
                                    <div className="rag-loading">
                                        <div className="loading-spinner-small"></div>
                                        <span>Generating analysis…</span>
                                    </div>
                                )}
                                {analysis && (
                                    <ReactMarkdown remarkPlugins={markdownPlugins}>{normalizeMarkdown(analysis)}</ReactMarkdown>
                                )}
                            </div>
                        </div>
                    </div>
                )}
                {activeTab === 'chat' && (
                    <div style={{
                        flex: 1,
                        display: 'flex',
                        flexDirection: 'column',
                        minHeight: 0,
                        overflow: 'hidden',
                    }}>
                        {renderChat()}
                    </div>
                )}
                {activeTab === 'workflow' && (
                    <div style={{ flex: 1, overflowY: 'auto' }}>
                        <WorkflowPanel />
                    </div>
                )}
            </div>
        </div>
    );
};

export default EvidencePane;
