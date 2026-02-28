<template>
  <div class="user-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <el-button
          type="text"
          :icon="ArrowLeft"
          class="back-btn"
          @click="router.back()"
        >
          返回
        </el-button>
        <div class="title-section">
          <h1>用户详情</h1>
          <p v-if="userInfo">
            查看 {{ userInfo.full_name || userInfo.username }} 的详细信息
          </p>
        </div>
      </div>
      <div class="header-right">
        <el-button
          v-if="canEdit"
          type="primary"
          :icon="Edit"
          @click="handleEdit"
        >
          编辑用户
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 用户信息 -->
    <div v-else-if="userInfo" class="user-content">
      <!-- 基本信息卡片 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <h3>基本信息</h3>
            <el-tag
              :type="userInfo.is_active ? 'success' : 'danger'"
              size="small"
            >
              {{ userInfo.is_active ? "启用" : "禁用" }}
            </el-tag>
          </div>
        </template>

        <div class="user-basic-info">
          <div class="avatar-section">
            <el-avatar
              :size="80"
              :src="userInfo.avatar"
              :alt="userInfo.full_name || userInfo.username"
            >
              <el-icon><User /></el-icon>
            </el-avatar>
          </div>

          <div class="info-grid">
            <div class="info-item">
              <label>用户名</label>
              <span>{{ userInfo.username }}</span>
            </div>
            <div class="info-item">
              <label>姓名</label>
              <span>{{ userInfo.full_name || "-" }}</span>
            </div>
            <div class="info-item">
              <label>邮箱</label>
              <span>{{ userInfo.email }}</span>
            </div>
            <div class="info-item">
              <label>手机号</label>
              <span>{{ userInfo.phone || "-" }}</span>
            </div>
            <div class="info-item">
              <label>部门</label>
              <span>{{ userInfo.department || "-" }}</span>
            </div>
            <div class="info-item">
              <label>职位</label>
              <span>{{ userInfo.position || "-" }}</span>
            </div>
            <div class="info-item">
              <label>角色</label>
              <el-tag size="small" type="primary">
                {{ getRoleLabel(userInfo.role) }}
              </el-tag>
            </div>
            <div class="info-item">
              <label>创建时间</label>
              <span>{{ formatDate(userInfo.created_at) }}</span>
            </div>
            <div class="info-item">
              <label>最后登录</label>
              <span>{{
                userInfo.last_login
                  ? formatDate(userInfo.last_login)
                  : "从未登录"
              }}</span>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 操作记录卡片 -->
      <el-card class="info-card">
        <template #header>
          <h3>操作记录</h3>
        </template>

        <div class="activity-section">
          <el-empty description="暂无操作记录" :image-size="100" />
        </div>
      </el-card>
    </div>

    <!-- 错误状态 -->
    <div v-else class="error-container">
      <el-result
        icon="error"
        title="加载失败"
        sub-title="无法加载用户信息，请稍后重试"
      >
        <template #extra>
          <el-button type="primary" @click="loadUserData"> 重新加载 </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { ArrowLeft, Edit, User } from "@element-plus/icons-vue";
import type { User as UserType } from "@/types/user";
import { getUserDetail } from "@/api/user";
import { formatDate } from "@/utils/date";
import { useUserStore } from "@/stores/user";

const route = useRoute();
const router = useRouter();
const userStore = useUserStore();

// 响应式数据
const loading = ref(true);
const userInfo = ref<UserType | null>(null);
const userId = computed(() => route.params.id as string);

// 权限检查
const canEdit = computed(() => {
  const currentUser = userStore.userInfo;
  if (!currentUser) return false;

  // 管理员可以编辑所有用户
  if (currentUser.role === "admin") return true;

  // 用户只能编辑自己的信息
  return currentUser.id.toString() === userId.value;
});

/**
 * 获取角色标签
 */
const getRoleLabel = (role: string) => {
  const roleMap: Record<string, string> = {
    admin: "管理员",
    user: "普通用户",
    viewer: "访客",
  };
  return roleMap[role] || role;
};

/**
 * 加载用户数据
 */
const loadUserData = async () => {
  try {
    loading.value = true;
    const response = await getUserDetail(userId.value);
    userInfo.value = response.data;
  } catch (error) {
    console.error("加载用户详情失败:", error);
    ElMessage.error("加载用户详情失败");
  } finally {
    loading.value = false;
  }
};

/**
 * 处理编辑
 */
const handleEdit = () => {
  router.push(`/users/edit/${userId.value}`);
};

// 组件挂载时加载数据
onMounted(() => {
  loadUserData();
});
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.user-detail {
  padding: $spacing-lg;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);

  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: $spacing-xl;
    padding-bottom: $spacing-lg;
    border-bottom: 1px solid var(--el-border-color-light);

    .header-left {
      display: flex;
      align-items: flex-start;
      gap: $spacing-md;

      .back-btn {
        margin-top: 4px;
        padding: 8px;

        &:hover {
          background-color: var(--el-fill-color-light);
        }
      }

      .title-section {
        h1 {
          margin: 0 0 $spacing-xs 0;
          font-size: $font-size-xl;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }

        p {
          margin: 0;
          font-size: $font-size-sm;
          color: var(--el-text-color-secondary);
        }
      }
    }

    .header-right {
      display: flex;
      gap: $spacing-md;
    }
  }

  .loading-container,
  .error-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 400px;
  }

  .user-content {
    display: flex;
    flex-direction: column;
    gap: $spacing-lg;

    .info-card {
      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;

        h3 {
          margin: 0;
          font-size: $font-size-lg;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
      }

      .user-basic-info {
        display: flex;
        gap: $spacing-xl;

        .avatar-section {
          flex-shrink: 0;
        }

        .info-grid {
          flex: 1;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: $spacing-lg;

          .info-item {
            display: flex;
            flex-direction: column;
            gap: $spacing-xs;

            label {
              font-size: $font-size-sm;
              font-weight: 500;
              color: var(--el-text-color-secondary);
            }

            span {
              font-size: $font-size-base;
              color: var(--el-text-color-primary);
            }
          }
        }
      }

      .activity-section {
        min-height: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .user-detail {
    padding: $spacing-md;

    .page-header {
      flex-direction: column;
      gap: $spacing-md;

      .header-left {
        flex-direction: column;
        gap: $spacing-sm;
      }

      .header-right {
        width: 100%;
        justify-content: center;
      }
    }

    .user-content {
      .info-card {
        .user-basic-info {
          flex-direction: column;
          text-align: center;

          .info-grid {
            grid-template-columns: 1fr;
          }
        }
      }
    }
  }
}
</style>
