<template>
  <div class="batch-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <el-button size="small" @click="goBack">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <div class="title-section">
            <h1 class="page-title">
              <el-icon><DataBoard /></el-icon>
              批次详情
            </h1>
            <p v-if="batchInfo" class="page-description">
              {{ batchInfo.batch_name }}
            </p>
          </div>
        </div>
        <div class="header-right">
          <el-button
            v-if="batchInfo?.status === 'pending'"
            type="success"
            @click="startProcessing"
          >
            <el-icon><VideoPlay /></el-icon>
            开始处理
          </el-button>
          <el-button
            v-if="batchInfo?.status === 'processing'"
            type="warning"
            @click="stopProcessing"
          >
            <el-icon><VideoPause /></el-icon>
            停止处理
          </el-button>
          <el-button
            v-if="
              batchInfo?.status === 'completed' && batchInfo?.result_file_path
            "
            type="info"
            @click="downloadResult"
          >
            <el-icon><Download /></el-icon>
            下载结果
          </el-button>
          <el-button @click="loadBatchInfo">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 批次基本信息 -->
    <div v-if="batchInfo" class="page-card">
      <div class="card-header">
        <h3>基本信息</h3>
      </div>
      <div class="batch-info">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="info-item">
              <span class="label">批次ID:</span>
              <span class="value">{{ batchInfo.id }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">批次名称:</span>
              <span class="value">{{ batchInfo.batch_name }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">所属平台:</span>
              <span class="value">{{ batchInfo.customer?.name || "-" }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">状态:</span>
              <el-tag :type="getStatusTagType(batchInfo.status)">
                {{ getStatusLabel(batchInfo.status) }}
              </el-tag>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="20" style="margin-top: 20px">
          <el-col :span="24">
            <div class="info-item">
              <span class="label">描述:</span>
              <span class="value">{{ batchInfo.description || "无描述" }}</span>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 处理进度 -->
    <div v-if="batchInfo" class="page-card">
      <div class="card-header">
        <h3>处理进度</h3>
      </div>
      <div class="progress-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="progress-item">
              <div class="progress-label">总记录数</div>
              <div class="progress-value">{{ batchInfo.total_records }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="progress-item">
              <div class="progress-label">已处理</div>
              <div class="progress-value success">
                {{ batchInfo.processed_records }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="progress-item">
              <div class="progress-label">失败数</div>
              <div class="progress-value danger">
                {{ batchInfo.failed_records }}
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="progress-item">
              <div class="progress-label">成功率</div>
              <div class="progress-value">{{ getSuccessRate() }}%</div>
            </div>
          </el-col>
        </el-row>

        <div class="progress-bar" style="margin-top: 20px">
          <el-progress
            :percentage="getProgress()"
            :status="getProgressStatus(batchInfo.status)"
            :stroke-width="12"
            :show-text="true"
          />
        </div>
      </div>
    </div>

    <!-- 时间信息 -->
    <div v-if="batchInfo" class="page-card">
      <div class="card-header">
        <h3>时间信息</h3>
      </div>
      <div class="time-info">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="info-item">
              <span class="label">创建时间:</span>
              <span class="value">{{ formatDate(batchInfo.created_at) }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">开始时间:</span>
              <span class="value">{{
                batchInfo.started_at
                  ? formatDate(batchInfo.started_at)
                  : "未开始"
              }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">完成时间:</span>
              <span class="value">{{
                batchInfo.completed_at
                  ? formatDate(batchInfo.completed_at)
                  : "未完成"
              }}</span>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="info-item">
              <span class="label">处理耗时:</span>
              <span class="value">{{ getProcessingDuration() }}</span>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 文件信息 -->
    <div v-if="batchInfo" class="page-card">
      <div class="card-header">
        <h3>文件信息</h3>
      </div>
      <div class="file-info">
        <el-row :gutter="20">
          <el-col :span="12">
            <div class="info-item">
              <span class="label">源文件:</span>
              <span class="value">{{ batchInfo.file_path || "无文件" }}</span>
            </div>
          </el-col>
          <el-col :span="12">
            <div class="info-item">
              <span class="label">结果文件:</span>
              <span class="value">
                {{ batchInfo.result_file_path || "无结果文件" }}
                <el-button
                  v-if="batchInfo.result_file_path"
                  size="small"
                  type="primary"
                  link
                  @click="downloadResult"
                >
                  下载
                </el-button>
              </span>
            </div>
          </el-col>
        </el-row>
      </div>
    </div>

    <!-- 错误信息 -->
    <div v-if="batchInfo?.error_message" class="page-card">
      <div class="card-header">
        <h3>错误信息</h3>
      </div>
      <div class="error-info">
        <el-alert
          :title="batchInfo.error_message"
          type="error"
          :closable="false"
          show-icon
        />
      </div>
    </div>

    <!-- 操作日志 -->
    <div class="page-card">
      <div class="card-header">
        <h3>操作日志</h3>
        <el-button size="small" @click="loadLogs">
          <el-icon><Refresh /></el-icon>
          刷新日志
        </el-button>
      </div>
      <div class="logs-section">
        <el-table v-loading="logsLoading" :data="logs" style="width: 100%">
          <el-table-column prop="timestamp" label="时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.timestamp) }}
            </template>
          </el-table-column>
          <el-table-column prop="level" label="级别" width="100">
            <template #default="{ row }">
              <el-tag :type="getLogLevelTagType(row.level)" size="small">
                {{ row.level }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" label="消息" min-width="300" />
          <el-table-column
            prop="details"
            label="详情"
            width="200"
            show-overflow-tooltip
          />
        </el-table>

        <div v-if="logs.length === 0 && !logsLoading" class="empty-logs">
          <el-empty description="暂无日志记录" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { formatDate } from "@/utils/date";
import {
  getBatch,
  startBatchProcessing,
  stopBatchProcessing,
  downloadBatchResult,
} from "@/api/apiManagement";
import type { DataBatch } from "@/types/apiManagement";

/**
 * 路由
 */
const route = useRoute();
const router = useRouter();

/**
 * 响应式数据
 */
const batchInfo = ref<DataBatch | null>(null);
const logs = ref<
  Array<{
    timestamp: string;
    level: string;
    message: string;
    details?: string;
  }>
>([]);
const logsLoading = ref(false);

/**
 * 生命周期钩子
 */
onMounted(() => {
  const batchId = route.params.id as string;
  if (batchId) {
    loadBatchInfo(parseInt(batchId));
    loadLogs(parseInt(batchId));
  }
});

/**
 * 方法定义
 */

/**
 * 加载批次信息
 */
const loadBatchInfo = async (batchId?: number) => {
  const id = batchId || parseInt(route.params.id as string);

  try {
    const response = await getBatch(id);
    if (response.success) {
      batchInfo.value = response.data;
    } else {
      ElMessage.error(response.message || "加载批次信息失败");
    }
  } catch (error) {
    console.error("加载批次信息失败:", error);
    ElMessage.error("加载批次信息失败");
  }
};

/**
 * 加载操作日志
 */
const loadLogs = async (batchId?: number) => {
  const id = batchId || parseInt(route.params.id as string);

  try {
    logsLoading.value = true;

    // 模拟日志数据，实际应该从API获取
    logs.value = [
      {
        timestamp: new Date().toISOString(),
        level: "INFO",
        message: "批次创建成功",
        details: "批次已创建，等待处理",
      },
      {
        timestamp: new Date(Date.now() - 60000).toISOString(),
        level: "INFO",
        message: "开始处理数据",
        details: "开始读取源文件",
      },
      {
        timestamp: new Date(Date.now() - 120000).toISOString(),
        level: "WARN",
        message: "发现无效数据",
        details: "第10行数据格式不正确",
      },
    ];
  } catch (error) {
    console.error("加载日志失败:", error);
    ElMessage.error("加载日志失败");
  } finally {
    logsLoading.value = false;
  }
};

/**
 * 获取状态标签类型
 */
const getStatusTagType = (status: string) => {
  const types: Record<string, string> = {
    pending: "info",
    processing: "warning",
    completed: "success",
    failed: "danger",
  };
  return types[status] || "info";
};

/**
 * 获取状态标签
 */
const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: "待处理",
    processing: "处理中",
    completed: "已完成",
    failed: "失败",
  };
  return labels[status] || status;
};

/**
 * 获取日志级别标签类型
 */
const getLogLevelTagType = (level: string) => {
  const types: Record<string, string> = {
    INFO: "success",
    WARN: "warning",
    ERROR: "danger",
    DEBUG: "info",
  };
  return types[level] || "info";
};

/**
 * 获取进度百分比
 */
const getProgress = () => {
  if (!batchInfo.value || batchInfo.value.total_records === 0) return 0;
  return Math.round(
    (batchInfo.value.processed_records / batchInfo.value.total_records) * 100,
  );
};

/**
 * 获取成功率
 */
const getSuccessRate = () => {
  if (!batchInfo.value || batchInfo.value.processed_records === 0) return 0;
  const successCount =
    batchInfo.value.processed_records - batchInfo.value.failed_records;
  return Math.round((successCount / batchInfo.value.processed_records) * 100);
};

/**
 * 获取进度状态
 */
const getProgressStatus = (status: string) => {
  if (status === "completed") return "success";
  if (status === "failed") return "exception";
  return undefined;
};

/**
 * 获取处理耗时
 */
const getProcessingDuration = () => {
  if (!batchInfo.value) return "-";

  const startTime = batchInfo.value.started_at;
  const endTime = batchInfo.value.completed_at || new Date().toISOString();

  if (!startTime) return "-";

  const start = new Date(startTime).getTime();
  const end = new Date(endTime).getTime();
  const duration = end - start;

  const hours = Math.floor(duration / (1000 * 60 * 60));
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));
  const seconds = Math.floor((duration % (1000 * 60)) / 1000);

  if (hours > 0) {
    return `${hours}小时${minutes}分钟${seconds}秒`;
  } else if (minutes > 0) {
    return `${minutes}分钟${seconds}秒`;
  } else {
    return `${seconds}秒`;
  }
};

/**
 * 返回上一页
 */
const goBack = () => {
  router.back();
};

/**
 * 开始处理
 */
const startProcessing = async () => {
  if (!batchInfo.value) return;

  try {
    const response = await startBatchProcessing(batchInfo.value.id);
    if (response.success) {
      ElMessage.success("批次处理已开始");
      loadBatchInfo();
    } else {
      ElMessage.error(response.message || "开始处理失败");
    }
  } catch (error) {
    console.error("开始处理失败:", error);
    ElMessage.error("开始处理失败");
  }
};

/**
 * 停止处理
 */
const stopProcessing = async () => {
  if (!batchInfo.value) return;

  try {
    await ElMessageBox.confirm(
      `确定要停止批次 "${batchInfo.value.batch_name}" 的处理吗？`,
      "确认停止",
      {
        confirmButtonText: "确定",
        cancelButtonText: "取消",
        type: "warning",
      },
    );

    const response = await stopBatchProcessing(batchInfo.value.id);
    if (response.success) {
      ElMessage.success("批次处理已停止");
      loadBatchInfo();
    } else {
      ElMessage.error(response.message || "停止处理失败");
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("停止处理失败:", error);
      ElMessage.error("停止处理失败");
    }
  }
};

/**
 * 下载结果
 */
const downloadResult = async () => {
  if (!batchInfo.value) return;

  try {
    const blob = await downloadBatchResult(batchInfo.value.id);

    // 创建下载链接
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `batch_${batchInfo.value.id}_result.xlsx`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    ElMessage.success("文件下载成功");
  } catch (error) {
    console.error("下载结果失败:", error);
    ElMessage.error("下载结果失败");
  }
};
</script>

<style scoped lang="scss">
.batch-detail {
  .page-header {
    margin-bottom: 20px;

    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .header-left {
        display: flex;
        align-items: center;
        gap: 16px;

        .title-section {
          .page-title {
            display: flex;
            align-items: center;
            gap: 8px;
            margin: 0 0 4px 0;
            font-size: 24px;
            font-weight: 600;
            color: var(--el-text-color-primary);
          }

          .page-description {
            margin: 0;
            color: var(--el-text-color-regular);
            font-size: 14px;
          }
        }
      }

      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 20px 0 20px;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
  }

  .batch-info,
  .time-info,
  .file-info {
    padding: 20px;

    .info-item {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;

      .label {
        font-weight: 500;
        color: var(--el-text-color-regular);
        min-width: 80px;
      }

      .value {
        color: var(--el-text-color-primary);
      }
    }
  }

  .progress-section {
    padding: 20px;

    .progress-item {
      text-align: center;

      .progress-label {
        font-size: 14px;
        color: var(--el-text-color-regular);
        margin-bottom: 8px;
      }

      .progress-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);

        &.success {
          color: var(--el-color-success);
        }

        &.danger {
          color: var(--el-color-danger);
        }
      }
    }
  }

  .error-info {
    padding: 20px;
  }

  .logs-section {
    padding: 20px;

    .empty-logs {
      text-align: center;
      padding: 40px 0;
    }
  }
}
</style>
