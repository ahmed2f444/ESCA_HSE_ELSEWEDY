import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        // Recharts is by far the heaviest dependency and the demo fixtures are
        // sizeable text — keeping both out of the main chunk means a page that
        // renders no chart doesn't pay for the charting library.
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
  server: {
    port: 5180,
    // When VITE_USE_MOCK=false the app talks to the Spring Boot service.
    // Proxying keeps the browser on one origin so we don't fight CORS during integration week.
    proxy: {
      '/api': { target: 'http://localhost:8080', changeOrigin: true },
      '/agent': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/agent/, ''),
      },
    },
  },
})
