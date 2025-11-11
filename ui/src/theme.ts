// frontend/src/theme.ts
import { theme } from 'antd';

export const useAntdTheme = () => {
    // Use dark algorithm by default
    return {
        algorithm: theme.darkAlgorithm,
        token: {
            colorBgBase: '#141414',
            colorTextBase: '#ffffff',
        },
    };
};

