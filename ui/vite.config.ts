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
            // 捕获用于验证的 /ready 路径
            // 例如: /ready -> http://localhost:8000/ready
            '/ready': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                secure: false,
            },
            '/reports': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
});
