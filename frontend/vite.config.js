import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5050,
    proxy: {
      // 数据 API 代理
      '/api': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      // 图片资源代理
      '/images': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      },
      // SSE 实时数据流代理
      '/stream': {
        target: 'http://127.0.0.1:5001',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
