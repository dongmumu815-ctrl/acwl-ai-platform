<template>
  <div class="sidebar-menu">
    <el-menu
      :default-active="activeMenu"
      :collapse="collapsed"
      :unique-opened="false"
      :collapse-transition="false"
      mode="vertical"
      class="sidebar-menu-el"
      @select="handleMenuSelect"
    >
      <SidebarMenuItem
        v-for="route in menuRoutes"
        :key="route.path"
        :route="route"
        :base-path="route.path === '/' ? '' : route.path"
        :collapsed="collapsed"
      />
    </el-menu>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useUserStore } from "@/stores/user";
import { authRoutes } from "@/router";
import SidebarMenuItem from "./SidebarMenuItem.vue";
import type { RouteRecordRaw } from "vue-router";

/**
 * 侧边栏菜单组件
 * 根据路由配置和用户权限动态生成菜单
 * 按照新的四个模块结构：数据中心概览、数据资源管理、权限与用户、系统管理
 */

interface Props {
  collapsed: boolean;
}

defineProps<Props>();

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 计算当前激活的菜单
const activeMenu = computed(() => {
  const { meta, path } = route;
  // 如果设置了activeMenu，使用activeMenu
  if (meta?.activeMenu) {
    return meta.activeMenu as string;
  }
  return path;
});

// 过滤并生成菜单路由
const menuRoutes = computed(() => {
  return filterMenuRoutes(authRoutes);
});

/**
 * 过滤菜单路由
 * 根据用户权限和路由配置过滤显示的菜单项
 * @param routes 路由配置
 * @param basePath 基础路径
 */
function filterMenuRoutes(
  routes: RouteRecordRaw[],
  basePath = ""
): RouteRecordRaw[] {
  const filteredRoutes: RouteRecordRaw[] = [];

  routes.forEach((route) => {
    const tmp = { ...route };

    // 检查是否应该显示在菜单中
    if (shouldShowInMenu(tmp)) {
      // 检查用户权限
      if (hasPermission(tmp)) {
        // 处理子路由
        if (tmp.children) {
          const childRoutes = filterMenuRoutes(tmp.children, tmp.path);
          if (childRoutes.length > 0) {
            tmp.children = childRoutes;
            filteredRoutes.push(tmp);
          }
        } else {
          filteredRoutes.push(tmp);
        }
      }
    }
  });

  return filteredRoutes;
}

/**
 * 检查路由是否应该显示在菜单中
 * @param route 路由配置
 */
function shouldShowInMenu(route: RouteRecordRaw): boolean {
  // 如果明确设置了hideInMenu为true，则不显示
  if (route.meta?.hideInMenu) {
    return false;
  }

  // 如果没有设置title，则不显示
  if (!route.meta?.title) {
    return false;
  }

  return true;
}

/**
 * 检查用户是否有权限访问路由
 * @param route 路由配置
 */
function hasPermission(route: RouteRecordRaw): boolean {
  /**
   * 菜单权限检查（与路由守卫一致）
   * - requiresAuth: 需登录
   * - roles: 任一角色满足
   * - permission: 单个权限码满足
   * - permissionsAny: 任一权限满足
   * - permissionsAll: 所有权限满足
   */
  // 登录要求
  if (route.meta?.requiresAuth && !userStore.isLoggedIn) {
    return false;
  }

  // 角色检查
  if (route.meta?.roles) {
    const roles = route.meta.roles as string[];
    if (!roles.some((role) => userStore.hasRole(role))) {
      return false;
    }
  }

  // 单个权限码
  if (route.meta?.permission) {
    const perm = route.meta.permission as string
    const useStrict = Boolean((route.meta as any)?.strictPermission)
    const ok = useStrict ? userStore.hasPermissionStrict(perm) : userStore.hasPermission(perm)
    if (!ok) {
      return false;
    }
  }

  // 任一权限
  if (route.meta?.permissionsAny) {
    const any = route.meta.permissionsAny as string[];
    const useStrict = Boolean((route.meta as any)?.strictPermission)
    const ok = useStrict
      ? any.some((p) => userStore.hasPermissionStrict(p))
      : userStore.hasAnyPermission(any)
    if (!ok) {
      return false;
    }
  }

  // 所有权限
  if (route.meta?.permissionsAll) {
    const all = route.meta.permissionsAll as string[];
    const useStrict = Boolean((route.meta as any)?.strictPermission)
    const ok = useStrict
      ? all.every((p) => userStore.hasPermissionStrict(p))
      : userStore.hasAllPermissions(all)
    if (!ok) {
      return false;
    }
  }

  return true;
}

/**
 * 处理菜单选择
 * @param index 菜单索引（路径）
 */
