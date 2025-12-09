import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');

  return {
    css: {
      postcss: './postcss.config.cjs'
    },
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: 3000,
      open: true,
      host: true, // Listen on all addresses (0.0.0.0)
      proxy: {
        '/api': {
          target: env.VITE_API_BASE_URL || 'http://localhost:8000', // Configurable backend target
          changeOrigin: true,
          secure: false,
        },
      },
    },
    define: {
      'process.env': {}
    }
  };
});
