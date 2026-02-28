<template>
  <div class="sidebar-menu-item">
    <!-- 有子菜单的情况 -->
    <el-sub-menu
      v-if="hasChildren"
      :index="resolvePath(route.path)"
      :popper-class="`sidebar-submenu-popper ${collapsed ? 'is-collapsed' : ''}`"
    >
      <template #title>
        <el-icon v-if="route.meta?.icon">
          <component :is="route.meta.icon" />
        </el-icon>
        <span v-if="!collapsed">{{ route.meta?.title }}</span>
      </template>

      <SidebarMenuItem
        v-for="child in route.children"
        :key="child.path"
        :route="child"
        :base-path="props.basePath"
        :collapsed="collapsed"
      />
    </el-sub-menu>

    <!-- 没有子菜单的情况 -->
    <el-menu-item
      v-else
      :index="resolvePath(route.path)"
      :class="{ 'is-external': isExternalLink(resolvePath(route.path)) }"
    >
      <el-icon v-if="route.meta?.icon">
        <component :is="route.meta.icon" />
      </el-icon>
      <template #title>
        <span>{{ route.meta?.title }}</span>
        <el-icon
          v-if="isExternalLink(resolvePath(route.path))"
          class="external-link-icon"
        >
          <Link />
        </el-icon>
      </template>
    </el-menu-item>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { isExternal } from "@/utils/validate";
import type { RouteRecordRaw } from "vue-router";
import { Link } from "@element-plus/icons-vue";

/**
 * 侧边栏菜单项组件
 * 递归渲染菜单结构，支持多级菜单
 */

interface Props {
  route: RouteRecordRaw;
  basePath: string;
  collapsed: boolean;
}

const props = defineProps<Props>();

// 计算是否有子菜单
const hasChildren = computed(() => {
  const children = props.route.children;
  if (!children || children.length === 0) {
    return false;
  }

  // 过滤掉隐藏的子菜单
  const visibleChildren = children.filter((child) => {
    return !child.meta?.hideInMenu && child.meta?.title;
  });

  return visibleChildren.length > 0;
});

/**
 * 解析路径
 * 将相对路径转换为绝对路径
 * @param routePath 路由路径
 */
function resolvePath(routePath: string): string {
  if (isExternalLink(routePath)) {
    return routePath;
  }

  if (isExternalLink(props.basePath)) {
    return props.basePath;
  }

  // 如果是绝对路径，直接返回
  if (routePath.startsWith("/")) {
    return routePath;
  }

  // 如果basePath为空（根路径情况），直接返回子路径
  if (!props.basePath || props.basePath === "") {
    return `/${routePath}`;
  }

  // 拼接基础路径
  const basePath = props.basePath.endsWith("/")
    ? props.basePath.slice(0, -1)
    : props.basePath;

  return `${basePath}/${routePath}`.replace(/\/+/g, "/");
}

/**
 * 检查是否为外部链接
 * @param path 路径
 */
function isExternalLink(path: string): boolean {
  return isExternal(path);
}
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.sidebar-menu-item {
  // 外部链接图标样式
  .external-link-icon {
    margin-left: auto;
    font-size: 12px;
    opacity: 0.6;
  }

  // 菜单项悬停效果
  :deep(.el-menu-item) {
    position: relative;
    overflow: hidden;

    &::before {
      content: "";
      position: absolute;
      left: -100%;
      top: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.1),
        transparent
      );
      transition: left 0.5s ease;
    }

    &:hover::before {
      left: 100%;
    }
  }

  // 子菜单标题样式
  :deep(.el-sub-menu__title) {
    position: relative;
    overflow: hidden;

    &::before {
      content: "";
      position: absolute;
      left: -100%;
      top: 0;
      width: 100%;
      height: 100%;
      background: linear-gradient(
        90deg,
        transparent,
        rgba(255, 255, 255, 0.1),
        transparent
      );
      transition: left 0.5s ease;
    }

    &:hover::before {
      left: 100%;
    }
  }
}

// 折叠状态下的子菜单弹出层样式
:deep(.sidebar-submenu-popper) {
  &.is-collapsed {
    margin-left: 8px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    border: 1px solid var(--el-border-color-light);

    .el-menu {
      background-color: var(--el-bg-color-overlay);
      border-radius: 8px;

      .el-menu-item {
        height: 40px;
        line-height: 40px;
        padding: 0 16px;
        margin: 2px 4px;
        border-radius: 4px;

        &:hover {
          background-color: var(--el-color-primary-light-9);
        }

        &.is-active {
          background-color: var(--el-color-primary-light-9);
          color: var(--el-color-primary);
        }
      }
    }
  }
}

// 暗色主题适配
.dark {
  :deep(.sidebar-submenu-popper) {
    &.is-collapsed {
      background-color: var(--el-bg-color-overlay);
      border-color: var(--el-border-color);

      .el-menu {
        background-color: var(--el-bg-color-overlay);

        .el-menu-item {
          &:hover {
            background-color: rgba(255, 255, 255, 0.1);
          }

          &.is-active {
            background-color: rgba(255, 255, 255, 0.1);
          }
        }
      }
    }
  }
}

// 动画效果
.sidebar-menu-item {
  :deep(.el-menu-item),
  :deep(.el-sub-menu__title) {
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);

    &:hover {
      transform: translateX(2px);
    }
  }

  :deep(.el-sub-menu) {
    .el-menu {
      .el-menu-item {
        &:hover {
          transform: translateX(4px);
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar-menu-item {
    :deep(.el-menu-item),
    :deep(.el-sub-menu__title) {
      &:hover {
        transform: none;
      }
    }
  }
}
</style>
