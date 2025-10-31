import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: [
        'vue',
        'vue-router',
        'pinia',
        {
          'element-plus': [
            'ElMessage',
            'ElMessageBox',
            'ElNotification',
            'ElLoading'
          ]
        }
      ],
      dts: true,
      eslintrc: {
        enabled: true
      }
    }),
    Components({
      resolvers: [ElementPlusResolver()]
    })
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  css: {
    preprocessorOptions: {
      scss: {
        additionalData: `@use "@/styles/variables.scss" as *;`
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    open: true,
    // 只在开发环境使用代理，生产环境直接访问本站目录
    proxy: process.env.NODE_ENV === 'development' ? {
      '/api': {
        // target: 'http://127.0.0.1:8082',
        // target: 'http://192.168.95.11:8082',
        target: 'http://10.20.1.201:8082',
        changeOrigin: true
      }
    } : undefined
  },
  // 设置为/ai/路径，适配部署在服务端的/ai/目录下
  base: process.env.NODE_ENV === 'production' ? '/ai/' : '/',
  
  build: {
    target: 'es2015',
    // 构建输出目录设置为backend下的ui目录
    outDir: process.env.NODE_ENV === 'production' ? '../backend/ai' : 'dist',
    // 静态资源目录
    assetsDir: 'static',
    sourcemap: false,
    minify: 'terser',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        chunkFileNames: 'static/js/[name]-[hash].js',
        entryFileNames: 'static/js/[name]-[hash].js',
        assetFileNames: 'static/[ext]/[name]-[hash].[ext]',
        manualChunks: {
          vue: ['vue', 'vue-router', 'pinia'],
          elementPlus: ['element-plus', '@element-plus/icons-vue'],
          echarts: ['echarts', 'vue-echarts'],
          utils: ['axios', 'dayjs', 'lodash-es']
        }
      }
    }
  },
  define: {
    __VUE_OPTIONS_API__: false,
    __VUE_PROD_DEVTOOLS__: false
  }
})