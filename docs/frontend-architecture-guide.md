# 分散前端架构指南

## 项目概述

本项目采用分散的前端架构，包含三个独立的前端应用：

- **主前端 (frontend)** - ACWL AI大模型管理平台前端 (端口: 3000)
- **数据中心前端 (dc_frontend)** - 数据资源中心前端应用 (端口: 3005)  
- **工作流前端 (taskflow-frontend)** - ACWL AI工作流管理平台前端 (端口: 3001)

## 架构优势

### 1. 独立开发
- 每个前端项目可以独立开发、测试和部署
- 不同团队可以并行工作，减少代码冲突
- 技术栈可以根据具体需求灵活选择

### 2. 性能优化
- 按需加载，用户只下载所需功能的代码
- 独立的构建优化策略
- 更小的包体积和更快的加载速度

### 3. 维护性
- 代码边界清晰，便于维护和调试
- 故障隔离，一个应用的问题不会影响其他应用
- 更容易进行重构和升级

## 技术栈规范

### 统一技术栈
- **框架**: Vue 3 + TypeScript
- **构建工具**: Vite
- **UI组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP客户端**: Axios
- **代码规范**: ESLint + Prettier

### 版本管理建议
```json
{
  "vue": "^3.4.0",
  "element-plus": "^2.10.6",
  "pinia": "^2.1.7",
  "vue-router": "^4.2.5",
  "axios": "^1.11.0",
  "dayjs": "^1.11.13"
}
```

## 开发规范

### 1. 项目结构
```
frontend-project/
├── src/
│   ├── components/     # 通用组件
│   ├── views/         # 页面组件
│   ├── stores/        # Pinia状态管理
│   ├── router/        # 路由配置
│   ├── api/           # API接口
│   ├── utils/         # 工具函数
│   ├── styles/        # 样式文件
│   └── types/         # TypeScript类型定义
├── public/            # 静态资源
└── dist/              # 构建输出
```

### 2. 命名规范
- **组件**: PascalCase (如: `UserProfile.vue`)
- **文件夹**: kebab-case (如: `user-management/`)
- **API文件**: camelCase (如: `userApi.ts`)
- **常量**: UPPER_SNAKE_CASE (如: `API_BASE_URL`)

### 3. 代码注释规范
```typescript
/**
 * 用户信息管理组件
 * @description 提供用户信息的展示、编辑和删除功能
 * @author 开发者姓名
 * @date 2024-01-01
 */
export default defineComponent({
  name: 'UserProfile',
  // ...
})

/**
 * 获取用户列表
 * @param params 查询参数
 * @returns Promise<UserListResponse> 用户列表响应
 */
export const getUserList = async (params: UserQueryParams): Promise<UserListResponse> => {
  // 实现逻辑
}
```

## 构建配置规范

### 基础Vite配置
```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig({
  plugins: [
    vue(),
    AutoImport({
      resolvers: [ElementPlusResolver()],
      imports: ['vue', 'vue-router', 'pinia'],
      dts: true,
      eslintrc: { enabled: true }
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
  server: {
    host: '0.0.0.0',
    port: 3000, // 各项目使用不同端口
    proxy: {
      '/api': {
        target: 'http://localhost:8082',
        changeOrigin: true
      }
    }
  }
})
```

### 生产环境优化
```typescript
build: {
  target: 'es2015',
  minify: 'terser',
  outDir: 'dist',
  sourcemap: false,
  rollupOptions: {
    output: {
      manualChunks: {
        vendor: ['vue', 'vue-router', 'pinia'],
        elementPlus: ['element-plus', '@element-plus/icons-vue'],
        utils: ['axios', 'dayjs']
      }
    }
  }
}
```

## 部署配置

### 1. 端口分配
- 主前端: 3000
- 工作流前端: 3001
- 数据中心前端: 3005

### 2. 代理配置
所有前端项目统一代理到后端API服务器 `http://localhost:8082`

### 3. 构建脚本
```json
{
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "build:check": "vue-tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .vue,.js,.jsx,.cjs,.mjs,.ts,.tsx,.cts,.mts --fix",
    "format": "prettier --write src/"
  }
}
```

## 共享资源管理

### 1. 设计系统
- 统一的颜色规范
- 统一的字体和间距
- 统一的组件样式

### 2. 工具函数
- 日期处理工具
- 数据格式化工具
- 验证工具
- HTTP请求封装

### 3. 类型定义
- API响应类型
- 业务数据类型
- 组件Props类型

## 最佳实践

### 1. 开发流程
1. 创建功能分支
2. 本地开发和测试
3. 代码审查
4. 合并到主分支
5. 独立部署

### 2. 性能优化
- 使用懒加载路由
- 合理拆分代码块
- 优化图片和静态资源
- 启用Gzip压缩

### 3. 错误处理
- 统一的错误处理机制
- 用户友好的错误提示
- 错误日志收集

### 4. 安全考虑
- API接口鉴权
- XSS防护
- CSRF防护
- 敏感信息保护

## 维护指南

### 1. 依赖更新
- 定期检查依赖版本
- 测试兼容性
- 渐进式升级

### 2. 代码质量
- 定期代码审查
- 单元测试覆盖
- 性能监控

### 3. 文档维护
- 及时更新API文档
- 维护组件文档
- 更新部署文档

## 总结

分散的前端架构为我们提供了更好的开发体验和维护性。通过遵循统一的规范和最佳实践，我们可以确保各个前端项目的质量和一致性，同时保持独立性和灵活性。