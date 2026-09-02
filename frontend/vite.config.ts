import { defineConfig, splitVendorChunkPlugin } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    vue(),
    splitVendorChunkPlugin(), // auto-splits node_modules chunks intelligently
  ],

  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
    },
  },

  server: {
    port: 5173,
    // Warm up the most-visited modules on dev server start
    warmup: {
      clientFiles: [
        './src/main.ts',
        './src/App.vue',
        './src/layouts/AppLayout.vue',
        './src/components/shared/*.vue',
        './src/views/DashboardView.vue',
      ],
    },
    proxy: {
      '/api': {
        target:       'http://localhost:8000',
        changeOrigin: true,
        rewrite:      (path) => path.replace(/^\/api/, ''),
      },
    },
  },

  build: {
    // Raise the inline threshold: assets < 4 KB are inlined as base64
    assetsInlineLimit: 4096,
    // Enable CSS code splitting
    cssCodeSplit: true,
    // Use terser for smaller output
    minify: 'esbuild',
    target: 'es2020',
    rollupOptions: {
      output: {
        // Fine-grained manual chunk splitting
        manualChunks(id) {
          // ECharts gets its own large chunk
          if (id.includes('echarts') || id.includes('zrender') || id.includes('vue-echarts')) {
            return 'echarts'
          }
          // Vue ecosystem
          if (id.includes('vue-router') || id.includes('pinia')) {
            return 'vue-ecosystem'
          }
          // Utility libs
          if (id.includes('axios') || id.includes('dayjs') || id.includes('@vueuse')) {
            return 'utils'
          }
          // Vue core stays in its own chunk (auto)
        },
        // Deterministic chunk names for better cache hits
        chunkFileNames: 'assets/[name]-[hash].js',
        entryFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash].[ext]',
      },
    },
    // Show bundle size warnings at 600 KB (ECharts chunk will be large — expected)
    chunkSizeWarningLimit: 600,
  },

  // Pre-bundle these for fast cold starts in dev
  optimizeDeps: {
    include: [
      'vue',
      'vue-router',
      'pinia',
      'axios',
      'dayjs',
      '@vueuse/core',
    ],
    // ECharts excluded so it stays as a separate async chunk in dev too
    exclude: ['echarts', 'vue-echarts'],
  },
})
