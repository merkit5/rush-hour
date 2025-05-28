import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    host: true, // Доступ извне контейнера
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://backend:3000', // Имя сервиса из docker-compose
        changeOrigin: true
      }
    }
  }
})