import React, { useState, useEffect } from 'react';
import { Button, Card, Input, Spin, App } from 'antd';

interface EdgeData {
    src: string;
    dst: string;
    type: string;
}

interface ApiResponse {
    agent: string;
    intent: string;
    query: string;
    summary_md: string;
    files: any[];
    edges_json: EdgeData[];
}

const EdgesJsonTest: React.FC = () => {
    const { message } = App.useApp();

    const [query, setQuery] = useState('user authentication');
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState<ApiResponse | null>(null);
    const [error, setError] = useState<string | null>(null);

    const testApi = async () => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch('/api/agent/code_lookup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: query }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data: ApiResponse = await response.json();
            setResponse(data);
            message.success('API 调用成功！');
        } catch (err) {
            const errorMsg = err instanceof Error ? err.message : 'Unknown error';
            setError(errorMsg);
            message.error(`API 调用失败: ${errorMsg}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <h2>Edges JSON API 测试</h2>

            <Card style={{ marginBottom: '20px' }}>
                <div style={{ marginBottom: '10px' }}>
                    <Input
                        placeholder="输入查询内容"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        style={{ marginRight: '10px', width: '300px' }}
                    />
                    <Button type="primary" onClick={testApi} loading={loading}>
                        测试 API
                    </Button>
                </div>

                {loading && <Spin />}

                {error && (
                    <div style={{ color: 'red', margin: '10px 0' }}>
                        ❌ 错误: {error}
                    </div>
                )}
            </Card>

            {response && (
                <Card title="API 响应">
                    <h3>基本信息</h3>
                    <p><strong>Agent:</strong> {response.agent}</p>
                    <p><strong>Intent:</strong> {response.intent}</p>
                    <p><strong>Query:</strong> {response.query}</p>

                    <h3>Edges JSON ({response.edges_json.length} 条边)</h3>
                    <div style={{ backgroundColor: '#f5f5f5', padding: '10px', borderRadius: '4px' }}>
                        <pre style={{ margin: 0, fontSize: '12px' }}>
                            {JSON.stringify(response.edges_json, null, 2)}
                        </pre>
                    </div>

                    <h3>调用关系图预览</h3>
                    <div style={{ margin: '10px 0' }}>
                        {response.edges_json.map((edge, index) => (
                            <div key={index} style={{ margin: '5px 0', padding: '5px', backgroundColor: '#e6f7ff', borderRadius: '4px' }}>
                                <strong>{edge.src}</strong> --[{edge.type}]--&gt; <strong>{edge.dst}</strong>
                            </div>
                        ))}
                    </div>

                    <h3>Summary</h3>
                    <div style={{ backgroundColor: '#f9f9f9', padding: '10px', borderRadius: '4px' }}>
                        <div dangerouslySetInnerHTML={{ __html: response.summary_md.replace(/\n/g, '<br>') }} />
                    </div>
                </Card>
            )}
        </div>
    );
};

export default EdgesJsonTest;
