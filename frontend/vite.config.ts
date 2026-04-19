import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000', // Connects UI to your Python Backend
      '/library': 'http://localhost:8000' // Connects UI to your 500GB drive
    }
  }
})