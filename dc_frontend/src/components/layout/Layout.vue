<template>
  <div class="app-layout" :class="{ 'is-dark': isDark }">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ 'is-collapsed': isCollapsed }">
      <div class="sidebar-header">
        <div class="logo">
          <img
            v-if="!isCollapsed"
            :src="logoUrl"
            alt="数据资源中心"
            class="logo-img"
          />
          <img v-else :src="logoUrl" alt="DRC" class="logo-img-mini" />
          <span v-if="!isCollapsed" class="logo-text">数据资源中心</span>
        </div>
      </div>

      <div class="sidebar-content">
        <SidebarMenu :collapsed="isCollapsed" />
      </div>
    </div>

    <!-- 移动端遮罩层（侧边栏展开时显示） -->
    <div
      class="sidebar-overlay"
      v-if="showOverlay"
      @click="toggleSidebar"
    ></div>

    <!-- 主内容区域 -->
    <div class="main-container">
      <!-- 顶部导航栏 -->
      <div class="header">
        <AppHeader :collapsed="isCollapsed" @toggle-sidebar="toggleSidebar" />
      </div>

      <!-- 面包屑导航 -->
      <!-- <div class="breadcrumb-container" v-if="showBreadcrumb">
        <Breadcrumb />
      </div> -->

      <!-- 页面内容 -->
      <div class="content">
        <router-view v-slot="{ Component, route }">
          <transition name="fade-transform" mode="out-in">
            <keep-alive :include="keepAliveComponents">
              <component :is="Component" :key="route.path" />
            </keep-alive>
          </transition>
        </router-view>
      </div>

      <!-- 底部 -->
      <div class="footer" v-if="showFooter">
        <AppFooter />
      </div>
    </div>

    <!-- 设置面板 -->
    <SettingsPanel
      v-model:modelValue="showSettings"
      @settings-change="handleSettingsChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { useAppStore } from "@/stores/app";
import { useUserStore } from "@/stores/user";
import SidebarMenu from "./components/SidebarMenu.vue";
import AppHeader from "./components/AppHeader.vue";
import AppFooter from "./components/AppFooter.vue";
import Breadcrumb from "./components/Breadcrumb.vue";
import SettingsPanel from "./components/SettingsPanel.vue";
import logoUrl from "@/assets/logo2.png";

/**
 * 布局组件
 * 提供应用的整体布局结构
 */

const route = useRoute();
const appStore = useAppStore();
const userStore = useUserStore();

// 响应式状态
const showSettings = ref(false);
const isMobile = ref(false);

// 计算属性
const isCollapsed = computed(() => appStore.sidebar.collapsed);
const isDark = computed(() => appStore.theme === "dark");
const showBreadcrumb = computed(() => {
  return !route.meta?.hideBreadcrumb && route.name !== "Dashboard";
});
const showFooter = computed(() => {
  return !route.meta?.hideFooter;
});

// 需要缓存的组件
const keepAliveComponents = computed(() => {
  return appStore.cachedViews;
});

// 移动端遮罩显示逻辑
const showOverlay = computed(() => isMobile.value && !isCollapsed.value);

/**
 * 切换侧边栏折叠状态
 */
const toggleSidebar = (): void => {
  appStore.toggleSidebar();
};

/**
 * 处理窗口大小变化
 */
const handleResize = (): void => {
  const width = window.innerWidth;
  isMobile.value = width < 768;

  if (width < 768) {
    // 移动端自动折叠侧边栏
    if (!isCollapsed.value) {
      appStore.toggleSidebar();
    }
  }
};

/**
 * 监听键盘快捷键
 */
const handleKeydown = (event: KeyboardEvent): void => {
  // Ctrl/Cmd + K 打开搜索
  if ((event.ctrlKey || event.metaKey) && event.key === "k") {
    event.preventDefault();
    // TODO: 打开全局搜索
  }

  // Ctrl/Cmd + , 打开设置
  if ((event.ctrlKey || event.metaKey) && event.key === ",") {
    event.preventDefault();
    showSettings.value = true;
  }
};

