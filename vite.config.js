import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import basicSsl from '@vitejs/plugin-basic-ssl';

export default defineConfig({
  plugins: [react(), basicSsl()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('transitShapes.json')) {
            return 'transit-shapes';
          }
          if (id.includes('leaflet')) {
            return 'leaflet-vendor';
          }
        }
      }
    }
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5055',
        changeOrigin: true
      }
    }
  }
});
