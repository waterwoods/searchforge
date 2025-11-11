import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],

    server: {
        port: 5173,
        host: true,
        open: true,
        proxy: {
            // 捕获所有 /api 开头的请求
            // 例如: /api/orchestrate/run -> http://localhost:8000/api/orchestrate/run
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false, // 如果后端是 http，需要这个
            },
            // 编排服务代理
            '/orchestrate': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false,
                rewrite: (path) => path.replace(/^\/orchestrate\b/, '/api/experiment'),
            },
        },
    },
});