/**
 * 设置变更回调（可接入持久化或状态同步）
 */
const handleSettingsChange = (settings: any): void => {
  // 这里可根据设置更新 appStore 或主题变量
};

// 生命周期
onMounted(() => {
  window.addEventListener("resize", handleResize);
  window.addEventListener("keydown", handleKeydown);

  // 初始化检查窗口大小
  handleResize();
});

onUnmounted(() => {
  window.removeEventListener("resize", handleResize);
  window.removeEventListener("keydown", handleKeydown);
});
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.app-layout {
  display: flex;
  height: 100vh;
  // background-color: var(--el-bg-color-page);

  &.is-dark {
    background-color: var(--el-bg-color-page);
  }
}

.sidebar {
  width: $sidebar-width;
  background-color: var(--el-bg-color);
  border-right: 1px solid var(--el-border-color-light);
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.08);
  transition: width 0.3s ease, transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  z-index: 1001;

  &.is-collapsed {
    width: $sidebar-collapsed-width;
  }

  .sidebar-header {
    height: $header-height;
    display: flex;
    align-items: center;
    padding: 0 16px;
    border-bottom: 1px solid var(--el-border-color-lighter);
    background-color: var(--el-bg-color);
    position: sticky;
    top: 0;
    z-index: 2;

    .logo {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 0 8px;
      border-radius: $border-radius-lg;
      cursor: pointer;
      transition: background-color 0.3s ease, opacity 0.3s ease;

      &:hover {
        background-color: var(--el-fill-color-light);
      }

      .logo-img,
      .logo-img-mini {
        width: 32px;
        height: 32px;
        object-fit: contain;
      }

      .logo-text {
        font-size: 18px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        white-space: nowrap;
        letter-spacing: 0.2px;
      }
    }
  }

  .sidebar-content {
    flex: 1;
    overflow-y: hidden;
    overflow-x: hidden;

    &::-webkit-scrollbar {
      width: 6px;
    }

    &::-webkit-scrollbar-track {
      background: transparent;
    }

    &::-webkit-scrollbar-thumb {
      background-color: var(--el-border-color);
      border-radius: 3px;

      &:hover {
        background-color: var(--el-border-color-dark);
      }
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-left: $sidebar-width;
  transition: margin-left 0.3s ease;
}

.header {
  height: $header-height;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);
  z-index: 999;
  position: sticky;
  top: 0;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.breadcrumb-container {
  padding: 5px 16px;
  background-color: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.content {
  flex: 1;
  overflow-y: auto;
  min-height: 0; // 让 flex 子项在容器内可滚动，避免被 100vh 限制
  // background-color: var(--el-bg-color-page);

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    // background: var(--el-bg-color-page);
  }

  &::-webkit-scrollbar-thumb {
    background-color: var(--el-border-color);
    border-radius: 4px;

    &:hover {
      background-color: var(--el-border-color-dark);
    }
  }
}

.footer {
  padding: 12px 16px;
  background-color: var(--el-bg-color);
  border-top: 1px solid var(--el-border-color-lighter);
  text-align: center;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

// 侧边栏与主内容的联动（折叠时收窄主内容左边距）
.sidebar.is-collapsed + .main-container {
  margin-left: $sidebar-collapsed-width;
}

// 移动端遮罩层样式
.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.3);
  z-index: 1000;
}

// 页面切换动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s ease;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

// 响应式设计
@media (max-width: 768px) {
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 1001;

    &.is-collapsed {
      transform: translateX(-100%);
    }
  }

  .main-container {
    margin-left: 0;
  }

  .content {
    padding: 12px;
  }
}

@media (max-width: 480px) {
  .content {
    padding: 8px;
  }

  .breadcrumb-container {
    padding: 3px 12px;
  }
}
</style>