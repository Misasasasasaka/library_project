import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig(({ command }) => {
  const isDev = command === 'serve'

  return {
    plugins: [vue()],

    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@components': resolve(__dirname, 'src/components'),
        '@utils': resolve(__dirname, 'src/utils'),
      }
    },

    build: {
      outDir: resolve(__dirname, '../static'),
      emptyOutDir: true,
      rollupOptions: {
        input: resolve(__dirname, 'index.html'),
        output: {
          assetFileNames: (assetInfo) => {
            const ext = assetInfo.name.split('.').pop()
            if (/css/i.test(ext)) {
              return 'css/[name]-[hash][extname]'
            }
            return 'assets/[name]-[hash][extname]'
          },
          chunkFileNames: 'js/[name]-[hash].js',
          entryFileNames: 'js/[name]-[hash].js',
        }
      },
      manifest: true,
    },

    server: {
      port: 5173,
      proxy: {
        '/api': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        },
        '/media': {
          target: 'http://127.0.0.1:8000',
          changeOrigin: true,
        }
      }
    }
  }
})
