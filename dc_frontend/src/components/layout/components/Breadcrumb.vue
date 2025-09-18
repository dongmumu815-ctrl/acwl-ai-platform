<template>
  <el-breadcrumb class="app-breadcrumb" separator="/">
    <transition-group name="breadcrumb" tag="div" class="breadcrumb-container">
      <el-breadcrumb-item
        v-for="(item, index) in breadcrumbs"
        :key="item.path"
        :class="{ 'no-redirect': item.redirect === 'noRedirect' }"
      >
        <span
          v-if="item.redirect === 'noRedirect' || index === breadcrumbs.length - 1"
          class="no-redirect"
        >
          {{ item.meta?.title }}
        </span>
        <a v-else @click.prevent="handleLink(item)">
          {{ item.meta?.title }}
        </a>
      </el-breadcrumb-item>
    </transition-group>
  </el-breadcrumb>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { RouteLocationMatched } from 'vue-router'

/**
 * 面包屑导航组件
 * 根据当前路由自动生成面包屑导航
 */

const route = useRoute()
const router = useRouter()

// 面包屑数据
const breadcrumbs = ref<RouteLocationMatched[]>([])

/**
 * 获取面包屑数据
 */
function getBreadcrumb(): void {
  // 过滤掉不需要显示在面包屑中的路由
  let matched = route.matched.filter(item => {
    return item.meta && item.meta.title && item.meta.breadcrumb !== false
  })

  // 获取第一个匹配的路由
  const first = matched[0]

  // 如果第一个路由不是首页，则添加首页到面包屑
  if (!isDashboard(first)) {
    matched = [
      {
        path: '/dashboard',
        meta: { title: '首页', icon: 'dashboard' }
      } as RouteLocationMatched
    ].concat(matched)
  }

  breadcrumbs.value = matched.filter(item => {
    return item.meta && item.meta.title && item.meta.breadcrumb !== false
  })
}

/**
 * 判断是否为首页
 * @param route 路由对象
 */
function isDashboard(route: RouteLocationMatched): boolean {
  const name = route && route.name
  if (!name) {
    return false
  }
  return name.toString().trim().toLocaleLowerCase() === 'dashboard'
}

/**
 * 处理面包屑点击
 * @param item 路由项
 */
function handleLink(item: RouteLocationMatched): void {
  const { redirect, path } = item
  
  if (redirect) {
    router.push(redirect as string)
    return
  }
  
  router.push(path)
}

// 监听路由变化
watch(
  () => route.path,
  () => {
    getBreadcrumb()
  },
  { immediate: true }
)
</script>

<style lang="scss" scoped>
@import '@/styles/variables.scss';

.app-breadcrumb {
  display: inline-block;
  font-size: 14px;
  line-height: $navbar-height;
  
  .breadcrumb-container {
    display: flex;
    align-items: center;
  }
  
  :deep(.el-breadcrumb__item) {
    .el-breadcrumb__inner {
      font-weight: 400;
      color: var(--el-text-color-secondary);
      transition: color 0.3s ease;
      
      a {
        color: var(--el-text-color-secondary);
        text-decoration: none;
        transition: all 0.3s ease;
        padding: 2px 4px;
        border-radius: 4px;
        
        &:hover {
          color: var(--el-color-primary);
          background: var(--el-color-primary-light-9);
        }
      }
      
      &.is-link {
        color: var(--el-text-color-secondary);
        
        &:hover {
          color: var(--el-color-primary);
        }
      }
    }
    
    &:last-child {
      .el-breadcrumb__inner {
        color: var(--el-text-color-primary);
        font-weight: 500;
        
        &.no-redirect {
          color: var(--el-text-color-primary);
          cursor: text;
        }
      }
    }
    
    .el-breadcrumb__separator {
      color: var(--el-text-color-placeholder);
      font-weight: 400;
      margin: 0 8px;
    }
  }
  
  .no-redirect {
    color: var(--el-text-color-primary);
    cursor: text;
  }
}

// 面包屑动画
.breadcrumb-enter-active,
.breadcrumb-leave-active {
  transition: all 0.3s ease;
}

.breadcrumb-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.breadcrumb-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.breadcrumb-move {
  transition: transform 0.3s ease;
}

// 暗色主题适配
.dark {
  .app-breadcrumb {
    :deep(.el-breadcrumb__item) {
      .el-breadcrumb__inner {
        color: var(--el-text-color-secondary);
        
        a {
          color: var(--el-text-color-secondary);
          
          &:hover {
            color: var(--el-color-primary);
            background: rgba(255, 255, 255, 0.1);
          }
        }
      }
      
      &:last-child {
        .el-breadcrumb__inner {
          color: var(--el-text-color-primary);
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .app-breadcrumb {
    font-size: 13px;
    
    :deep(.el-breadcrumb__item) {
      .el-breadcrumb__separator {
        margin: 0 6px;
      }
    }
  }
}

@media (max-width: 480px) {
  .app-breadcrumb {
    font-size: 12px;
    
    // 在小屏幕上隐藏中间的面包屑项，只显示首页和当前页
    :deep(.el-breadcrumb__item) {
      &:not(:first-child):not(:last-child) {
        display: none;
      }
      
      &:first-child:not(:last-child)::after {
        content: '...';
        color: var(--el-text-color-placeholder);
        margin: 0 6px;
      }
    }
  }
}
</style>