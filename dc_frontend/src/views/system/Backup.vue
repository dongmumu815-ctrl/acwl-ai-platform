<template>
  <div class="backup-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><FolderOpened /></el-icon>
        系统备份
      </h1>
      <p class="page-description">管理系统数据备份和恢复</p>
    </div>

    <!-- 备份操作区 -->
    <div class="backup-actions">
      <el-card class="action-card">
        <template #header>
          <div class="card-header">
            <span>创建备份</span>
            <el-button type="primary" @click="createBackup">
              <el-icon><Plus /></el-icon>
              立即备份
            </el-button>
          </div>
        </template>

        <div class="backup-form">
          <el-form :model="backupForm" label-width="100px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="备份类型">
                  <el-select v-model="backupForm.type" style="width: 100%">
                    <el-option label="完整备份" value="full" />
                    <el-option label="增量备份" value="incremental" />
                    <el-option label="差异备份" value="differential" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="备份范围">
                  <el-select v-model="backupForm.scope" style="width: 100%">
                    <el-option label="全部数据" value="all" />
                    <el-option label="用户数据" value="user" />
                    <el-option label="系统配置" value="config" />
                    <el-option label="日志文件" value="logs" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item label="压缩级别">
                  <el-select
                    v-model="backupForm.compression"
                    style="width: 100%"
                  >
                    <el-option label="无压缩" value="none" />
                    <el-option label="快速压缩" value="fast" />
                    <el-option label="标准压缩" value="standard" />
                    <el-option label="最大压缩" value="max" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="备份描述">
                  <el-input
                    v-model="backupForm.description"
                    placeholder="请输入备份描述"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-card>
    </div>

    <!-- 自动备份设置 -->
    <div class="auto-backup-section">
      <el-card class="settings-card">
        <template #header>
          <div class="card-header">
            <span>自动备份设置</span>
            <el-switch
              v-model="autoBackupEnabled"
              active-text="已启用"
              inactive-text="已禁用"
              @change="toggleAutoBackup"
            />
          </div>
        </template>

        <div v-if="autoBackupEnabled" class="auto-backup-form">
          <el-form :model="autoBackupForm" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-form-item label="备份频率">
                  <el-select
                    v-model="autoBackupForm.frequency"
                    style="width: 100%"
                  >
                    <el-option label="每小时" value="hourly" />
                    <el-option label="每天" value="daily" />
                    <el-option label="每周" value="weekly" />
                    <el-option label="每月" value="monthly" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="备份时间">
                  <el-time-picker
                    v-model="autoBackupForm.time"
                    format="HH:mm"
                    value-format="HH:mm"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="保留天数">
                  <el-input-number
                    v-model="autoBackupForm.retentionDays"
                    :min="1"
                    :max="365"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-button type="primary" @click="saveAutoBackupSettings">
                保存设置
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-card>
    </div>

    <!-- 备份列表 -->
    <div class="backup-list-section">
      <el-card class="list-card">
        <template #header>
          <div class="card-header">
            <span>备份历史</span>
            <div class="header-actions">
              <el-input
                v-model="searchKeyword"
                placeholder="搜索备份..."
                style="width: 200px; margin-right: 12px"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button @click="refreshBackupList">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          v-loading="loading"
          :data="filteredBackups"
          stripe
          style="width: 100%"
        >
          <el-table-column prop="name" label="备份名称" min-width="200">
            <template #default="{ row }">
              <div class="backup-name">
                <el-icon class="backup-icon"><FolderOpened /></el-icon>
                <span>{{ row.name }}</span>
                <el-tag v-if="row.isAutoBackup" type="info" size="small"
                  >自动</el-tag
                >
              </div>
            </template>
          </el-table-column>

          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="getBackupTypeTag(row.type)" size="small">
                {{ getBackupTypeLabel(row.type) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column prop="scope" label="范围" width="100">
            <template #default="{ row }">
              <span>{{ getBackupScopeLabel(row.scope) }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="size" label="大小" width="100">
            <template #default="{ row }">
              <span>{{ formatFileSize(row.size) }}</span>
            </template>
          </el-table-column>

          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusTagType(row.status)" size="small">
                {{ getStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>

          <el-table-column
            prop="createdAt"
            label="创建时间"
            width="180"
            sortable
          >
            <template #default="{ row }">
              {{ formatDate(row.createdAt) }}
            </template>
          </el-table-column>

          <el-table-column prop="description" label="描述" min-width="150">
            <template #default="{ row }">
              <span class="description-text">{{ row.description || "-" }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button
                type="primary"
                size="small"
                :disabled="row.status !== 'completed'"
                @click="downloadBackup(row)"
              >
                <el-icon><Download /></el-icon>
                下载
              </el-button>

              <el-button
                type="warning"
                size="small"
                :disabled="row.status !== 'completed'"
                @click="restoreBackup(row)"
              >
                <el-icon><RefreshRight /></el-icon>
                恢复
              </el-button>

              <el-button type="danger" size="small" @click="deleteBackup(row)">
                <el-icon><Delete /></el-icon>
                删除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalBackups"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 恢复确认对话框 -->
    <el-dialog v-model="restoreDialogVisible" title="确认恢复" width="500px">
      <div class="restore-warning">
        <el-alert title="警告" type="warning" :closable="false" show-icon>
          <template #default>
            <p>恢复备份将会覆盖当前系统数据，此操作不可逆！</p>
            <p>
              请确认您要恢复的备份：<strong>{{ selectedBackup?.name }}</strong>
            </p>
          </template>
        </el-alert>

        <div class="restore-options" style="margin-top: 20px">
          <el-checkbox v-model="restoreOptions.createBackupBeforeRestore">
            恢复前创建当前数据备份
          </el-checkbox>
          <el-checkbox v-model="restoreOptions.restartAfterRestore">
            恢复后重启系统
          </el-checkbox>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="restoreDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmRestore">
            确认恢复
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

// 响应式数据
const loading = ref(false);
const searchKeyword = ref("");
const currentPage = ref(1);
const pageSize = ref(20);
const totalBackups = ref(0);
const autoBackupEnabled = ref(true);
const restoreDialogVisible = ref(false);
const selectedBackup = ref<any>(null);

// 备份表单
const backupForm = ref({
  type: "full",
  scope: "all",
  compression: "standard",
  description: "",
});

// 自动备份表单
const autoBackupForm = ref({
  frequency: "daily",
  time: "02:00",
  retentionDays: 30,
});

// 恢复选项
const restoreOptions = ref({
  createBackupBeforeRestore: true,
  restartAfterRestore: false,
});

// 备份列表数据
const backups = ref([
  {
    id: 1,
    name: "backup_2024_01_15_full",
    type: "full",
    scope: "all",
    size: 2147483648, // 2GB
    status: "completed",
    createdAt: "2024-01-15 02:00:00",
    description: "每日自动完整备份",
    isAutoBackup: true,
  },
  {
    id: 2,
    name: "backup_2024_01_14_incremental",
    type: "incremental",
    scope: "user",
    size: 524288000, // 500MB
    status: "completed",
    createdAt: "2024-01-14 14:30:00",
    description: "用户数据增量备份",
    isAutoBackup: false,
  },
  {
    id: 3,
    name: "backup_2024_01_14_config",
    type: "differential",
    scope: "config",
    size: 10485760, // 10MB
    status: "completed",
    createdAt: "2024-01-14 10:15:00",
    description: "系统配置备份",
    isAutoBackup: false,
  },
  {
    id: 4,
    name: "backup_2024_01_13_full",
    type: "full",
    scope: "all",
    size: 2097152000, // 2GB
    status: "failed",
    createdAt: "2024-01-13 02:00:00",
    description: "每日自动完整备份（失败）",
    isAutoBackup: true,
  },
  {
    id: 5,
    name: "backup_2024_01_12_manual",
    type: "full",
    scope: "all",
    size: 1073741824, // 1GB
    status: "in_progress",
    createdAt: "2024-01-12 16:45:00",
    description: "手动创建的完整备份",
    isAutoBackup: false,
  },
]);

/**
 * 过滤后的备份列表
 */
const filteredBackups = computed(() => {
  let filtered = backups.value;

  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    filtered = filtered.filter(
      (backup) =>
        backup.name.toLowerCase().includes(keyword) ||
        backup.description.toLowerCase().includes(keyword),
    );
  }

  return filtered.sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
  );
});

/**
 * 获取备份类型标签
 */
const getBackupTypeTag = (type: string) => {
  const tagMap: Record<string, string> = {
    full: "primary",
    incremental: "success",
    differential: "warning",
  };
  return tagMap[type] || "info";
};

/**
 * 获取备份类型标签文本
 */
const getBackupTypeLabel = (type: string) => {
  const labelMap: Record<string, string> = {
    full: "完整",
    incremental: "增量",
    differential: "差异",
  };
  return labelMap[type] || type;
};

/**
 * 获取备份范围标签文本
 */
const getBackupScopeLabel = (scope: string) => {
  const labelMap: Record<string, string> = {
    all: "全部数据",
    user: "用户数据",
    config: "系统配置",
    logs: "日志文件",
  };
  return labelMap[scope] || scope;
};

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string) => {
  const tagMap: Record<string, string> = {
    completed: "success",
    in_progress: "warning",
    failed: "danger",
  };
  return tagMap[status] || "info";
};

/**
 * 获取状态标签文本
 */
const getStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    completed: "已完成",
    in_progress: "进行中",
    failed: "失败",
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

  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

/**
 * 创建备份
 */
const createBackup = () => {
  if (!backupForm.value.description.trim()) {
    ElMessage.warning("请输入备份描述");
    return;
  }

  loading.value = true;

  // 模拟创建备份
  setTimeout(() => {
    const newBackup = {
      id: Date.now(),
      name: `backup_${new Date().toISOString().slice(0, 10).replace(/-/g, "_")}_${backupForm.value.type}`,
      type: backupForm.value.type,
      scope: backupForm.value.scope,
      size: Math.floor(Math.random() * 2000000000) + 100000000, // 随机大小
      status: "in_progress",
      createdAt: new Date().toISOString().replace("T", " ").substring(0, 19),
      description: backupForm.value.description,
      isAutoBackup: false,
    };

    backups.value.unshift(newBackup);
    loading.value = false;

    ElMessage.success("备份任务已创建，正在后台执行");

    // 模拟备份完成
    setTimeout(() => {
      newBackup.status = "completed";
      ElMessage.success(`备份 "${newBackup.name}" 已完成`);
    }, 5000);

    // 重置表单
    backupForm.value.description = "";
  }, 1000);
};

/**
 * 切换自动备份
 */
const toggleAutoBackup = (enabled: boolean) => {
  if (enabled) {
    ElMessage.success("自动备份已启用");
  } else {
    ElMessage.info("自动备份已禁用");
  }
};

/**
 * 保存自动备份设置
 */
const saveAutoBackupSettings = () => {
  ElMessage.success("自动备份设置已保存");
};

/**
 * 刷新备份列表
 */
const refreshBackupList = () => {
  loading.value = true;

  setTimeout(() => {
    loading.value = false;
    ElMessage.success("备份列表已刷新");
  }, 1000);
};

/**
 * 下载备份
 */
const downloadBackup = (backup: any) => {
  ElMessage.info(`开始下载备份: ${backup.name}`);

  // 模拟下载
  setTimeout(() => {
    ElMessage.success("备份文件下载完成");
  }, 2000);
};

/**
 * 恢复备份
 */
const restoreBackup = (backup: any) => {
  selectedBackup.value = backup;
  restoreDialogVisible.value = true;
};

/**
 * 确认恢复
 */
const confirmRestore = () => {
  if (!selectedBackup.value) return;

  restoreDialogVisible.value = false;
  loading.value = true;

  ElMessage.info(`开始恢复备份: ${selectedBackup.value.name}`);

  // 模拟恢复过程
  setTimeout(() => {
    loading.value = false;
    ElMessage.success("备份恢复完成");

    if (restoreOptions.value.restartAfterRestore) {
      ElMessage.warning("系统将在5秒后重启");
    }
  }, 3000);
};

/**
 * 删除备份
 */
const deleteBackup = (backup: any) => {
  ElMessageBox.confirm(
    `确定要删除备份 "${backup.name}" 吗？此操作不可恢复！`,
    "确认删除",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    },
  )
    .then(() => {
      const index = backups.value.findIndex((b) => b.id === backup.id);
      if (index > -1) {
        backups.value.splice(index, 1);
        ElMessage.success("备份已删除");
      }
    })
    .catch(() => {
      // 用户取消删除
    });
};

/**
 * 处理页面大小变化
 */
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  currentPage.value = 1;
};

/**
 * 处理当前页变化
 */
const handleCurrentChange = (page: number) => {
  currentPage.value = page;
};

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  totalBackups.value = backups.value.length;
});
</script>

<style lang="scss" scoped>
.backup-container {
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

.backup-actions,
.auto-backup-section,
.backup-list-section {
  margin-bottom: 20px;
}

.action-card,
.settings-card,
.list-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .header-actions {
      display: flex;
      align-items: center;
    }
  }
}

.backup-form,
.auto-backup-form {
  .el-form-item {
    margin-bottom: 16px;
  }
}

.backup-name {
  display: flex;
  align-items: center;
  gap: 8px;

  .backup-icon {
    color: var(--el-color-primary);
  }
}

.description-text {
  color: var(--el-text-color-secondary);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
}

.restore-warning {
  .restore-options {
    .el-checkbox {
      display: block;
      margin-bottom: 8px;
    }
  }
}

.dialog-footer {
  text-align: right;
}

// 响应式设计
@media (max-width: 1200px) {
  .backup-form,
  .auto-backup-form {
    .el-row {
      .el-col {
        margin-bottom: 16px;
      }
    }
  }
}

@media (max-width: 768px) {
  .backup-container {
    padding: 16px;
  }

  .card-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch !important;

    .header-actions {
      justify-content: center;
    }
  }

  .backup-form,
  .auto-backup-form {
    .el-col {
      span: 24 !important;
    }
  }
}
</style>
