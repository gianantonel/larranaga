import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Config configurable via env vars:
//   VITE_DEV_PORT      → puerto del frontend (default 5173)
//   VITE_API_TARGET    → URL del backend al que hacer proxy (default http://localhost:8000)
export default defineConfig({
  plugins: [react()],
  server: {
    port: Number(process.env.VITE_DEV_PORT) || 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
