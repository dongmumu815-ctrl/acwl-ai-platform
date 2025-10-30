<template>
  <div class="app-header">
    <div class="header-left">
      <el-button
        type="text"
        @click="$emit('toggle-sidebar')"
        class="sidebar-toggle"
      >
        <el-icon><Expand v-if="collapsed" /><Fold v-else /></el-icon>
      </el-button>

      <!-- <div class="breadcrumb">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>数据中心</el-breadcrumb-item>
        </el-breadcrumb>
      </div> -->
      <!-- 面包屑导航 -->
      <div class="breadcrumb-container" v-if="showBreadcrumb">
        <Breadcrumb />
      </div>
    </div>

    <div class="header-right">
      <el-dropdown trigger="click">
        <div class="user-info">
          <el-avatar
            :size="32"
            :src="userInfo?.avatar || '/avatar.png'"
            :alt="userName"
          />
          <span class="username">{{ userName }}</span>
          <el-icon><ArrowDown /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="$router.push('/profile')">
              <el-icon><User /></el-icon>
              个人中心
            </el-dropdown-item>
            <el-dropdown-item @click="$router.push('/settings')">
              <el-icon><Setting /></el-icon>
              系统设置
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon>
              退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useRouter, useRoute } from "vue-router";
import { useUserStore } from "@/stores/user";

/**
 * 定义组件属性
 */
interface Props {
  collapsed: boolean;
}

/**
 * 定义组件事件
 */
interface Emits {
  (e: "toggle-sidebar"): void;
}

defineProps<Props>();
defineEmits<Emits>();

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 计算用户信息
const userInfo = computed(() => userStore.userInfo);
const userName = computed(() => {
  if (userInfo.value) {
    return (
      userInfo.value.username ||
      userInfo.value.email ||
      "用户"
    );
  }
  return "未登录";
});

const showBreadcrumb = computed(() => {
  return !route.meta?.hideBreadcrumb && route.name !== "Dashboard";
});

/**
 * 处理用户退出登录
 */
const handleLogout = async () => {
  try {
    await ElMessageBox.confirm("确定要退出登录吗？", "提示", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning"
    });

    await userStore.logout();
    ElMessage.success("退出登录成功");
    router.push("/login");
  } catch (error: any) {
    if (error !== "cancel") {
      console.error("退出登录失败:", error);
      // 即使退出接口失败，也要清除本地状态并跳转
      userStore.reset();
      router.push("/login");
    }
  }
};
</script>

<style lang="scss" scoped>
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 16px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color-light);

  .header-left {
    display: flex;
    align-items: center;
    gap: 16px;

    .sidebar-toggle {
      padding: 8px;
      font-size: 18px;
      color: var(--el-text-color-regular);

      &:hover {
        color: var(--el-color-primary);
      }
    }

    .breadcrumb {
      :deep(.el-breadcrumb__item) {
        .el-breadcrumb__inner {
          color: var(--el-text-color-regular);
          font-weight: normal;

          &:hover {
            color: var(--el-color-primary);
          }
        }

        &:last-child .el-breadcrumb__inner {
          color: var(--el-text-color-primary);
          font-weight: 500;
        }
      }
    }
  }

  .header-right {
    .user-info {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      transition: background-color 0.3s;

      &:hover {
        background: var(--el-fill-color-light);
      }

      .username {
        font-size: 14px;
        color: var(--el-text-color-primary);
      }

      .el-icon {
        font-size: 12px;
        color: var(--el-text-color-regular);
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .app-header {
    .header-left {
      .breadcrumb {
        display: none;
      }
    }

    .header-right {
      .user-info {
        .username {
          display: none;
        }
      }
    }
  }
}
</style>