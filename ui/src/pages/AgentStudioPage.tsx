// frontend/src/pages/AgentStudioPage.tsx
import { useState } from 'react';
import { Button, Card, Input, List, Spin, Tag, Typography, App, Modal } from 'antd';
import { RobotOutlined, UserOutlined, CopyOutlined, LikeOutlined, DislikeOutlined, EyeOutlined } from '@ant-design/icons';
import { AgentCodeFile, AgentCodeNeighbor, ApiAgentCodeResponse, ApiAgentResponse, ApiAgentTuneResponse } from '../types/api.types';

// We need react-markdown to render text and code blocks.
// Please run: `pnpm add react-markdown`
import ReactMarkdown from 'react-markdown';

// Syntax highlighting and copy functionality
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { CopyToClipboard } from 'react-copy-to-clipboard';

const { Title } = Typography;

interface ChatMessage {
    sender: 'user' | 'agent';
    content: ApiAgentResponse | string; // string for user, object for agent
}

export const AgentStudioPage = () => {
    const { message } = App.useApp();

    // Simplified state management
    const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
    const [requestId, setRequestId] = useState<string | undefined>();
    const [answer, setAnswer] = useState<any | null>(null); // To store files, snippets, summary
    const [error, setError] = useState<string | undefined>();
    const [isModalVisible, setIsModalVisible] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [currentQuery, setCurrentQuery] = useState<string | undefined>();

    const handleSend = async (messageText: string) => {
        if (!messageText || status === 'loading') return;

        // Reset state
        setStatus('loading');
        setAnswer(null);
        setRequestId(undefined);
        setError(undefined);
        setCurrentQuery(messageText); // Store the current query

        const userMessage: ChatMessage = { sender: 'user', content: messageText };
        setMessages((prev) => [...prev, userMessage]);

        try {
            const res = await fetch('/api/agent/code_lookup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText }),
            });

            if (!res.ok) {
                throw new Error(`API request failed with status ${res.status}`);
            }

            const data: ApiAgentResponse = await res.json();

            // Extract textual results and request ID
            if (data.intent === 'code_lookup') {
                const codeData = data as ApiAgentCodeResponse;
                setAnswer({
                    summary: codeData.summary_md,
                    files: codeData.files || []
                });

                // Extract request ID from response
                const responseRid = (data as any).rid;
                if (responseRid) {
                    setRequestId(responseRid);
                }

                setStatus('ready');
            } else {
                throw new Error('Unexpected response type');
            }

        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Unknown error';
            setError(errorMessage);
            setStatus('error');

            // Add error message to chat
            const errorChatMessage: ChatMessage = {
                sender: 'agent',
                content: {
                    agent: 'error_handler',
                    intent: 'error' as any,
                    message_md: `Sorry, I encountered an error: ${errorMessage}`,
                    params_patch: null,
                    apply_hint: '',
                } as unknown as ApiAgentTuneResponse,
            };
            setMessages((prev) => [...prev, errorChatMessage]);
        }
    };

    const renderMessageContent = (msg: ChatMessage) => {
        if (msg.sender === 'user') {
            return <Typography.Text>{msg.content as string}</Typography.Text>;
        }

        // Agent's response
        const data = msg.content as ApiAgentResponse;

        if (data.intent === 'optimize_latency') {
            const tuneData = data as ApiAgentTuneResponse;
            return (
                <div style={{ overflowWrap: 'break-word' }}>
                    <ReactMarkdown>{tuneData.message_md}</ReactMarkdown>
                    <Button
                        type="primary"
                        style={{ marginTop: '10px' }}
                        onClick={() => {
                            // Handle apply params if needed
                            message.success('Parameters applied!');
                        }}
                    >
                        Apply Strategy
                    </Button>
                </div>
            );
        }

        if (data.intent === 'code_lookup') {
            const codeData = data as ApiAgentCodeResponse;
            const summary = codeData.summary_md || "Agent found some code information.";
            const files = Array.isArray(codeData.files) ? codeData.files : [];

            return (
                <div style={{ overflowWrap: 'break-word' }}>
                    <ReactMarkdown>{summary}</ReactMarkdown>

                    {/* View Code Flow Graph Button */}
                    {(data as any).rid && (
                        <div style={{ marginTop: '16px', marginBottom: '16px' }}>
                            <Button
                                type="primary"
                                icon={<EyeOutlined />}
                                onClick={() => setIsModalVisible(true)}
                                style={{ marginRight: '8px' }}
                                data-testid="open-graph-btn"
                            >
                                View Code Flow Graph
                            </Button>
                        </div>
                    )}

                    <div data-testid="hits-list">
                        {files.map((file, index) => (
                            <Card
                                key={file.path ? `${file.path}-${index}` : `file-${index}`}
                                type="inner"
                                title={file.path || "Unknown File"}
                                style={{ marginTop: '10px' }}
                                data-file-path={file.path}
                                extra={
                                    <CopyToClipboard text={file.snippet || ""} onCopy={() => message.success('Code copied!')}>
                                        <Button icon={<CopyOutlined />} size="small">Copy</Button>
                                    </CopyToClipboard>
                                }
                            >
                                <SyntaxHighlighter
                                    language={file.language || 'plaintext'}
                                    style={atomDark}
                                    showLineNumbers
                                    wrapLines={true}
                                    customStyle={{ maxHeight: '300px', overflowY: 'auto', margin: 0 }}
                                >
                                    {file.snippet || "No snippet available."}
                                </SyntaxHighlighter>
                                <Typography.Text type="secondary" italic style={{ display: 'block', marginTop: '8px', fontSize: '12px' }}>
                                    💡 {file.why_relevant || "Relevance info not provided."}
                                </Typography.Text>
                                <div style={{ marginTop: '10px', textAlign: 'right' }}>
                                    <Button
                                        icon={<LikeOutlined />}
                                        size="small"
                                        onClick={() => message.success(`Liked: ${file.path}`)}
                                        style={{ marginRight: '8px' }}
                                    >
                                        Good
                                    </Button>
                                    <Button
                                        icon={<DislikeOutlined />}
                                        size="small"
                                        onClick={() => message.error(`Disliked: ${file.path}`)}
                                        danger
                                    >
                                        Bad
                                    </Button>
                                </div>
                                {/* --- One-Hop Neighbor Display --- */}
                                {file.neighbors && file.neighbors.length > 0 && (
                                    <div style={{ marginTop: '15px', borderTop: '1px solid #444', paddingTop: '10px' }}>
                                        <Typography.Text strong style={{ fontSize: '12px', color: '#aaa' }}>
                                            Related Code:
                                        </Typography.Text>
                                        <List
                                            size="small"
                                            dataSource={file.neighbors}
                                            renderItem={(neighbor: AgentCodeNeighbor) => (
                                                <List.Item style={{ padding: '4px 0' }}>
                                                    <Tag color="cyan" style={{ marginRight: '5px', fontSize: '10px' }}>
                                                        {neighbor.relation}
                                                    </Tag>
                                                    <Typography.Text code style={{ fontSize: '12px' }}>
                                                        {neighbor.name ? `${neighbor.path}::${neighbor.name}` : neighbor.path}
                                                    </Typography.Text>
                                                </List.Item>
                                            )}
                                            split={false}
                                        />
                                    </div>
                                )}
                                {/* --- End Neighbor Display --- */}
                            </Card>
                        ))}
                        {files.length === 0 && <Typography.Text type="secondary">No specific code snippets found.</Typography.Text>}
                    </div>
                </div>
            );
        }

        // Handle static frontend info messages
        if ((data as any).intent === 'info' || (data as any).intent === 'error') {
            const infoData = data as ApiAgentTuneResponse;
            return (
                <div style={{ overflowWrap: 'break-word' }}>
                    <ReactMarkdown>{infoData.message_md}</ReactMarkdown>
                </div>
            );
        }

        return <Spin />;
    };

    return (
        <div>
            <Title level={2}>Agent Studio</Title>

            {/* Conditional rendering based on status */}
            {status === 'loading' && (
                <div style={{ textAlign: 'center', padding: '40px' }}>
                    <Spin size="large" />
                    <div style={{ marginTop: '16px' }}>Searching for code...</div>
                </div>
            )}

            {status === 'error' && (
                <div style={{ textAlign: 'center', padding: '40px', color: '#ff4d4f' }}>
                    <div>Error: {error}</div>
                </div>
            )}

            {status === 'ready' && answer && (
                <div>
                    <ReactMarkdown>{answer.summary}</ReactMarkdown>

                    {/* View Code Flow Graph Button - only show if requestId exists */}
                    {requestId && (
                        <div style={{ marginTop: '16px', marginBottom: '16px' }}>
                            <Button
                                type="primary"
                                icon={<EyeOutlined />}
                                onClick={() => setIsModalVisible(true)}
                                style={{ marginRight: '8px' }}
                                data-testid="open-graph-btn"
                            >
                                View Code Flow Graph
                            </Button>
                        </div>
                    )}

                    <div data-testid="hits-list">
                        {answer.files.map((file: AgentCodeFile, index: number) => (
                            <Card
                                key={file.path ? `${file.path}-${index}` : `file-${index}`}
                                type="inner"
                                title={file.path || "Unknown File"}
                                style={{ marginTop: '10px' }}
                                data-file-path={file.path}
                                extra={
                                    <CopyToClipboard text={file.snippet || ""} onCopy={() => message.success('Code copied!')}>
                                        <Button icon={<CopyOutlined />} size="small">Copy</Button>
                                    </CopyToClipboard>
                                }
                            >
                                <SyntaxHighlighter
                                    language={file.language || 'plaintext'}
                                    style={atomDark}
                                    showLineNumbers
                                    wrapLines={true}
                                    customStyle={{ maxHeight: '300px', overflowY: 'auto', margin: 0 }}
                                >
                                    {file.snippet || "No snippet available."}
                                </SyntaxHighlighter>
                                <Typography.Text type="secondary" italic style={{ display: 'block', marginTop: '8px', fontSize: '12px' }}>
                                    💡 {file.why_relevant || "Relevance info not provided."}
                                </Typography.Text>
                                <div style={{ marginTop: '10px', textAlign: 'right' }}>
                                    <Button
                                        icon={<LikeOutlined />}
                                        size="small"
                                        onClick={() => message.success(`Liked: ${file.path}`)}
                                        style={{ marginRight: '8px' }}
                                    >
                                        Good
                                    </Button>
                                    <Button
                                        icon={<DislikeOutlined />}
                                        size="small"
                                        onClick={() => message.error(`Disliked: ${file.path}`)}
                                        danger
                                    >
                                        Bad
                                    </Button>
                                </div>
                                {/* --- One-Hop Neighbor Display --- */}
                                {file.neighbors && file.neighbors.length > 0 && (
                                    <div style={{ marginTop: '15px', borderTop: '1px solid #444', paddingTop: '10px' }}>
                                        <Typography.Text strong style={{ fontSize: '12px', color: '#aaa' }}>
                                            Related Code:
                                        </Typography.Text>
                                        <List
                                            size="small"
                                            dataSource={file.neighbors}
                                            renderItem={(neighbor: AgentCodeNeighbor) => (
                                                <List.Item style={{ padding: '4px 0' }}>
                                                    <Tag color="cyan" style={{ marginRight: '5px', fontSize: '10px' }}>
                                                        {neighbor.relation}
                                                    </Tag>
                                                    <Typography.Text code style={{ fontSize: '12px' }}>
                                                        {neighbor.name ? `${neighbor.path}::${neighbor.name}` : neighbor.path}
                                                    </Typography.Text>
                                                </List.Item>
                                            )}
                                            split={false}
                                        />
                                    </div>
                                )}
                                {/* --- End Neighbor Display --- */}
                            </Card>
                        ))}
                        {answer.files.length === 0 && <Typography.Text type="secondary">No specific code snippets found.</Typography.Text>}
                    </div>
                </div>
            )}

            <List
                style={{ height: '60vh', overflowY: 'auto', marginBottom: '20px', padding: '16px' }}
                dataSource={messages}
                renderItem={(item) => (
                    <List.Item>
                        <List.Item.Meta
                            avatar={item.sender === 'agent' ? <RobotOutlined /> : <UserOutlined />}
                            title={item.sender === 'agent' ? 'SearchForge Agent' : 'You'}
                            description={renderMessageContent(item)}
                        />
                    </List.Item>
                )}
            />
            <div data-testid="ask-input">
                <Input.Search
                    placeholder="Ask the agent: 'Help me optimize latency' or 'Show me the embedding code'"
                    enterButton={<span data-testid="send-btn">Send</span>}
                    size="large"
                    onSearch={handleSend}
                    loading={status === 'loading'}
                    disabled={status === 'loading'}
                />
            </div>

            {/* Graph Viewer Modal */}
            <Modal
                open={isModalVisible}
                onCancel={() => setIsModalVisible(false)}
                destroyOnClose={true}
                footer={null}
                width="90vw"
            >
                {currentQuery && (
                    <iframe
                        src={`/graph-viewer?query=${encodeURIComponent(currentQuery)}&theme=dark`}
                        style={{ width: '100%', height: '75vh', border: 'none' }}
                        title="Code Flow Graph Viewer"
                    />
                )}
            </Modal>
        </div>
    );
};
