# 共享组件库指南

## 概述

为了在分散的前端架构中实现代码复用和设计一致性，我们需要建立一套共享组件库和设计系统。本指南定义了共享组件的开发、使用和维护规范。

## 设计原则

### 1. 一致性
- 统一的视觉风格
- 统一的交互行为
- 统一的API设计

### 2. 可复用性
- 组件功能单一且明确
- 支持灵活的配置
- 良好的扩展性

### 3. 可维护性
- 清晰的文档说明
- 完善的类型定义
- 充分的测试覆盖

## 设计系统规范

### 1. 颜色规范
```scss
// 主色调
$primary-color: #409eff;
$success-color: #67c23a;
$warning-color: #e6a23c;
$danger-color: #f56c6c;
$info-color: #909399;

// 中性色
$text-primary: #303133;
$text-regular: #606266;
$text-secondary: #909399;
$text-placeholder: #c0c4cc;

// 边框色
$border-base: #dcdfe6;
$border-light: #e4e7ed;
$border-lighter: #ebeef5;
$border-extra-light: #f2f6fc;

// 背景色
$bg-color: #ffffff;
$bg-color-page: #f2f3f5;
$bg-color-overlay: #ffffff;
```

### 2. 间距规范
```scss
// 间距系统 (4px基准)
$spacing-xs: 4px;
$spacing-sm: 8px;
$spacing-md: 16px;
$spacing-lg: 24px;
$spacing-xl: 32px;
$spacing-xxl: 48px;

// 组件内边距
$padding-xs: 4px 8px;
$padding-sm: 8px 12px;
$padding-md: 12px 16px;
$padding-lg: 16px 24px;
```

### 3. 字体规范
```scss
// 字体大小
$font-size-xs: 12px;
$font-size-sm: 14px;
$font-size-md: 16px;
$font-size-lg: 18px;
$font-size-xl: 20px;
$font-size-xxl: 24px;

// 行高
$line-height-sm: 1.2;
$line-height-md: 1.5;
$line-height-lg: 1.8;

// 字重
$font-weight-light: 300;
$font-weight-normal: 400;
$font-weight-medium: 500;
$font-weight-bold: 700;
```

## 共享组件分类

### 1. 基础组件 (Basic Components)
- **Button** - 按钮组件
- **Input** - 输入框组件
- **Select** - 选择器组件
- **DatePicker** - 日期选择器
- **Upload** - 文件上传组件

### 2. 布局组件 (Layout Components)
- **Container** - 容器组件
- **Header** - 页头组件
- **Sidebar** - 侧边栏组件
- **Footer** - 页脚组件
- **Card** - 卡片组件

### 3. 数据展示组件 (Data Display Components)
- **Table** - 表格组件
- **Pagination** - 分页组件
- **Chart** - 图表组件
- **Tag** - 标签组件
- **Badge** - 徽章组件

### 4. 反馈组件 (Feedback Components)
- **Modal** - 模态框组件
- **Drawer** - 抽屉组件
- **Message** - 消息提示
- **Loading** - 加载组件
- **Empty** - 空状态组件

### 5. 业务组件 (Business Components)
- **UserAvatar** - 用户头像
- **StatusIndicator** - 状态指示器
- **SearchBox** - 搜索框
- **FilterPanel** - 筛选面板
- **ActionBar** - 操作栏

## 组件开发规范

### 1. 组件结构
```vue
<template>
  <div class="shared-component" :class="componentClasses">
    <!-- 组件内容 -->
    <slot />
  </div>
</template>

<script setup lang="ts">
/**
 * 共享组件示例
 * @description 这是一个共享组件的示例
 * @author 开发者姓名
 * @date 2024-01-01
 */
import { computed } from 'vue'

// Props定义
interface Props {
  /** 组件大小 */
  size?: 'small' | 'medium' | 'large'
  /** 是否禁用 */
  disabled?: boolean
  /** 组件类型 */
  type?: 'primary' | 'secondary' | 'danger'
}

const props = withDefaults(defineProps<Props>(), {
  size: 'medium',
  disabled: false,
  type: 'primary'
})

// Emits定义
interface Emits {
  /** 点击事件 */
  click: [event: MouseEvent]
  /** 值变化事件 */
  change: [value: any]
}

const emit = defineEmits<Emits>()

// 计算属性
const componentClasses = computed(() => ({
  [`shared-component--${props.size}`]: true,
  [`shared-component--${props.type}`]: true,
  'shared-component--disabled': props.disabled
}))

// 方法
const handleClick = (event: MouseEvent) => {
  if (!props.disabled) {
    emit('click', event)
  }
}
</script>

<style lang="scss" scoped>
.shared-component {
  // 组件样式
  &--small {
    // 小尺寸样式
  }
  
  &--medium {
    // 中等尺寸样式
  }
  
  &--large {
    // 大尺寸样式
  }
  
  &--disabled {
    // 禁用状态样式
  }
}
</style>
```

