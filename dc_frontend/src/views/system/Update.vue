<template>
  <div class="update-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Upgrade /></el-icon>
        系统更新
      </h1>
      <p class="page-description">管理系统版本更新和补丁安装</p>
    </div>

    <!-- 当前版本信息 -->
    <div class="current-version-section">
      <el-card class="version-card">
        <template #header>
          <div class="card-header">
            <span>当前版本信息</span>
            <el-button @click="checkForUpdates">
              <el-icon><Refresh /></el-icon>
              检查更新
            </el-button>
          </div>
        </template>

        <div class="version-info">
          <el-row :gutter="20">
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">系统版本</div>
                <div class="info-value">{{ currentVersion.version }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">构建日期</div>
                <div class="info-value">{{ currentVersion.buildDate }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">构建号</div>
                <div class="info-value">{{ currentVersion.buildNumber }}</div>
              </div>
            </el-col>
          </el-row>

          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">更新渠道</div>
                <div class="info-value">
                  <el-tag :type="getChannelTagType(currentVersion.channel)">{{
                    getChannelLabel(currentVersion.channel)
                  }}</el-tag>
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">最后检查</div>
                <div class="info-value">
                  {{ formatDate(currentVersion.lastCheck) }}
                </div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">系统状态</div>
                <div class="info-value">
                  <el-tag type="success">运行正常</el-tag>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <!-- 可用更新 -->
    <div v-if="availableUpdates.length > 0" class="available-updates-section">
      <el-card class="updates-card">
        <template #header>
          <div class="card-header">
            <span>可用更新 ({{ availableUpdates.length }})</span>
            <el-button
              type="primary"
              :disabled="isUpdating"
              @click="installAllUpdates"
            >
              <el-icon><Download /></el-icon>
              安装所有更新
            </el-button>
          </div>
        </template>

        <div class="updates-list">
          <div
            v-for="update in availableUpdates"
            :key="update.id"
            class="update-item"
          >
            <div class="update-header">
              <div class="update-title">
                <h4>{{ update.title }}</h4>
                <div class="update-meta">
                  <el-tag :type="getUpdateTypeTag(update.type)" size="small">{{
                    getUpdateTypeLabel(update.type)
                  }}</el-tag>
                  <el-tag type="info" size="small">{{ update.version }}</el-tag>
                  <span class="update-size">{{
                    formatFileSize(update.size)
                  }}</span>
                </div>
              </div>
              <div class="update-actions">
                <el-button
                  type="primary"
                  size="small"
                  :disabled="isUpdating"
                  @click="installUpdate(update)"
                >
                  <el-icon><Download /></el-icon>
                  安装
                </el-button>
                <el-button size="small" @click="viewUpdateDetails(update)">
                  <el-icon><View /></el-icon>
                  详情
                </el-button>
              </div>
            </div>

            <div class="update-description">
              {{ update.description }}
            </div>

            <div
              v-if="update.features && update.features.length > 0"
              class="update-features"
            >
              <h5>主要更新内容：</h5>
              <ul>
                <li v-for="feature in update.features" :key="feature">
                  {{ feature }}
                </li>
              </ul>
            </div>

            <div v-if="update.isInstalling" class="update-progress">
              <el-progress
                :percentage="update.progress"
                :status="update.progress === 100 ? 'success' : undefined"
              >
                <template #default="{ percentage }">
                  <span class="progress-text"
                    >{{ percentage }}% - {{ update.progressText }}</span
                  >
                </template>
              </el-progress>
            </div>
          </div>
        </div>
      </el-card>
    </div>

    <!-- 更新设置 -->
    <div class="update-settings-section">
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>更新设置</span>
            <el-button @click="saveUpdateSettings">
              <el-icon><Check /></el-icon>
              保存设置
            </el-button>
          </div>
        </template>

        <div class="settings-form">
          <el-form :model="updateSettings" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="自动更新">
                  <el-switch
                    v-model="updateSettings.autoUpdate"
                    active-text="启用"
                    inactive-text="禁用"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="更新渠道">
                  <el-select
                    v-model="updateSettings.channel"
                    style="width: 100%"
                  >
                    <el-option label="稳定版" value="stable" />
                    <el-option label="测试版" value="beta" />
                    <el-option label="开发版" value="dev" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="检查频率">
                  <el-select
                    v-model="updateSettings.checkFrequency"
                    style="width: 100%"
                  >
                    <el-option label="每小时" value="hourly" />
                    <el-option label="每天" value="daily" />
                    <el-option label="每周" value="weekly" />
                    <el-option label="手动" value="manual" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="安装时间">
                  <el-time-picker
                    v-model="updateSettings.installTime"
                    format="HH:mm"
                    value-format="HH:mm"
                    style="width: 100%"
                    :disabled="!updateSettings.autoUpdate"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="下载限速">
                  <el-input-number
                    v-model="updateSettings.downloadLimit"
                    :min="0"
                    :max="1000"
                    style="width: 100%"
                  />
                  <span
                    style="
                      margin-left: 8px;
                      color: var(--el-text-color-secondary);
                    "
                    >MB/s (0为不限速)</span
                  >
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="备份设置">
                  <el-checkbox v-model="updateSettings.createBackup">
                    更新前自动备份
                  </el-checkbox>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="通知设置">
              <el-checkbox-group v-model="updateSettings.notifications">
                <el-checkbox label="email">邮件通知</el-checkbox>
                <el-checkbox label="system">系统通知</el-checkbox>
                <el-checkbox label="log">日志记录</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>
      </el-card>
    </div>

    <!-- 更新历史 -->
    <div class="update-history-section">
      <el-card class="history-card">
        <template #header>
          <div class="card-header">
            <span>更新历史</span>
            <el-button @click="refreshUpdateHistory">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
        </template>

        <el-table
          v-loading="historyLoading"
          :data="updateHistory"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="version" label="版本" width="120" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getUpdateTypeTag(row.type)" size="small">
                {{ getUpdateTypeLabel(row.type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="title" label="标题" min-width="200" />
          <el-table-column
            prop="installDate"
            label="安装时间"
            width="180"
            sortable
          >
            <template #default="{ row }">
              {{ formatDate(row.installDate) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="size" label="大小" width="100">
            <template #default="{ row }">
              {{ formatFileSize(row.size) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                @click="viewUpdateDetails(row)"
              >
                <el-icon><View /></el-icon>
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 更新详情对话框 -->
    <el-dialog
      v-model="updateDetailVisible"
      :title="selectedUpdate?.title || '更新详情'"
      width="800px"
      top="5vh"
    >
      <div v-if="selectedUpdate" class="update-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="版本">
            {{ selectedUpdate.version }}
          </el-descriptions-item>
          <el-descriptions-item label="类型">
            <el-tag :type="getUpdateTypeTag(selectedUpdate.type)">
              {{ getUpdateTypeLabel(selectedUpdate.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="大小">
            {{ formatFileSize(selectedUpdate.size) }}
          </el-descriptions-item>
          <el-descriptions-item label="发布日期">
            {{
              formatDate(
                selectedUpdate.releaseDate || selectedUpdate.installDate,
              )
            }}
          </el-descriptions-item>
          <el-descriptions-item label="描述" span="2">
            {{ selectedUpdate.description }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedUpdate.changelog" class="update-changelog">
          <h4>更新日志</h4>
          <div
            class="changelog-content"
            v-html="selectedUpdate.changelog"
          ></div>
        </div>

        <div
          v-if="selectedUpdate.features && selectedUpdate.features.length > 0"
          class="update-features"
        >
          <h4>主要功能</h4>
          <ul>
            <li v-for="feature in selectedUpdate.features" :key="feature">
              {{ feature }}
            </li>
          </ul>
        </div>

        <div v-if="selectedUpdate.requirements" class="update-requirements">
          <h4>系统要求</h4>
          <el-descriptions :column="1" size="small">
            <el-descriptions-item
              v-if="selectedUpdate.requirements.minVersion"
              label="最低版本"
            >
              {{ selectedUpdate.requirements.minVersion }}
            </el-descriptions-item>
            <el-descriptions-item
              v-if="selectedUpdate.requirements.diskSpace"
              label="磁盘空间"
            >
              {{ formatFileSize(selectedUpdate.requirements.diskSpace) }}
            </el-descriptions-item>
            <el-descriptions-item
              v-if="selectedUpdate.requirements.memory"
              label="内存要求"
            >
              {{ formatFileSize(selectedUpdate.requirements.memory) }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="updateDetailVisible = false">关闭</el-button>
          <el-button
            v-if="selectedUpdate && !selectedUpdate.installDate"
            type="primary"
            :disabled="isUpdating"
            @click="installUpdate(selectedUpdate)"
          >
            <el-icon><Download /></el-icon>
            安装更新
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

// 响应式数据
const isUpdating = ref(false);
const historyLoading = ref(false);
const updateDetailVisible = ref(false);
const selectedUpdate = ref<any>(null);

// 当前版本信息
const currentVersion = ref({
  version: "v2.1.3",
  buildDate: "2024-01-15",
  buildNumber: "20240115001",
  channel: "stable",
  lastCheck: "2024-01-15 14:30:00",
});

// 可用更新
const availableUpdates = ref([
  {
    id: 1,
    title: "数据中心系统 v2.2.0",
    version: "v2.2.0",
    type: "major",
    size: 157286400, // 150MB
    description: "重大版本更新，包含新的数据分析功能和性能优化",
    releaseDate: "2024-01-20",
    features: [
      "新增实时数据分析仪表板",
      "优化数据查询性能，提升50%查询速度",
      "新增数据导出功能支持更多格式",
      "改进用户界面和用户体验",
      "修复已知安全漏洞",
    ],
    changelog:
      "<p><strong>新功能：</strong></p><ul><li>实时数据分析仪表板</li><li>高级数据筛选器</li></ul><p><strong>改进：</strong></p><ul><li>查询性能优化</li><li>界面响应速度提升</li></ul>",
    requirements: {
      minVersion: "v2.0.0",
      diskSpace: 524288000, // 500MB
      memory: 2147483648, // 2GB
    },
    isInstalling: false,
    progress: 0,
    progressText: "",
  },
  {
    id: 2,
    title: "安全补丁 SP-2024-001",
    version: "v2.1.4",
    type: "security",
    size: 25165824, // 24MB
    description: "重要安全补丁，修复多个安全漏洞",
    releaseDate: "2024-01-18",
    features: [
      "修复SQL注入漏洞",
      "加强用户认证安全",
      "更新第三方依赖库",
      "改进日志记录机制",
    ],
    isInstalling: false,
    progress: 0,
    progressText: "",
  },
]);

// 更新设置
const updateSettings = ref({
  autoUpdate: true,
  channel: "stable",
  checkFrequency: "daily",
  installTime: "02:00",
  downloadLimit: 0,
  createBackup: true,
  notifications: ["system", "log"],
});

// 更新历史
const updateHistory = ref([
  {
    id: 1,
    version: "v2.1.3",
    type: "patch",
    title: "系统补丁 v2.1.3",
    installDate: "2024-01-15 02:00:00",
    status: "success",
    size: 15728640, // 15MB
  },
  {
    id: 2,
    version: "v2.1.2",
    type: "minor",
    title: "功能更新 v2.1.2",
    installDate: "2024-01-10 02:00:00",
    status: "success",
    size: 52428800, // 50MB
  },
  {
    id: 3,
    version: "v2.1.1",
    type: "patch",
    title: "错误修复 v2.1.1",
    installDate: "2024-01-05 02:00:00",
    status: "success",
    size: 10485760, // 10MB
  },
  {
    id: 4,
    version: "v2.1.0",
    type: "major",
    title: "主要版本更新 v2.1.0",
    installDate: "2024-01-01 02:00:00",
    status: "success",
    size: 209715200, // 200MB
  },
  {
    id: 5,
    version: "v2.0.5",
    type: "security",
    title: "安全补丁 v2.0.5",
    installDate: "2023-12-25 02:00:00",
    status: "failed",
    size: 31457280, // 30MB
  },
]);

/**
 * 获取渠道标签类型
 */
const getChannelTagType = (channel: string) => {
  const tagMap: Record<string, string> = {
    stable: "success",
    beta: "warning",
    dev: "danger",
  };
  return tagMap[channel] || "info";
};

/**
 * 获取渠道标签文本
 */
const getChannelLabel = (channel: string) => {
  const labelMap: Record<string, string> = {
    stable: "稳定版",
    beta: "测试版",
    dev: "开发版",
  };
  return labelMap[channel] || channel;
};

/**
 * 获取更新类型标签
 */
const getUpdateTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    major: "primary",
    minor: "success",
    patch: "info",
    security: "danger",
  };
  return tagMap[type] || "info";
};

/**
 * 获取更新类型标签文本
 */
const getUpdateTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    major: "主要版本",
    minor: "功能更新",
    patch: "补丁",
    security: "安全更新",
  };
  return labelMap[type] || type;
};

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string) => {
  const tagMap: Record<string, string> = {
    success: "success",
    failed: "danger",
    installing: "warning",
  };
  return tagMap[status] || "info";
};

/**
 * 获取状态标签文本
 */
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    success: "成功",
    failed: "失败",
    installing: "安装中",
  };
  return labelMap[status] || status;
};

/**
 * 格式化文件大小
 */
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return "0 B";

  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
};

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

/**
 * 检查更新
 */
const checkForUpdates = () => {
  ElMessage.info("正在检查更新...");

  // 模拟检查更新
  setTimeout(() => {
    currentVersion.value.lastCheck = new Date()
      .toISOString()
      .replace("T", " ")
      .substring(0, 19);
    ElMessage.success(
      `检查完成，发现 ${availableUpdates.value.length} 个可用更新`,
    );
  }, 2000);
};

/**
 * 安装更新
 */
const installUpdate = (update: any) => {
  if (isUpdating.value) {
    ElMessage.warning("已有更新正在进行中");
    return;
  }

  ElMessageBox.confirm(`确定要安装更新 "${update.title}" 吗？`, "确认安装", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "info",
  })
    .then(() => {
      startUpdateInstallation(update);
    })
    .catch(() => {
      // 用户取消
    });
};

/**
 * 开始安装更新
 */
const startUpdateInstallation = (update: any) => {
  isUpdating.value = true;
  update.isInstalling = true;
  update.progress = 0;
  update.progressText = "准备下载...";

  ElMessage.info(`开始安装更新: ${update.title}`);

  // 模拟安装过程
  const installTimer = setInterval(() => {
    update.progress += Math.random() * 10;

    if (update.progress < 30) {
      update.progressText = "正在下载...";
    } else if (update.progress < 60) {
      update.progressText = "正在验证...";
    } else if (update.progress < 90) {
      update.progressText = "正在安装...";
    } else {
      update.progressText = "正在完成...";
    }

    if (update.progress >= 100) {
      clearInterval(installTimer);
      update.progress = 100;
      update.progressText = "安装完成";

      setTimeout(() => {
        // 移除已安装的更新
        const index = availableUpdates.value.findIndex(
          (u) => u.id === update.id,
        );
        if (index > -1) {
          availableUpdates.value.splice(index, 1);
        }

        // 添加到历史记录
        updateHistory.value.unshift({
          id: Date.now(),
          version: update.version,
          type: update.type,
          title: update.title,
          installDate: new Date()
            .toISOString()
            .replace("T", " ")
            .substring(0, 19),
          status: "success",
          size: update.size,
        });

        // 更新当前版本
        if (update.type === "major" || update.type === "minor") {
          currentVersion.value.version = update.version;
          currentVersion.value.buildDate = new Date()
            .toISOString()
            .substring(0, 10);
          currentVersion.value.buildNumber = new Date()
            .toISOString()
            .replace(/[-:T]/g, "")
            .substring(0, 14);
        }

        isUpdating.value = false;
        ElMessage.success(`更新 "${update.title}" 安装完成`);

        if (updateDetailVisible.value) {
          updateDetailVisible.value = false;
        }
      }, 1000);
    }
  }, 200);
};

/**
 * 安装所有更新
 */
const installAllUpdates = () => {
  if (isUpdating.value) {
    ElMessage.warning("已有更新正在进行中");
    return;
  }

  ElMessageBox.confirm(
    `确定要安装所有 ${availableUpdates.value.length} 个更新吗？`,
    "确认安装",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "info",
    },
  )
    .then(() => {
      // 按优先级排序（安全更新优先）
      const sortedUpdates = [...availableUpdates.value].sort((a, b) => {
        const priority = { security: 0, major: 1, minor: 2, patch: 3 };
        return priority[a.type] - priority[b.type];
      });

      installUpdatesSequentially(sortedUpdates, 0);
    })
    .catch(() => {
      // 用户取消
    });
};

/**
 * 顺序安装更新
 */
const installUpdatesSequentially = (updates: any[], index: number) => {
  if (index >= updates.length) {
    ElMessage.success("所有更新安装完成");
    return;
  }

  const update = updates[index];
  startUpdateInstallation(update);

  // 等待当前更新完成后安装下一个
  const checkTimer = setInterval(() => {
    if (!update.isInstalling) {
      clearInterval(checkTimer);
      setTimeout(() => {
        installUpdatesSequentially(updates, index + 1);
      }, 1000);
    }
  }, 500);
};

/**
 * 查看更新详情
 */
const viewUpdateDetails = (update: any) => {
  selectedUpdate.value = update;
  updateDetailVisible.value = true;
};

/**
 * 保存更新设置
 */
const saveUpdateSettings = () => {
  ElMessage.success("更新设置已保存");
};

/**
 * 刷新更新历史
 */
const refreshUpdateHistory = () => {
  historyLoading.value = true;

  setTimeout(() => {
    historyLoading.value = false;
    ElMessage.success("更新历史已刷新");
  }, 1000);
};

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  // 初始化时检查更新
  setTimeout(() => {
    checkForUpdates();
  }, 1000);
});
</script>

<style lang="scss" scoped>
.update-container {
  padding: 20px;
  background: var(--el-bg-color-page);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 24px;

  .page-title {
    display: flex;
    align-items: center;
    font-size: 24px;
    font-weight: 600;
    color: var(--el-text-color-primary);
    margin: 0 0 8px 0;

    .el-icon {
      margin-right: 8px;
      color: var(--el-color-primary);
    }
  }

  .page-description {
    color: var(--el-text-color-secondary);
    margin: 0;
  }
}

.current-version-section,
.available-updates-section,
.update-settings-section,
.update-history-section {
  margin-bottom: 20px;
}

.version-card,
.updates-card,
.settings-card,
.history-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}

.version-info {
  .info-item {
    .info-label {
      font-size: 14px;
      color: var(--el-text-color-secondary);
      margin-bottom: 4px;
    }

    .info-value {
      font-size: 16px;
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }
}

.updates-list {
  .update-item {
    padding: 20px;
    border: 1px solid var(--el-border-color-light);
    border-radius: 8px;
    margin-bottom: 16px;
    background: var(--el-bg-color-page);

    &:last-child {
      margin-bottom: 0;
    }

    .update-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 12px;

      .update-title {
        flex: 1;

        h4 {
          margin: 0 0 8px 0;
          color: var(--el-text-color-primary);
        }

        .update-meta {
          display: flex;
          align-items: center;
          gap: 8px;

          .update-size {
            font-size: 12px;
            color: var(--el-text-color-placeholder);
          }
        }
      }

      .update-actions {
        display: flex;
        gap: 8px;
      }
    }

    .update-description {
      color: var(--el-text-color-secondary);
      margin-bottom: 12px;
      line-height: 1.5;
    }

    .update-features {
      margin-bottom: 12px;

      h5 {
        margin: 0 0 8px 0;
        color: var(--el-text-color-primary);
        font-size: 14px;
      }

      ul {
        margin: 0;
        padding-left: 20px;

        li {
          color: var(--el-text-color-secondary);
          margin-bottom: 4px;
          line-height: 1.4;
        }
      }
    }

    .update-progress {
      margin-top: 16px;

      .progress-text {
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
  }
}

.settings-form {
  .el-form-item {
    margin-bottom: 16px;
  }
}

.update-detail {
  .update-changelog,
  .update-features,
  .update-requirements {
    margin-top: 20px;

    h4 {
      margin: 0 0 12px 0;
      color: var(--el-text-color-primary);
      font-size: 16px;
      font-weight: 600;
    }

    .changelog-content {
      padding: 12px;
      background: var(--el-bg-color-page);
      border-radius: 4px;
      border: 1px solid var(--el-border-color-light);

      :deep(p) {
        margin: 0 0 8px 0;
      }

      :deep(ul) {
        margin: 0;
        padding-left: 20px;
      }

      :deep(li) {
        margin-bottom: 4px;
      }
    }

    ul {
      margin: 0;
      padding-left: 20px;

      li {
        color: var(--el-text-color-secondary);
        margin-bottom: 4px;
        line-height: 1.4;
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}

// 响应式设计
@media (max-width: 1200px) {
  .version-info,
  .settings-form {
    .el-row {
      .el-col {
        margin-bottom: 16px;
      }
    }
  }
}

@media (max-width: 768px) {
  .update-container {
    padding: 16px;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch !important;
  }

  .update-header {
    flex-direction: column !important;
    align-items: stretch !important;

    .update-actions {
      justify-content: center;
      margin-top: 12px;
    }
  }

  .version-info,
  .settings-form {
    .el-col {
      span: 24 !important;
    }
  }
}
</style>
