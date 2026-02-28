<template>
  <div class="user-detail">
    <!-- 用户基本信息 -->
    <div class="detail-section">
      <h3 class="section-title">基本信息</h3>
      <div class="user-profile">
        <div class="avatar-section">
          <el-avatar :src="user.avatar" :alt="user.full_name" :size="80">
            {{ user.full_name?.charAt(0) }}
          </el-avatar>
          <div class="status-badge">
            <el-tag :type="user.is_active ? 'success' : 'danger'">
              {{ user.is_active ? "启用" : "禁用" }}
            </el-tag>
          </div>
        </div>
        <div class="profile-info">
          <div class="info-grid">
            <div class="info-item">
              <span class="label">用户名：</span>
              <span class="value">{{ user.username }}</span>
            </div>
            <div class="info-item">
              <span class="label">姓名：</span>
              <span class="value">{{ user.full_name }}</span>
            </div>
            <div class="info-item">
              <span class="label">邮箱：</span>
              <span class="value">{{ user.email }}</span>
            </div>
            <div class="info-item">
              <span class="label">手机：</span>
              <span class="value">{{ user.phone || "-" }}</span>
            </div>
            <div class="info-item">
              <span class="label">部门：</span>
              <span class="value">{{ user.department || "-" }}</span>
            </div>
            <div class="info-item">
              <span class="label">职位：</span>
              <span class="value">{{ user.position || "-" }}</span>
            </div>
            <div class="info-item">
              <span class="label">超级管理员：</span>
              <span class="value">
                <el-tag :type="user.is_superuser ? 'warning' : 'info'">
                  {{ user.is_superuser ? "是" : "否" }}
                </el-tag>
              </span>
            </div>
            <div class="info-item">
              <span class="label">创建时间：</span>
              <span class="value">{{ formatDateTime(user.created_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">更新时间：</span>
              <span class="value">{{ formatDateTime(user.updated_at) }}</span>
            </div>
            <div class="info-item">
              <span class="label">最后登录：</span>
              <span class="value">{{ formatDateTime(user.last_login) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 角色信息 -->
    <div v-if="userDetail?.roles?.length" class="detail-section">
      <h3 class="section-title">角色信息</h3>
      <div class="roles-list">
        <el-tag
          v-for="role in userDetail.roles"
          :key="role.id"
          type="primary"
          class="role-tag"
        >
          {{ role.name }}
        </el-tag>
      </div>
    </div>

    <!-- 权限信息 -->
    <div v-if="userDetail?.permissions?.length" class="detail-section">
      <h3 class="section-title">权限信息</h3>
      <div class="permissions-grid">
        <div
          v-for="permission in userDetail.permissions"
          :key="permission.id"
          class="permission-item"
        >
          <div class="permission-name">{{ permission.name }}</div>
          <div class="permission-code">{{ permission.code }}</div>
          <div v-if="permission.description" class="permission-desc">
            {{ permission.description }}
          </div>
        </div>
      </div>
    </div>

    <!-- 统计信息 -->
    <div v-if="userStats" class="detail-section">
      <h3 class="section-title">统计信息</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <div class="stat-value">{{ userStats.total_logins }}</div>
          <div class="stat-label">总登录次数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ userStats.resources_created }}</div>
          <div class="stat-label">创建资源数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ userStats.resources_accessed }}</div>
          <div class="stat-label">访问资源数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ userStats.queries_executed }}</div>
          <div class="stat-label">执行查询数</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">{{ userStats.favorites_count }}</div>
          <div class="stat-label">收藏数量</div>
        </div>
      </div>
    </div>

    <!-- 会话信息 -->
    <div v-if="userSessions?.length" class="detail-section">
      <h3 class="section-title">活跃会话</h3>
      <el-table :data="userSessions" stripe>
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="user_agent" label="用户代理" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.user_agent" placement="top">
              <span class="user-agent-text">{{
                formatUserAgent(row.user_agent)
              }}</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="last_activity" label="最后活动" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.last_activity) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_current" label="当前会话" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_current ? 'success' : 'info'">
              {{ row.is_current ? "是" : "否" }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_current"
              type="danger"
              size="small"
              @click="handleTerminateSession(row)"
            >
              终止
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 最近活动 -->
    <div v-if="userActivities?.length" class="detail-section">
      <h3 class="section-title">最近活动</h3>
      <div class="activities-list">
        <div
          v-for="activity in userActivities"
          :key="activity.id"
          class="activity-item"
        >
          <div class="activity-time">
            {{ formatDateTime(activity.created_at) }}
          </div>
          <div class="activity-content">
            <div class="activity-action">{{ activity.action }}</div>
            <div class="activity-description">{{ activity.description }}</div>
            <div class="activity-meta">
              <span>{{ activity.resource_type }}</span>
              <span v-if="activity.resource_id"
                >ID: {{ activity.resource_id }}</span
              >
              <span>{{ activity.ip_address }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="detail-actions">
      <el-button type="primary" @click="handleEdit">
        <el-icon><Edit /></el-icon>
        编辑用户
      </el-button>
      <el-button @click="handleResetPassword">
        <el-icon><Key /></el-icon>
        重置密码
      </el-button>
      <el-button
        :type="user.is_active ? 'warning' : 'success'"
        @click="handleToggleStatus"
      >
        <el-icon><Switch /></el-icon>
        {{ user.is_active ? "禁用" : "启用" }}用户
      </el-button>
      <el-button @click="$emit('close')"> 关闭 </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Edit, Key, Switch } from "@element-plus/icons-vue";
import type {
  User,
  UserDetail as UserDetailType,
  UserStats,
  UserSession,
  UserActivity,
} from "@/types/user";
import {
  getUserDetail,
  getUserStats,
  getUserSessions,
  getUserActivities,
  updateUserStatus,
  resetUserPassword,
  terminateUserSession,
} from "@/api/user";
import { formatDateTime } from "@/utils/format";

interface Props {
  user: User;
}

const props = defineProps<Props>();
const emit = defineEmits<{
  close: [];
}>();

const router = useRouter();

// 响应式数据
const loading = ref(false);
const userDetail = ref<UserDetailType | null>(null);
const userStats = ref<UserStats | null>(null);
const userSessions = ref<UserSession[]>([]);
const userActivities = ref<UserActivity[]>([]);

/**
 * 加载用户详细信息
 */
const loadUserDetail = async () => {
  try {
    loading.value = true;
    const [detailRes, statsRes, sessionsRes, activitiesRes] = await Promise.all(
      [
        getUserDetail(props.user.id),
        getUserStats(props.user.id),
        getUserSessions(props.user.id),
        getUserActivities(props.user.id, { page: 1, page_size: 10 }),
      ],
    );

    userDetail.value = detailRes.data;
    userStats.value = statsRes.data;
    userSessions.value = sessionsRes.data;
    userActivities.value = activitiesRes.data.items;
  } catch (error) {
    ElMessage.error("加载用户详情失败");
  } finally {
    loading.value = false;
  }
};

/**
 * 格式化用户代理字符串
 */
const formatUserAgent = (userAgent: string): string => {
  if (userAgent.includes("Chrome")) {
    return "Chrome";
  } else if (userAgent.includes("Firefox")) {
    return "Firefox";
  } else if (userAgent.includes("Safari")) {
    return "Safari";
  } else if (userAgent.includes("Edge")) {
    return "Edge";
  }
  return "未知浏览器";
};

/**
 * 处理编辑用户
 */
const handleEdit = () => {
  router.push(`/user/edit/${props.user.id}`);
  emit("close");
};

/**
 * 处理重置密码
 */
const handleResetPassword = async () => {
  try {
    await ElMessageBox.confirm(
      "确定要重置该用户的密码吗？新密码将通过邮件发送给用户。",
      "重置密码",
      {
        type: "warning",
      },
    );

    await resetUserPassword(props.user.id);
    ElMessage.success("密码重置成功，新密码已发送到用户邮箱");
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("密码重置失败");
    }
  }
};

