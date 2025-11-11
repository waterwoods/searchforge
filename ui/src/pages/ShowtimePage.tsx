import { Space } from 'antd';
import { QueryConsole } from '../components/console/QueryConsole';
import { RunStewardCard } from '../components/RunStewardCard';

export const ShowtimePage = () => {
    return (
        <Space
            direction="vertical"
            size="large"
            style={{ padding: 24, width: '100%', boxSizing: 'border-box' }}
        >
            <RunStewardCard />
            <QueryConsole />
        </Space>
    );
};

