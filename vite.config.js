import { defineConfig } from 'vite'
import { resolve } from 'path'

export default defineConfig({
  base: '/static/',
  build: {
    manifest: 'manifest.json',
    outDir: resolve('./static'),
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'frontend/src/js/main.js'),
      },
    },
    emptyOutDir: true,
  },
})