function handleMenuSelect(index: string): void {
  console.log("=== 菜单点击调试信息 ===");
  console.log("点击的菜单路径:", index);
  console.log("当前路由路径:", route.path);
  console.log("当前路由名称:", route.name);
  console.log("当前路由meta:", route.meta);
  console.log("用户角色:", userStore.userRoles);
  console.log("用户权限:", userStore.userPermissions);
  console.log("========================");

  // 如果是外部链接
  if (isExternalLink(index)) {
    console.log("检测到外部链接，在新窗口打开:", index);
    window.open(index, "_blank");
    return;
  }

  // 内部路由跳转
  if (index !== route.path) {
    console.log("准备跳转到路由:", index);
    router
      .push(index)
      .then(() => {
        console.log("路由跳转成功到:", index);
        console.log("跳转后当前路由:", router.currentRoute.value.path);
      })
      .catch((error) => {
        console.error("路由跳转失败:", error);
        console.error("错误详情:", error.message);
      });
  } else {
    console.log("路径相同，不进行跳转");
  }
}

/**
 * 检查是否为外部链接
 * @param path 路径
 */
function isExternalLink(path: string): boolean {
  return /^(https?:|mailto:|tel:)/.test(path);
}
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.sidebar-menu {
  height: 100%;

  .sidebar-menu-el {
    border: none;
    height: 100%;
    width: 100% !important;
    overflow: auto;
    padding-bottom: 10px;
    background-color: transparent;

    // 菜单项样式
    :deep(.el-menu-item) {
      height: 48px;
      line-height: 48px;
      padding: 0 16px;
      margin: 2px 8px;
      border-radius: 6px;
      color: var(--el-text-color-primary);
      transition: all 0.3s ease;

      &:hover {
        background-color: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
      }

      &.is-active {
        background-color: var(--el-color-primary-light-9);
        color: var(--el-color-primary);
        font-weight: 600;

        &::before {
          content: "";
          position: absolute;
          left: 0;
          top: 50%;
          transform: translateY(-50%);
          width: 3px;
          height: 20px;
          background-color: var(--el-color-primary);
          border-radius: 0 2px 2px 0;
        }
      }

      .el-icon {
        margin-right: 8px;
        font-size: 18px;
      }
    }

    // 子菜单样式
    :deep(.el-sub-menu) {
      .el-sub-menu__title {
        height: 48px;
        line-height: 48px;
        padding: 0 16px;
        margin: 2px 8px;
        border-radius: 6px;
        color: var(--el-text-color-primary);
        transition: all 0.3s ease;

        &:hover {
          background-color: var(--el-color-primary-light-9);
          color: var(--el-color-primary);
        }

        .el-icon {
          margin-right: 8px;
          font-size: 18px;
        }

        .el-sub-menu__icon-arrow {
          font-size: 12px;
          transition: transform 0.3s ease;
        }
      }

      &.is-opened {
        .el-sub-menu__title {
          .el-sub-menu__icon-arrow {
            transform: rotateZ(90deg);
          }
        }
      }

      .el-menu {
        background-color: transparent;

        .el-menu-item {
          padding-left: 45px;
          // margin-left: 25px;
          height: 40px;
          line-height: 40px;
          font-size: 14px;

          &.is-active {
            &::before {
              left: 24px;
              // left: 15px;
            }
          }
        }
      }
    }

    // 折叠状态样式
    &.el-menu--collapse {
      width: $sidebar-collapsed-width;

      .el-menu-item,
      .el-sub-menu__title {
        padding: 0;
        text-align: center;

        .el-icon {
          margin-right: 0;
          font-size: 20px;
        }

        span {
          display: none;
        }
      }

      .el-sub-menu {
        .el-sub-menu__title {
          .el-sub-menu__icon-arrow {
            display: none;
          }
        }
      }
    }
  }
}

.is-collapsed {
  .sidebar-menu {
    :deep(.el-sub-menu) {
        &.is-opened {
          .el-sub-menu__title {
            .el-sub-menu__icon-arrow {
              color: var(--el-color-primary);
              transform: rotateZ(90deg) !important;
            }
          }
        }
    }
  }
}

// 暗色主题适配
.dark {
  .sidebar-menu {
    .sidebar-menu-el {
      :deep(.el-menu-item) {
        color: var(--el-text-color-primary);

        &:hover {
          background-color: rgba(255, 255, 255, 0.1);
          color: var(--el-color-primary);
        }

        &.is-active {
          background-color: rgba(255, 255, 255, 0.1);
          color: var(--el-color-primary);
        }
      }

      :deep(.el-sub-menu) {
        .el-sub-menu__title {
          color: var(--el-text-color-primary);

          &:hover {
            background-color: rgba(255, 255, 255, 0.1);
            color: var(--el-color-primary);
          }
        }
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar-menu {
    .sidebar-menu-el {
      :deep(.el-menu-item),
      :deep(.el-sub-menu__title) {
        height: 44px;
        line-height: 44px;
        padding: 0 12px;
        margin: 1px 4px;
      }
    }
  }
}
</style>