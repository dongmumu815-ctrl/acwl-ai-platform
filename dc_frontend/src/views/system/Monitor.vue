<template>
  <div class="monitor-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1 class="page-title">
        <el-icon><Monitor /></el-icon>
        系统监控
      </h1>
      <p class="page-description">实时监控系统运行状态和性能指标</p>
    </div>

    <!-- 系统概览 -->
    <div class="overview-section">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="metric-card cpu-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ systemMetrics.cpu.usage }}%</div>
                <div class="metric-label">CPU使用率</div>
                <div
                  class="metric-trend"
                  :class="getTrendClass(systemMetrics.cpu.trend)"
                >
                  <el-icon
                    ><ArrowUp v-if="systemMetrics.cpu.trend > 0" /><ArrowDown
                      v-else
                  /></el-icon>
                  {{ Math.abs(systemMetrics.cpu.trend) }}%
                </div>
              </div>
            </div>
            <div class="metric-progress">
              <el-progress
                :percentage="systemMetrics.cpu.usage"
                :color="getProgressColor(systemMetrics.cpu.usage)"
                :show-text="false"
                :stroke-width="6"
              />
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="metric-card memory-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon><MemoryCard /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">
                  {{ systemMetrics.memory.usage }}%
                </div>
                <div class="metric-label">内存使用率</div>
                <div class="metric-detail">
                  {{ formatBytes(systemMetrics.memory.used) }} /
                  {{ formatBytes(systemMetrics.memory.total) }}
                </div>
              </div>
            </div>
            <div class="metric-progress">
              <el-progress
                :percentage="systemMetrics.memory.usage"
                :color="getProgressColor(systemMetrics.memory.usage)"
                :show-text="false"
                :stroke-width="6"
              />
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="metric-card disk-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon><HardDrive /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">{{ systemMetrics.disk.usage }}%</div>
                <div class="metric-label">磁盘使用率</div>
                <div class="metric-detail">
                  {{ formatBytes(systemMetrics.disk.used) }} /
                  {{ formatBytes(systemMetrics.disk.total) }}
                </div>
              </div>
            </div>
            <div class="metric-progress">
              <el-progress
                :percentage="systemMetrics.disk.usage"
                :color="getProgressColor(systemMetrics.disk.usage)"
                :show-text="false"
                :stroke-width="6"
              />
            </div>
          </el-card>
        </el-col>

        <el-col :span="6">
          <el-card class="metric-card network-card">
            <div class="metric-content">
              <div class="metric-icon">
                <el-icon><Connection /></el-icon>
              </div>
              <div class="metric-info">
                <div class="metric-value">
                  {{ systemMetrics.network.connections }}
                </div>
                <div class="metric-label">网络连接</div>
                <div class="metric-detail">
                  ↑{{ formatBytes(systemMetrics.network.upload) }}/s ↓{{
                    formatBytes(systemMetrics.network.download)
                  }}/s
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 实时图表 -->
    <div class="charts-section">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>CPU & 内存使用率</span>
                <el-button-group size="small">
                  <el-button
                    :type="timeRange === '1h' ? 'primary' : ''"
                    @click="setTimeRange('1h')"
                    >1小时</el-button
                  >
                  <el-button
                    :type="timeRange === '6h' ? 'primary' : ''"
                    @click="setTimeRange('6h')"
                    >6小时</el-button
                  >
                  <el-button
                    :type="timeRange === '24h' ? 'primary' : ''"
                    @click="setTimeRange('24h')"
                    >24小时</el-button
                  >
                </el-button-group>
              </div>
            </template>
            <div ref="cpuMemoryChart" class="chart-container"></div>
          </el-card>
        </el-col>

        <el-col :span="12">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>网络流量</span>
                <el-switch
                  v-model="networkChartRealtime"
                  active-text="实时"
                  inactive-text="历史"
                  @change="toggleNetworkRealtime"
                />
              </div>
            </template>
            <div ref="networkChart" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20" style="margin-top: 20px">
        <el-col :span="24">
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>系统负载</span>
                <div class="load-indicators">
                  <el-tag type="info" size="small"
                    >1分钟: {{ systemMetrics.load.load1 }}</el-tag
                  >
                  <el-tag type="warning" size="small"
                    >5分钟: {{ systemMetrics.load.load5 }}</el-tag
                  >
                  <el-tag type="danger" size="small"
                    >15分钟: {{ systemMetrics.load.load15 }}</el-tag
                  >
                </div>
              </div>
            </template>
            <div ref="loadChart" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 进程监控 -->
    <div class="process-section">
      <el-card class="process-card">
        <template #header>
          <div class="card-header">
            <span>进程监控</span>
            <div class="header-actions">
              <el-input
                v-model="processSearch"
                placeholder="搜索进程..."
                style="width: 200px; margin-right: 12px"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button @click="refreshProcesses">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </div>
        </template>

        <el-table
          v-loading="processLoading"
          :data="filteredProcesses"
          stripe
          style="width: 100%"
          :default-sort="{ prop: 'cpu', order: 'descending' }"
        >
          <el-table-column prop="pid" label="PID" width="80" sortable />
          <el-table-column prop="name" label="进程名" min-width="200" sortable>
            <template #default="{ row }">
              <div class="process-name">
                <el-icon class="process-icon"><Operation /></el-icon>
                <span>{{ row.name }}</span>
                <el-tag v-if="row.isSystemProcess" type="info" size="small"
                  >系统</el-tag
                >
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="cpu" label="CPU%" width="100" sortable>
            <template #default="{ row }">
              <div class="cpu-usage">
                <span :class="getCpuUsageClass(row.cpu)">{{ row.cpu }}%</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="memory" label="内存" width="120" sortable>
            <template #default="{ row }">
              <span>{{ formatBytes(row.memory) }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getProcessStatusType(row.status)" size="small">
                {{ getProcessStatusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="startTime"
            label="启动时间"
            width="150"
            sortable
          >
            <template #default="{ row }">
              {{ formatTime(row.startTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="command" label="命令" min-width="200">
            <template #default="{ row }">
              <el-tooltip :content="row.command" placement="top">
                <span class="command-text">{{
                  truncateText(row.command, 50)
                }}</span>
              </el-tooltip>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                type="danger"
                size="small"
                :disabled="row.isSystemProcess"
                @click="killProcess(row)"
              >
                <el-icon><Close /></el-icon>
                终止
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- 系统服务 -->
    <div class="services-section">
      <el-card class="services-card">
        <template #header>
          <div class="card-header">
            <span>系统服务</span>
            <el-button @click="refreshServices">
              <el-icon><Refresh /></el-icon>
              刷新服务
            </el-button>
          </div>
        </template>

        <el-row :gutter="20">
          <el-col
            v-for="service in systemServices"
            :key="service.name"
            :span="6"
          >
            <div class="service-item">
              <div class="service-header">
                <div class="service-name">{{ service.name }}</div>
                <el-tag
                  :type="getServiceStatusType(service.status)"
                  size="small"
                >
                  {{ getServiceStatusLabel(service.status) }}
                </el-tag>
              </div>
              <div class="service-description">{{ service.description }}</div>
              <div class="service-actions">
                <el-button
                  v-if="service.status === 'stopped'"
                  type="success"
                  size="small"
                  @click="startService(service)"
                >
                  启动
                </el-button>
                <el-button
                  v-if="service.status === 'running'"
                  type="warning"
                  size="small"
                  @click="stopService(service)"
                >
                  停止
                </el-button>
                <el-button
                  v-if="service.status === 'running'"
                  type="info"
                  size="small"
                  @click="restartService(service)"
                >
                  重启
                </el-button>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";

// 响应式数据
const timeRange = ref("1h");
const networkChartRealtime = ref(true);
const processSearch = ref("");
const processLoading = ref(false);

// 图表引用
const cpuMemoryChart = ref<HTMLElement>();
const networkChart = ref<HTMLElement>();
const loadChart = ref<HTMLElement>();

// 定时器
let metricsTimer: NodeJS.Timeout | null = null;
let chartTimer: NodeJS.Timeout | null = null;

// 系统指标数据
const systemMetrics = ref({
  cpu: {
    usage: 45,
    trend: 2.3,
  },
  memory: {
    usage: 68,
    used: 5497558138880, // 5.5GB
    total: 8589934592000, // 8GB
  },
  disk: {
    usage: 72,
    used: 751619276800, // 700GB
    total: 1099511627776, // 1TB
  },
  network: {
    connections: 156,
    upload: 1048576, // 1MB/s
    download: 2097152, // 2MB/s
  },
  load: {
    load1: 1.25,
    load5: 1.18,
    load15: 1.32,
  },
});

// 进程数据
const processes = ref([
  {
    pid: 1234,
    name: "node",
    cpu: 15.6,
    memory: 536870912, // 512MB
    status: "running",
    startTime: "2024-01-15 08:30:00",
    command: "node /app/server.js --port 3000",
    isSystemProcess: false,
  },
  {
    pid: 5678,
    name: "nginx",
    cpu: 2.3,
    memory: 67108864, // 64MB
    status: "running",
    startTime: "2024-01-15 08:00:00",
    command: "nginx: master process /usr/sbin/nginx -g daemon off;",
    isSystemProcess: true,
  },
  {
    pid: 9012,
    name: "mysql",
    cpu: 8.7,
    memory: 1073741824, // 1GB
    status: "running",
    startTime: "2024-01-15 08:00:00",
    command:
      "/usr/sbin/mysqld --daemonize --pid-file=/var/run/mysqld/mysqld.pid",
    isSystemProcess: true,
  },
  {
    pid: 3456,
    name: "redis-server",
    cpu: 1.2,
    memory: 134217728, // 128MB
    status: "running",
    startTime: "2024-01-15 08:00:00",
    command: "redis-server *:6379",
    isSystemProcess: false,
  },
  {
    pid: 7890,
    name: "python",
    cpu: 25.4,
    memory: 268435456, // 256MB
    status: "running",
    startTime: "2024-01-15 14:20:00",
    command: "python /app/data_processor.py --batch-size 1000",
    isSystemProcess: false,
  },
]);

// 系统服务数据
const systemServices = ref([
  {
    name: "Web服务器",
    status: "running",
    description: "Nginx Web服务器",
  },
  {
    name: "数据库",
    status: "running",
    description: "MySQL数据库服务",
  },
  {
    name: "缓存服务",
    status: "running",
    description: "Redis缓存服务",
  },
  {
    name: "消息队列",
    status: "stopped",
    description: "RabbitMQ消息队列",
  },
  {
    name: "监控服务",
    status: "running",
    description: "系统监控代理",
  },
  {
    name: "备份服务",
    status: "stopped",
    description: "自动备份服务",
  },
  {
    name: "日志服务",
    status: "running",
    description: "日志收集服务",
  },
  {
    name: "防火墙",
    status: "running",
    description: "系统防火墙服务",
  },
]);

/**
 * 过滤后的进程列表
 */
const filteredProcesses = computed(() => {
  if (!processSearch.value) {
    return processes.value;
  }

  const keyword = processSearch.value.toLowerCase();
  return processes.value.filter(
    (process) =>
      process.name.toLowerCase().includes(keyword) ||
      process.command.toLowerCase().includes(keyword) ||
      process.pid.toString().includes(keyword),
  );
});

/**
 * 获取进度条颜色
 */
const getProgressColor = (percentage: number) => {
  if (percentage < 50) return "#67c23a";
  if (percentage < 80) return "#e6a23c";
  return "#f56c6c";
};

/**
 * 获取趋势样式类
 */
const getTrendClass = (trend: number) => {
  return trend > 0 ? "trend-up" : "trend-down";
};

/**
 * 格式化字节数
 */
const formatBytes = (bytes: number) => {
  if (bytes === 0) return "0 B";

  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
};

/**
 * 格式化时间
 */
const formatTime = (timeStr: string) => {
  return new Date(timeStr).toLocaleString("zh-CN");
};

/**
 * 截断文本
 */
const truncateText = (text: string, maxLength: number) => {
  return text.length > maxLength ? text.substring(0, maxLength) + "..." : text;
};

/**
 * 获取CPU使用率样式类
 */
const getCpuUsageClass = (cpu: number) => {
  if (cpu < 50) return "cpu-low";
  if (cpu < 80) return "cpu-medium";
  return "cpu-high";
};

/**
 * 获取进程状态类型
 */
const getProcessStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    running: "success",
    sleeping: "info",
    stopped: "danger",
    zombie: "warning",
  };
  return typeMap[status] || "info";
};

/**
 * 获取进程状态标签
 */
const getProcessStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    running: "运行中",
    sleeping: "休眠",
    stopped: "已停止",
    zombie: "僵尸进程",
  };
  return labelMap[status] || status;
};

/**
 * 获取服务状态类型
 */
const getServiceStatusType = (status: string) => {
  const typeMap: Record<string, string> = {
    running: "success",
    stopped: "danger",
    starting: "warning",
    stopping: "warning",
  };
  return typeMap[status] || "info";
};

/**
 * 获取服务状态标签
 */
const getServiceStatusLabel = (status: string) => {
  const labelMap: Record<string, string> = {
    running: "运行中",
    stopped: "已停止",
    starting: "启动中",
    stopping: "停止中",
  };
  return labelMap[status] || status;
};

/**
 * 设置时间范围
 */
const setTimeRange = (range: string) => {
  timeRange.value = range;
  updateCharts();
};

/**
 * 切换网络图表实时模式
 */
const toggleNetworkRealtime = (realtime: boolean) => {
  if (realtime) {
    ElMessage.success("网络图表已切换到实时模式");
  } else {
    ElMessage.info("网络图表已切换到历史模式");
  }
  updateCharts();
};

/**
 * 刷新进程列表
 */
const refreshProcesses = () => {
  processLoading.value = true;

  setTimeout(() => {
    // 模拟更新进程数据
    processes.value.forEach((process) => {
      process.cpu = Math.random() * 30;
      process.memory = process.memory + (Math.random() - 0.5) * 10485760; // ±10MB
    });

    processLoading.value = false;
    ElMessage.success("进程列表已刷新");
  }, 1000);
};

/**
 * 终止进程
 */
const killProcess = (process: any) => {
  ElMessageBox.confirm(
    `确定要终止进程 "${process.name}" (PID: ${process.pid}) 吗？`,
    "确认终止进程",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    },
  )
    .then(() => {
      const index = processes.value.findIndex((p) => p.pid === process.pid);
      if (index > -1) {
        processes.value.splice(index, 1);
        ElMessage.success(`进程 ${process.name} 已终止`);
      }
    })
    .catch(() => {
      // 用户取消
    });
};

/**
 * 刷新服务列表
 */
const refreshServices = () => {
  ElMessage.success("服务列表已刷新");
};

/**
 * 启动服务
 */
const startService = (service: any) => {
  service.status = "starting";
  ElMessage.info(`正在启动 ${service.name}...`);

  setTimeout(() => {
    service.status = "running";
    ElMessage.success(`${service.name} 已启动`);
  }, 2000);
};

/**
 * 停止服务
 */
const stopService = (service: any) => {
  ElMessageBox.confirm(
    `确定要停止 "${service.name}" 服务吗？`,
    "确认停止服务",
    {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    },
  )
    .then(() => {
      service.status = "stopping";
      ElMessage.info(`正在停止 ${service.name}...`);

      setTimeout(() => {
        service.status = "stopped";
        ElMessage.success(`${service.name} 已停止`);
      }, 2000);
    })
    .catch(() => {
      // 用户取消
    });
};

/**
 * 重启服务
 */
const restartService = (service: any) => {
  service.status = "stopping";
  ElMessage.info(`正在重启 ${service.name}...`);

  setTimeout(() => {
    service.status = "starting";
    setTimeout(() => {
      service.status = "running";
      ElMessage.success(`${service.name} 已重启`);
    }, 2000);
  }, 1000);
};

/**
 * 更新系统指标
 */
const updateMetrics = () => {
  // 模拟更新系统指标
  systemMetrics.value.cpu.usage = Math.floor(Math.random() * 100);
  systemMetrics.value.memory.usage = Math.floor(Math.random() * 100);
  systemMetrics.value.disk.usage = Math.floor(Math.random() * 100);
  systemMetrics.value.network.connections =
    Math.floor(Math.random() * 300) + 50;
  systemMetrics.value.network.upload = Math.floor(Math.random() * 10485760); // 0-10MB/s
  systemMetrics.value.network.download = Math.floor(Math.random() * 20971520); // 0-20MB/s
  systemMetrics.value.load.load1 = Math.random() * 3;
  systemMetrics.value.load.load5 = Math.random() * 3;
  systemMetrics.value.load.load15 = Math.random() * 3;
};

/**
 * 初始化图表
 */
const initCharts = () => {
  // 这里应该使用真实的图表库（如 ECharts）来初始化图表
  // 为了演示，我们只是创建占位符
  nextTick(() => {
    if (cpuMemoryChart.value) {
      cpuMemoryChart.value.innerHTML =
        '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">CPU & 内存使用率图表</div>';
    }
    if (networkChart.value) {
      networkChart.value.innerHTML =
        '<div style="height: 300px; display: flex; align-items: center; justify-content: center; color: #999;">网络流量图表</div>';
    }
    if (loadChart.value) {
      loadChart.value.innerHTML =
        '<div style="height: 200px; display: flex; align-items: center; justify-content: center; color: #999;">系统负载图表</div>';
    }
  });
};

/**
 * 更新图表
 */
const updateCharts = () => {
  // 这里应该更新图表数据
  console.log("更新图表数据");
};

/**
 * 组件挂载时初始化
 */
onMounted(() => {
  initCharts();

  // 启动定时器更新数据
  metricsTimer = setInterval(updateMetrics, 5000); // 每5秒更新一次指标
  chartTimer = setInterval(updateCharts, 10000); // 每10秒更新一次图表
});

/**
 * 组件卸载时清理
 */
onUnmounted(() => {
  if (metricsTimer) {
    clearInterval(metricsTimer);
  }
  if (chartTimer) {
    clearInterval(chartTimer);
  }
});
</script>

<style lang="scss" scoped>
.monitor-container {
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

.overview-section,
.charts-section,
.process-section,
.services-section {
  margin-bottom: 20px;
}

.metric-card {
  height: 120px;

  .metric-content {
    display: flex;
    align-items: center;
    margin-bottom: 12px;

    .metric-icon {
      font-size: 32px;
      margin-right: 16px;
      color: var(--el-color-primary);
    }

    .metric-info {
      flex: 1;

      .metric-value {
        font-size: 24px;
        font-weight: 600;
        color: var(--el-text-color-primary);
        line-height: 1;
      }

      .metric-label {
        font-size: 14px;
        color: var(--el-text-color-secondary);
        margin: 4px 0;
      }

      .metric-detail {
        font-size: 12px;
        color: var(--el-text-color-placeholder);
      }

      .metric-trend {
        display: flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;

        &.trend-up {
          color: var(--el-color-danger);
        }

        &.trend-down {
          color: var(--el-color-success);
        }
      }
    }
  }

  .metric-progress {
    margin-top: auto;
  }
}

.chart-card {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .load-indicators {
      display: flex;
      gap: 8px;
    }
  }

  .chart-container {
    height: 300px;
    background: var(--el-bg-color-page);
    border-radius: 4px;
  }
}

.process-card,
.services-card {
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

.process-name {
  display: flex;
  align-items: center;
  gap: 8px;

  .process-icon {
    color: var(--el-color-primary);
  }
}

.cpu-usage {
  .cpu-low {
    color: var(--el-color-success);
  }

  .cpu-medium {
    color: var(--el-color-warning);
  }

  .cpu-high {
    color: var(--el-color-danger);
  }
}

.command-text {
  font-family: "Courier New", monospace;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.service-item {
  padding: 16px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  border: 1px solid var(--el-border-color-light);
  margin-bottom: 16px;

  .service-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;

    .service-name {
      font-weight: 600;
      color: var(--el-text-color-primary);
    }
  }

  .service-description {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-bottom: 12px;
  }

  .service-actions {
    display: flex;
    gap: 8px;
  }
}

// 响应式设计
@media (max-width: 1200px) {
  .overview-section {
    .el-col {
      margin-bottom: 16px;
    }
  }

  .charts-section {
    .el-col {
      margin-bottom: 20px;
    }
  }
}

@media (max-width: 768px) {
  .monitor-container {
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

  .metric-card {
    height: auto;

    .metric-content {
      flex-direction: column;
      text-align: center;

      .metric-icon {
        margin-right: 0;
        margin-bottom: 8px;
      }
    }
  }

  .services-section {
    .el-col {
      span: 24 !important;
    }
  }
}
</style>
