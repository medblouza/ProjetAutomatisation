import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/login': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/info': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/generate-cdc': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/clean': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/dropbox': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    }
  }
})
