import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';

const MermaidTest: React.FC = () => {
    const mermaidRef = useRef<HTMLDivElement>(null);
    const [isRendered, setIsRendered] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const renderMermaid = async () => {
            try {
                // 初始化 Mermaid
                mermaid.initialize({
                    startOnLoad: false,
                    theme: 'default',
                    securityLevel: 'loose',
                });

                // 渲染图表
                const mermaidCode = `
          graph TD
            A[开始] --> B[处理]
            B --> C[结束]
        `;

                if (mermaidRef.current) {
                    mermaidRef.current.innerHTML = '';

                    // 使用 render 方法
                    const { svg } = await mermaid.render('mermaid-test-' + Date.now(), mermaidCode);
                    mermaidRef.current.innerHTML = svg;
                    setIsRendered(true);
                }
            } catch (err) {
                console.error('Mermaid render error:', err);
                setError(err instanceof Error ? err.message : 'Unknown error');
            }
        };

        renderMermaid();
    }, []);

    return (
        <div style={{ padding: '20px' }}>
            <h2>Mermaid 测试</h2>
            <p>如果您能看到下面的流程图，说明 Mermaid.js 环境配置成功！</p>

            <div
                ref={mermaidRef}
                style={{
                    border: '1px solid #ccc',
                    padding: '20px',
                    margin: '20px 0',
                    minHeight: '200px',
                    backgroundColor: '#f5f5f5'
                }}
            />

            {error && (
                <div style={{ color: 'red', margin: '10px 0' }}>
                    ❌ 错误: {error}
                </div>
            )}

            {isRendered && !error && (
                <p style={{ color: 'green' }}>✅ 环境验证成功！可以开始集成真实的调用关系图了。</p>
            )}

            {!isRendered && !error && (
                <p style={{ color: 'orange' }}>⏳ 正在渲染图表...</p>
            )}
        </div>
    );
};

export default MermaidTest;
