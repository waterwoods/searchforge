// frontend/src/components/panels/ImprovePanel.tsx
import { Form, Slider, Switch, Typography } from 'antd';
import { useAppStore } from '../../store/useAppStore';

const { Title, Text } = Typography;

export const ImprovePanel = () => {
    // Connect to the global Zustand store
    const { topK, rerank, setTopK, setRerank } = useAppStore();

    return (
        <div>
            <Title level={5}>Tuning Parameters</Title>
            <Text type="secondary">
                Adjust these controls and re-run your query to see the impact.
            </Text>
            <Form layout="vertical" style={{ marginTop: '20px' }}>
                <Form.Item label={`Top K: ${topK}`}>
                    <Slider
                        min={1}
                        max={50}
                        value={topK}
                        onChange={setTopK} // Update global state on change
                    />
                </Form.Item>
                <Form.Item label="Enable Reranker">
                    <Switch
                        checked={rerank}
                        onChange={setRerank} // Update global state on change
                    />
                </Form.Item>
            </Form>
        </div>
    );
};

