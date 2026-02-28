<template>
  <div class="logs-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Document /></el-icon>
        系统日志
      </h1>
      <p class="page-description">查看和管理系统运行日志</p>
    </div>

    <!-- 筛选和操作栏 -->
    <div class="filter-bar">
      <div class="filter-left">
        <el-select
          v-model="filterLevel"
          placeholder="日志级别"
          style="width: 120px"
          clearable
        >
          <el-option label="全部" value="" />
          <el-option label="调试" value="debug" />
          <el-option label="信息" value="info" />
          <el-option label="警告" value="warn" />
          <el-option label="错误" value="error" />
          <el-option label="致命" value="fatal" />
        </el-select>

        <el-select
          v-model="filterModule"
          placeholder="模块"
          style="width: 150px"
          clearable
        >
          <el-option label="全部" value="" />
          <el-option label="用户管理" value="user" />
          <el-option label="数据中心" value="data" />
          <el-option label="权限管理" value="permission" />
          <el-option label="系统管理" value="system" />
          <el-option label="API接口" value="api" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="datetimerange"
          range-separator="至"
          start-placeholder="开始时间"
          end-placeholder="结束时间"
          format="YYYY-MM-DD HH:mm:ss"
          value-format="YYYY-MM-DD HH:mm:ss"
          style="width: 350px"
        />
      </div>

      <div class="filter-right">
        <el-input
          v-model="searchKeyword"
          placeholder="搜索日志内容..."
          style="width: 250px"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-button @click="refreshLogs">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>

        <el-button @click="exportLogs">
          <el-icon><Download /></el-icon>
          导出
        </el-button>

        <el-button type="danger" @click="clearLogs">
          <el-icon><Delete /></el-icon>
          清空日志
        </el-button>
      </div>
    </div>

    <!-- 实时日志开关 -->
    <div class="realtime-control">
      <el-switch
        v-model="realtimeEnabled"
        active-text="实时日志"
        inactive-text="静态查看"
        @change="toggleRealtime"
      />
      <span v-if="realtimeEnabled" class="realtime-status">
        <el-icon class="status-icon"><VideoPlay /></el-icon>
        实时监控中...
      </span>
    </div>

    <!-- 日志列表 -->
    <div class="logs-content">
      <el-table
        v-loading="loading"
        :data="filteredLogs"
        stripe
        style="width: 100%"
        :row-class-name="getRowClassName"
        @row-click="viewLogDetail"
      >
        <el-table-column prop="timestamp" label="时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatDate(row.timestamp) }}
          </template>
        </el-table-column>

        <el-table-column prop="level" label="级别" width="80">
          <template #default="{ row }">
            <el-tag :type="getLevelTagType(row.level)" size="small">
              {{ getLevelLabel(row.level) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="module" label="模块" width="120">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{
              getModuleLabel(row.module)
            }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="user" label="用户" width="100">
          <template #default="{ row }">
            <span v-if="row.user">{{ row.user }}</span>
            <span v-else class="text-placeholder">系统</span>
          </template>
        </el-table-column>

        <el-table-column prop="ip" label="IP地址" width="130" />

        <el-table-column prop="message" label="日志内容" min-width="300">
          <template #default="{ row }">
            <div class="log-message">
              <span class="message-text">{{ row.message }}</span>
              <el-button
                v-if="row.details"
                type="primary"
                size="small"
                text
                @click.stop="viewLogDetail(row)"
              >
                查看详情
              </el-button>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="requestId" label="请求ID" width="120">
          <template #default="{ row }">
            <span v-if="row.requestId" class="request-id">{{
              row.requestId
            }}</span>
            <span v-else class="text-placeholder">-</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[20, 50, 100, 200]"
        :total="totalLogs"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="logDetailVisible"
      title="日志详情"
      width="800px"
      top="5vh"
    >
      <div v-if="selectedLog" class="log-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="时间">
            {{ formatDate(selectedLog.timestamp) }}
          </el-descriptions-item>
          <el-descriptions-item label="级别">
            <el-tag :type="getLevelTagType(selectedLog.level)">
              {{ getLevelLabel(selectedLog.level) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="模块">
            <el-tag type="info">{{
              getModuleLabel(selectedLog.module)
            }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户">
            {{ selectedLog.user || "系统" }}
          </el-descriptions-item>
          <el-descriptions-item label="IP地址">
            {{ selectedLog.ip }}
          </el-descriptions-item>
          <el-descriptions-item label="请求ID">
            {{ selectedLog.requestId || "-" }}
          </el-descriptions-item>
          <el-descriptions-item label="消息" span="2">
            {{ selectedLog.message }}
          </el-descriptions-item>
        </el-descriptions>

        <div v-if="selectedLog.details" class="log-details">
          <h4>详细信息</h4>
          <el-input
            v-model="selectedLog.details"
            type="textarea"
            :rows="10"
            readonly
            class="details-textarea"
          />
        </div>

        <div v-if="selectedLog.stack" class="log-stack">
          <h4>堆栈信息</h4>
          <el-input
            v-model="selectedLog.stack"
            type="textarea"
            :rows="8"
            readonly
            class="stack-textarea"
          />
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="logDetailVisible = false">关闭</el-button>
          <el-button type="primary" @click="copyLogDetail">
            <el-icon><CopyDocument /></el-icon>
            复制详情
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

// 响应式数据
const loading = ref(false);
const searchKeyword = ref("");
const filterLevel = ref("");
const filterModule = ref("");
const dateRange = ref<[string, string] | null>(null);
const currentPage = ref(1);
const pageSize = ref(50);
const totalLogs = ref(0);
const realtimeEnabled = ref(false);
const logDetailVisible = ref(false);
const selectedLog = ref<any>(null);

// 实时日志定时器
let realtimeTimer: NodeJS.Timeout | null = null;

// 日志数据
const logs = ref([
  {
    id: 1,
    timestamp: "2024-01-15 14:30:25",
    level: "info",
    module: "user",
    user: "张三",
    ip: "192.168.1.100",
    message: "用户登录成功",
    requestId: "req_001",
    details:
      "用户张三通过用户名密码方式登录系统，登录IP: 192.168.1.100，浏览器: Chrome 120.0.0.0",
    stack: null,
  },
  {
    id: 2,
    timestamp: "2024-01-15 14:29:45",
    level: "warn",
    module: "api",
    user: "李四",
    ip: "192.168.1.101",
    message: "API调用频率过高",
    requestId: "req_002",
    details:
      "API接口 /api/data/query 在1分钟内被调用了150次，超过了限制阈值100次",
    stack: null,
  },
  {
    id: 3,
    timestamp: "2024-01-15 14:29:30",
    level: "error",
    module: "data",
    user: null,
    ip: "127.0.0.1",
    message: "数据库连接失败",
    requestId: "req_003",
    details: "连接数据库时发生错误: Connection timeout after 30000ms",
    stack:
      "Error: Connection timeout\n    at Database.connect (/app/db.js:45:12)\n    at DataService.query (/app/service.js:23:8)\n    at async Controller.getData (/app/controller.js:15:5)",
  },
  {
    id: 4,
    timestamp: "2024-01-15 14:29:15",
    level: "debug",
    module: "system",
    user: null,
    ip: "127.0.0.1",
    message: "系统定时任务执行",
    requestId: null,
    details: '定时任务 "数据清理" 开始执行，预计耗时5分钟',
    stack: null,
  },
  {
    id: 5,
    timestamp: "2024-01-15 14:29:00",
    level: "fatal",
    module: "system",
    user: null,
    ip: "127.0.0.1",
    message: "系统内存不足",
    requestId: null,
    details: "系统可用内存不足100MB，当前使用率95%，建议立即处理",
    stack:
      "OutOfMemoryError: Java heap space\n    at java.util.Arrays.copyOf(Arrays.java:3332)\n    at java.lang.AbstractStringBuilder.ensureCapacityInternal(AbstractStringBuilder.java:124)",
  },
  {
    id: 6,
    timestamp: "2024-01-15 14:28:45",
    level: "info",
    module: "permission",
    user: "王五",
    ip: "192.168.1.102",
    message: "权限配置更新",
    requestId: "req_004",
    details: '用户王五更新了角色 "数据分析师" 的权限配置，新增了数据导出权限',
    stack: null,
  },
  {
    id: 7,
    timestamp: "2024-01-15 14:28:30",
    level: "warn",
    module: "data",
    user: "赵六",
    ip: "192.168.1.103",
    message: "数据查询超时",
    requestId: "req_005",
    details:
      "查询语句执行时间超过30秒: SELECT * FROM large_table WHERE complex_condition",
    stack: null,
  },
  {
    id: 8,
    timestamp: "2024-01-15 14:28:15",
    level: "info",
    module: "user",
    user: "孙七",
    ip: "192.168.1.104",
    message: "用户信息更新",
    requestId: "req_006",
    details: "用户孙七更新了个人信息，包括邮箱和手机号码",
    stack: null,
  },
]);

/**
 * 过滤后的日志列表
 */
const filteredLogs = computed(() => {
  let filtered = logs.value;

  // 按级别筛选
  if (filterLevel.value) {
    filtered = filtered.filter((log) => log.level === filterLevel.value);
  }

  // 按模块筛选
  if (filterModule.value) {
    filtered = filtered.filter((log) => log.module === filterModule.value);
  }

  // 按关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase();
    filtered = filtered.filter(
      (log) =>
        log.message.toLowerCase().includes(keyword) ||
        (log.user && log.user.toLowerCase().includes(keyword)) ||
        log.ip.includes(keyword) ||
        (log.requestId && log.requestId.toLowerCase().includes(keyword)),
    );
  }

  // 按日期范围筛选
  if (dateRange.value && dateRange.value.length === 2) {
    const [startDate, endDate] = dateRange.value;
    filtered = filtered.filter((log) => {
      return log.timestamp >= startDate && log.timestamp <= endDate;
    });
  }

  return filtered.sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime(),
  );
});

/**
 * 获取级别标签类型
 */
const getLevelTagType = (level: string) => {
  const tagMap: Record<string, string> = {
    debug: "info",
    info: "success",
    warn: "warning",
    error: "danger",
    fatal: "danger",
  };
  return tagMap[level] || "info";
};

/**
 * 获取级别标签文本
 */
const getLevelLabel = (level: string) => {
  const labelMap: Record<string, string> = {
    debug: "调试",
    info: "信息",
    warn: "警告",
    error: "错误",
    fatal: "致命",
  };
  return labelMap[level] || level;
};

/**
 * 获取模块标签文本
 */
const getModuleLabel = (module: string) => {
  const labelMap: Record<string, string> = {
    user: "用户管理",
    data: "数据中心",
    permission: "权限管理",
    system: "系统管理",
    api: "API接口",
  };
  return labelMap[module] || module;
};

/**
 * 获取行样式类名
 */
const getRowClassName = ({ row }: { row: any }) => {
  const classMap: Record<string, string> = {
    debug: "log-row-debug",
    info: "log-row-info",
    warn: "log-row-warn",
    error: "log-row-error",
    fatal: "log-row-fatal",
  };
  return classMap[row.level] || "";
};

/**
 * 格式化日期
 */
const formatDate = (dateStr: string) => {
  return new Date(dateStr).toLocaleString("zh-CN");
};

/**
 * 查看日志详情
 */
const viewLogDetail = (log: any) => {
  selectedLog.value = log;
  logDetailVisible.value = true;
};

/**
 * 复制日志详情
 */
const copyLogDetail = () => {
  if (!selectedLog.value) return;

  const detail = [
    `时间: ${formatDate(selectedLog.value.timestamp)}`,
    `级别: ${getLevelLabel(selectedLog.value.level)}`,
    `模块: ${getModuleLabel(selectedLog.value.module)}`,
    `用户: ${selectedLog.value.user || "系统"}`,
    `IP地址: ${selectedLog.value.ip}`,
    `请求ID: ${selectedLog.value.requestId || "-"}`,
    `消息: ${selectedLog.value.message}`,
    selectedLog.value.details ? `详细信息: ${selectedLog.value.details}` : "",
    selectedLog.value.stack ? `堆栈信息: ${selectedLog.value.stack}` : "",
  ]
    .filter(Boolean)
    .join("\n");

  navigator.clipboard
    .writeText(detail)
    .then(() => {
      ElMessage.success("日志详情已复制到剪贴板");
    })
    .catch(() => {
      ElMessage.error("复制失败");
    });
};

/**
 * 刷新日志
 */
const refreshLogs = () => {
  loading.value = true;

  // 模拟刷新
  setTimeout(() => {
    loading.value = false;
    ElMessage.success("日志列表已刷新");
  }, 1000);
};

/**
 * 导出日志
 */
const exportLogs = () => {
  ElMessage.info("开始导出日志文件");

  // 模拟导出
  setTimeout(() => {
    ElMessage.success("日志文件导出成功");
  }, 2000);
};

/**
 * 清空日志
 */
const clearLogs = () => {
  ElMessageBox.confirm("确定要清空所有日志吗？此操作不可恢复！", "确认清空", {
    confirmButtonText: "确定",
    cancelButtonText: "取消",
    type: "warning",
  })
    .then(() => {
      logs.value = [];
      ElMessage.success("日志已清空");
    })
    .catch(() => {
      // 用户取消清空
    });
};

/**
 * 切换实时日志
 */
const toggleRealtime = (enabled: boolean) => {
  if (enabled) {
    startRealtimeLog();
    ElMessage.success("实时日志已开启");
  } else {
    stopRealtimeLog();
    ElMessage.info("实时日志已关闭");
  }
};

/**
 * 开始实时日志
 */
const startRealtimeLog = () => {
  realtimeTimer = setInterval(() => {
    // 模拟新日志
    const newLog = {
      id: Date.now(),
      timestamp: new Date().toISOString().replace("T", " ").substring(0, 19),
      level: ["debug", "info", "warn", "error"][Math.floor(Math.random() * 4)],
      module: ["user", "data", "permission", "system", "api"][
        Math.floor(Math.random() * 5)
      ],
      user:
        Math.random() > 0.5
          ? ["张三", "李四", "王五"][Math.floor(Math.random() * 3)]
          : null,
      ip: `192.168.1.${Math.floor(Math.random() * 255)}`,
      message: "实时日志消息 - " + Math.random().toString(36).substring(7),
      requestId:
        Math.random() > 0.5
          ? "req_" + Math.random().toString(36).substring(7)
          : null,
      details: "这是一条实时生成的日志详情",
      stack: null,
    };

    logs.value.unshift(newLog);

    // 限制日志数量
    if (logs.value.length > 1000) {
      logs.value = logs.value.slice(0, 1000);
    }
  }, 3000); // 每3秒生成一条新日志
};

/**
 * 停止实时日志
 */
const stopRealtimeLog = () => {
  if (realtimeTimer) {
    clearInterval(realtimeTimer);
    realtimeTimer = null;
  }
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
  totalLogs.value = logs.value.length;
});

/**
 * 组件卸载时清理
 */
onUnmounted(() => {
  stopRealtimeLog();
});
</script>

<style lang="scss" scoped>
.logs-container {
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

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px;
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);

  .filter-left {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .filter-right {
    display: flex;
    gap: 12px;
    align-items: center;
  }
}

.realtime-control {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: var(--el-bg-color);
  border-radius: 6px;
  border: 1px solid var(--el-border-color-light);

  .realtime-status {
    display: flex;
    align-items: center;
    gap: 4px;
    color: var(--el-color-success);
    font-size: 14px;

    .status-icon {
      animation: pulse 1.5s infinite;
    }
  }
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.logs-content {
  background: var(--el-bg-color);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  overflow: hidden;

  .log-message {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .message-text {
      flex: 1;
      margin-right: 12px;
    }
  }

  .request-id {
    font-family: "Courier New", monospace;
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }

  .text-placeholder {
    color: var(--el-text-color-placeholder);
  }
}

// 日志级别行样式
:deep(.log-row-debug) {
  background-color: var(--el-color-info-light-9) !important;
}

:deep(.log-row-info) {
  background-color: var(--el-color-success-light-9) !important;
}

:deep(.log-row-warn) {
  background-color: var(--el-color-warning-light-9) !important;
}

:deep(.log-row-error) {
  background-color: var(--el-color-danger-light-9) !important;
}

:deep(.log-row-fatal) {
  background-color: var(--el-color-danger-light-8) !important;
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

.log-detail {
  .log-details,
  .log-stack {
    margin-top: 20px;

    h4 {
      margin: 0 0 12px 0;
      color: var(--el-text-color-primary);
      font-size: 14px;
      font-weight: 600;
    }

    .details-textarea,
    .stack-textarea {
      font-family: "Courier New", monospace;
      font-size: 12px;

      :deep(.el-textarea__inner) {
        background-color: var(--el-bg-color-page);
      }
    }
  }
}

.dialog-footer {
  text-align: right;
}

// 响应式设计
@media (max-width: 1200px) {
  .filter-bar {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;

    .filter-left,
    .filter-right {
      justify-content: center;
      flex-wrap: wrap;
    }
  }
}

@media (max-width: 768px) {
  .logs-container {
    padding: 16px;
  }

  .filter-bar {
    .filter-left,
    .filter-right {
      flex-direction: column;
      width: 100%;
    }
  }

  .realtime-control {
    flex-direction: column;
    align-items: stretch;
    text-align: center;
  }
}
</style>