/**
 * 处理切换用户状态
 */
const handleToggleStatus = async () => {
  try {
    const action = props.user.is_active ? "禁用" : "启用";
    await ElMessageBox.confirm(`确定要${action}该用户吗？`, `${action}用户`, {
      type: "warning",
    });

    await updateUserStatus(props.user.id, !props.user.is_active);
    ElMessage.success(`用户${action}成功`);
    // 更新本地状态
    props.user.is_active = !props.user.is_active;
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("操作失败");
    }
  }
};

/**
 * 处理终止会话
 */
const handleTerminateSession = async (session: UserSession) => {
  try {
    await ElMessageBox.confirm("确定要终止该会话吗？", "终止会话", {
      type: "warning",
    });

    await terminateUserSession(session.id);
    ElMessage.success("会话终止成功");
    // 重新加载会话列表
    const sessionsRes = await getUserSessions(props.user.id);
    userSessions.value = sessionsRes.data;
  } catch (error) {
    if (error !== "cancel") {
      ElMessage.error("终止会话失败");
    }
  }
};

// 组件挂载时加载数据
onMounted(() => {
  loadUserDetail();
});
</script>

<style lang="scss" scoped>
@use "@/styles/variables.scss" as *;

.user-detail {
  .detail-section {
    margin-bottom: $spacing-xl;

    .section-title {
      margin: 0 0 $spacing-lg 0;
      font-size: $font-size-lg;
      font-weight: 600;
      color: var(--el-text-color-primary);
      border-bottom: 2px solid var(--el-color-primary);
      padding-bottom: $spacing-xs;
    }
  }

  .user-profile {
    display: flex;
    gap: $spacing-xl;
    align-items: flex-start;

    .avatar-section {
      position: relative;
      text-align: center;

      .status-badge {
        margin-top: $spacing-sm;
      }
    }

    .profile-info {
      flex: 1;

      .info-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: $spacing-md;

        .info-item {
          display: flex;
          align-items: center;

          .label {
            width: 100px;
            font-weight: 500;
            color: var(--el-text-color-regular);
          }

          .value {
            flex: 1;
            color: var(--el-text-color-primary);
          }
        }
      }
    }
  }

  .roles-list {
    display: flex;
    flex-wrap: wrap;
    gap: $spacing-sm;

    .role-tag {
      font-size: $font-size-sm;
    }
  }

  .permissions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: $spacing-md;

    .permission-item {
      padding: $spacing-md;
      border: 1px solid var(--el-border-color-light);
      border-radius: $border-radius-base;
      background-color: var(--el-bg-color);

      .permission-name {
        font-weight: 600;
        color: var(--el-text-color-primary);
        margin-bottom: $spacing-xs;
      }

      .permission-code {
        font-family: $font-family-mono;
        font-size: $font-size-sm;
        color: var(--el-color-primary);
        margin-bottom: $spacing-xs;
      }

      .permission-desc {
        font-size: $font-size-sm;
        color: var(--el-text-color-regular);
      }
    }
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: $spacing-lg;

    .stat-item {
      text-align: center;
      padding: $spacing-lg;
      border: 1px solid var(--el-border-color-light);
      border-radius: $border-radius-base;
      background-color: var(--el-bg-color);

      .stat-value {
        font-size: $font-size-xxl;
        font-weight: 600;
        color: var(--el-color-primary);
        margin-bottom: $spacing-xs;
      }

      .stat-label {
        font-size: $font-size-sm;
        color: var(--el-text-color-regular);
      }
    }
  }

  .activities-list {
    .activity-item {
      display: flex;
      gap: $spacing-md;
      padding: $spacing-md;
      border-bottom: 1px solid var(--el-border-color-lighter);

      &:last-child {
        border-bottom: none;
      }

      .activity-time {
        width: 140px;
        font-size: $font-size-sm;
        color: var(--el-text-color-regular);
        flex-shrink: 0;
      }

      .activity-content {
        flex: 1;

        .activity-action {
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: $spacing-xs;
        }

        .activity-description {
          color: var(--el-text-color-regular);
          margin-bottom: $spacing-xs;
        }

        .activity-meta {
          display: flex;
          gap: $spacing-md;
          font-size: $font-size-sm;
          color: var(--el-text-color-secondary);
        }
      }
    }
  }

  .user-agent-text {
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    display: inline-block;
  }

  .detail-actions {
    display: flex;
    gap: $spacing-md;
    justify-content: center;
    padding-top: $spacing-xl;
    border-top: 1px solid var(--el-border-color-lighter);
  }
}

// 响应式设计
@media (max-width: 768px) {
  .user-detail {
    .user-profile {
      flex-direction: column;
      text-align: center;

      .profile-info {
        .info-grid {
          grid-template-columns: 1fr;
        }
      }
    }

    .permissions-grid {
      grid-template-columns: 1fr;
    }

    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }

    .detail-actions {
      flex-direction: column;
    }
  }
}

// 暗色主题适配
@media (prefers-color-scheme: dark) {
  .user-detail {
    .permission-item,
    .stat-item {
      background-color: var(--el-bg-color);
      border-color: var(--el-border-color);
    }
  }
}
</style>