### 2. 类型定义
```typescript
// types/components.ts

/** 组件大小类型 */
export type ComponentSize = 'small' | 'medium' | 'large'

/** 组件状态类型 */
export type ComponentStatus = 'success' | 'warning' | 'error' | 'info'

/** 按钮类型 */
export type ButtonType = 'primary' | 'secondary' | 'danger' | 'text'

/** 表格列配置 */
export interface TableColumn {
  /** 列标题 */
  title: string
  /** 数据字段 */
  dataIndex: string
  /** 列宽度 */
  width?: number | string
  /** 是否可排序 */
  sortable?: boolean
  /** 自定义渲染 */
  render?: (value: any, record: any, index: number) => any
}

/** 分页配置 */
export interface PaginationConfig {
  /** 当前页码 */
  current: number
  /** 每页条数 */
  pageSize: number
  /** 总条数 */
  total: number
  /** 显示快速跳转 */
  showQuickJumper?: boolean
  /** 显示每页条数选择器 */
  showSizeChanger?: boolean
}
```

### 3. 工具函数
```typescript
// utils/shared.ts

/**
 * 格式化日期
 * @param date 日期对象或时间戳
 * @param format 格式化字符串
 * @returns 格式化后的日期字符串
 */
export const formatDate = (date: Date | number | string, format = 'YYYY-MM-DD HH:mm:ss'): string => {
  // 实现日期格式化逻辑
}

/**
 * 防抖函数
 * @param fn 要防抖的函数
 * @param delay 延迟时间
 * @returns 防抖后的函数
 */
export const debounce = <T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): ((...args: Parameters<T>) => void) => {
  // 实现防抖逻辑
}

/**
 * 节流函数
 * @param fn 要节流的函数
 * @param interval 间隔时间
 * @returns 节流后的函数
 */
export const throttle = <T extends (...args: any[]) => any>(
  fn: T,
  interval: number
): ((...args: Parameters<T>) => void) => {
  // 实现节流逻辑
}

/**
 * 深拷贝对象
 * @param obj 要拷贝的对象
 * @returns 拷贝后的对象
 */
export const deepClone = <T>(obj: T): T => {
  // 实现深拷贝逻辑
}

/**
 * 生成唯一ID
 * @param prefix 前缀
 * @returns 唯一ID字符串
 */
export const generateId = (prefix = 'id'): string => {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}
```

## 使用指南

### 1. 组件引入
```typescript
// 在各个前端项目中使用共享组件
import { SharedButton, SharedTable, SharedModal } from '@/components/shared'

// 或者按需引入
import SharedButton from '@/components/shared/Button.vue'
```

### 2. 样式变量引入
```scss
// 在各个项目的样式文件中引入共享变量
@import '@/styles/shared/variables.scss';
@import '@/styles/shared/mixins.scss';
```

### 3. 工具函数使用
```typescript
import { formatDate, debounce, generateId } from '@/utils/shared'

// 使用工具函数
const formattedDate = formatDate(new Date())
const debouncedSearch = debounce(searchFunction, 300)
const uniqueId = generateId('component')
```

## 维护策略

### 1. 版本管理
- 使用语义化版本控制
- 主版本号：不兼容的API修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 2. 文档维护
- 每个组件都要有详细的使用文档
- 包含Props、Events、Slots说明
- 提供使用示例和最佳实践

### 3. 测试策略
- 单元测试覆盖所有组件
- 集成测试验证组件交互
- 视觉回归测试确保样式一致性

### 4. 更新流程
1. 在共享组件库中开发新功能
2. 编写测试和文档
3. 发布新版本
4. 在各个前端项目中更新依赖
5. 验证兼容性和功能

## 最佳实践

### 1. 组件设计
- 保持组件功能单一
- 提供合理的默认值
- 支持灵活的自定义
- 考虑无障碍访问

### 2. 性能优化
- 使用懒加载减少初始包大小
- 合理使用计算属性和监听器
- 避免不必要的重新渲染
- 优化大列表渲染

### 3. 兼容性
- 确保在不同浏览器中正常工作
- 考虑移动端适配
- 支持主题切换
- 国际化支持

通过建立完善的共享组件库和设计系统，我们可以在保持各前端项目独立性的同时，实现代码复用和设计一致性，提高开发效率和用户体验。