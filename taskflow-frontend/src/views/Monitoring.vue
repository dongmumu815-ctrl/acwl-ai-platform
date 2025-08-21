<template>
  <div class="monitoring">
    <div class="monitoring-header">
      <h2>系统监控</h2>
      <div class="header-actions">
        <el-select v-model="selectedProject" placeholder="选择项目" clearable style="width: 200px; margin-right: 12px">
          <el-option
            v-for="project in projects"
            :key="project.id"
            :label="project.name"
            :value="project.id"
          />
        </el-select>
        <el-select v-model="timeRange" style="width: 150px; margin-right: 12px">
          <el-option label="最近1小时" value="1h" />
          <el-option label="最近6小时" value="6h" />
          <el-option label="最近24小时" value="24h" />
          <el-option label="最近7天" value="7d" />
          <el-option label="最近30天" value="30d" />
        </el-select>
        <el-button @click="refreshData" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <div class="monitoring-content" v-loading="loading">
      <!-- 系统概览 -->
      <el-row :gutter="20" class="overview-section">
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="overview-item">
              <div class="overview-icon running">
                <el-icon :size="24"><VideoPlay /></el-icon>
              </div>
              <div class="overview-info">
                <div class="overview-value">{{ systemStats.running_workflows || 0 }}</div>
                <div class="overview-label">运行中工作流</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="overview-item">
              <div class="overview-icon pending">
                <el-icon :size="24"><Clock /></el-icon>
              </div>
              <div class="overview-info">
                <div class="overview-value">{{ systemStats.pending_tasks || 0 }}</div>
                <div class="overview-label">等待中任务</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="overview-item">
              <div class="overview-icon success">
                <el-icon :size="24"><SuccessFilled /></el-icon>
              </div>
              <div class="overview-info">
                <div class="overview-value">{{ calculateSuccessRate() }}%</div>
                <div class="overview-label">成功率</div>
              </div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="overview-card">
            <div class="overview-item">
              <div class="overview-icon error">
                <el-icon :size="24"><Warning /></el-icon>
              </div>
              <div class="overview-info">
                <div class="overview-value">{{ systemStats.error_count || 0 }}</div>
                <div class="overview-label">错误数量</div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <!-- 执行趋势图 -->
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>执行趋势</span>
                <el-radio-group v-model="executionChartType" size="small">
                  <el-radio-button label="count">执行次数</el-radio-button>
                  <el-radio-button label="duration">平均耗时</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div ref="executionChart" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <!-- 状态分布图 -->
          <el-card class="chart-card">
            <template #header>
              <span>状态分布</span>
            </template>
            <div ref="statusChart" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="16">
          <!-- 系统资源监控 -->
          <el-card class="chart-card">
            <template #header>
              <div class="card-header">
                <span>系统资源</span>
                <el-radio-group v-model="resourceType" size="small">
                  <el-radio-button label="cpu">CPU</el-radio-button>
                  <el-radio-button label="memory">内存</el-radio-button>
                  <el-radio-button label="disk">磁盘</el-radio-button>
                </el-radio-group>
              </div>
            </template>
            <div ref="resourceChart" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <el-col :span="8">
          <!-- 实时日志 -->
          <el-card class="log-card">
            <template #header>
              <div class="card-header">
                <span>实时日志</span>
                <el-switch
                  v-model="autoRefreshLogs"
                  active-text="自动刷新"
                  size="small"
                />
              </div>
            </template>
            <div class="log-container">
              <div v-if="logs.length === 0" class="empty-logs">
                <el-empty description="暂无日志" :image-size="60" />
              </div>
              <div v-else class="log-list">
                <div
                  v-for="log in logs"
                  :key="log.id"
                  :class="['log-item', `log-${log.level}`]"
                >
                  <div class="log-time">{{ formatTime(log.timestamp) }}</div>
                  <div class="log-level">
                    <el-tag :type="getLogLevelColor(log.level)" size="small">
                      {{ log.level.toUpperCase() }}
                    </el-tag>
                  </div>
                  <div class="log-message">{{ log.message }}</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 活跃工作流 -->
      <el-card class="table-card">
        <template #header>
          <div class="card-header">
            <span>活跃工作流</span>
            <el-button text type="primary" @click="viewAllWorkflows">
              查看全部
            </el-button>
          </div>
        </template>
        
        <el-table :data="activeWorkflows" style="width: 100%">
          <el-table-column prop="name" label="工作流名称" min-width="200">
            <template #default="{ row }">
              <el-link @click="viewWorkflowDetail(row.id)" type="primary">
                {{ row.name }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="project_name" label="所属项目" width="150" />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusColor(row.status)">
                {{ formatStatus(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="started_at" label="开始时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.started_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="运行时长" width="120">
            <template #default="{ row }">
              {{ formatDuration(row.duration) }}
            </template>
          </el-table-column>
          <el-table-column prop="progress" label="进度" width="120">
            <template #default="{ row }">
              <el-progress
                :percentage="row.progress || 0"
                :status="row.status === 'failed' ? 'exception' : undefined"
                :stroke-width="6"
              />
            </template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.status === 'running'"
                @click="stopWorkflow(row.id)"
                type="danger"
                size="small"
                text
              >
                停止
              </el-button>
              <el-button
                @click="viewWorkflowDetail(row.id)"
                type="primary"
                size="small"
                text
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-card>

      <!-- 系统警告 -->
      <el-card class="alert-card" v-if="alerts.length > 0">
        <template #header>
          <div class="card-header">
            <span>系统警告</span>
            <el-button @click="clearAlerts" size="small">
              清除全部
            </el-button>
          </div>
        </template>
        
        <div class="alert-list">
          <el-alert
            v-for="alert in alerts"
            :key="alert.id"
            :title="alert.title"
            :description="alert.description"
            :type="alert.type"
            :closable="true"
            @close="removeAlert(alert.id)"
            style="margin-bottom: 12px"
          >
            <template #default>
              <div class="alert-content">
                <div class="alert-message">{{ alert.message }}</div>
                <div class="alert-time">{{ formatDateTime(alert.created_at) }}</div>
              </div>
            </template>
          </el-alert>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  VideoPlay,
  Clock,
  SuccessFilled,
  Warning
} from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import { useProjectStore } from '@/stores/project'
import { formatDateTime, formatDuration } from '@/utils'
import * as echarts from 'echarts'

const router = useRouter()
const workflowStore = useWorkflowStore()
const projectStore = useProjectStore()

const loading = ref(false)
const selectedProject = ref('')
const timeRange = ref('24h')
const executionChartType = ref('count')
const resourceType = ref('cpu')
const autoRefreshLogs = ref(true)

const projects = ref([])
const systemStats = ref({})
const activeWorkflows = ref([])
const logs = ref([])
const alerts = ref([])

const executionChart = ref(null)
const statusChart = ref(null)
const resourceChart = ref(null)

let executionChartInstance = null
let statusChartInstance = null
let resourceChartInstance = null
let refreshTimer = null
let logTimer = null

/**
 * 获取监控数据
 */
const fetchMonitoringData = async () => {
  try {
    loading.value = true
    
    // 获取系统统计
    systemStats.value = await workflowStore.getSystemStats({
      project_id: selectedProject.value,
      time_range: timeRange.value
    })
    
    // 获取活跃工作流
    const workflowResult = await workflowStore.getActiveWorkflows({
      project_id: selectedProject.value,
      page: 1,
      size: 10
    })
    activeWorkflows.value = workflowResult.items || []
    
    // 获取系统警告
    alerts.value = await workflowStore.getSystemAlerts({
      project_id: selectedProject.value
    })
    
    // 更新图表
    await nextTick()
    updateCharts()
    
  } catch (error) {
    ElMessage.error('获取监控数据失败')
    console.error('获取监控数据失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 获取项目列表
 */
const fetchProjects = async () => {
  try {
    const result = await projectStore.getProjects({ page: 1, size: 100 })
    projects.value = result.items || []
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

/**
 * 获取实时日志
 */
const fetchLogs = async () => {
  try {
    const result = await workflowStore.getSystemLogs({
      project_id: selectedProject.value,
      page: 1,
      size: 50
    })
    logs.value = result.items || []
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

/**
 * 更新图表
 */
const updateCharts = async () => {
  await updateExecutionChart()
  await updateStatusChart()
  await updateResourceChart()
}

/**
 * 更新执行趋势图
 */
const updateExecutionChart = async () => {
  if (!executionChart.value) return
  
  if (!executionChartInstance) {
    executionChartInstance = echarts.init(executionChart.value)
  }
  
  try {
    const data = await workflowStore.getExecutionTrend({
      project_id: selectedProject.value,
      time_range: timeRange.value,
      type: executionChartType.value
    })
    
    const option = {
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['成功', '失败', '取消']
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.labels || []
      },
      yAxis: {
        type: 'value'
      },
      series: [
        {
          name: '成功',
          type: 'line',
          data: data.success || [],
          smooth: true,
          itemStyle: { color: '#67C23A' }
        },
        {
          name: '失败',
          type: 'line',
          data: data.failed || [],
          smooth: true,
          itemStyle: { color: '#F56C6C' }
        },
        {
          name: '取消',
          type: 'line',
          data: data.cancelled || [],
          smooth: true,
          itemStyle: { color: '#E6A23C' }
        }
      ]
    }
    
    executionChartInstance.setOption(option)
  } catch (error) {
    console.error('更新执行趋势图失败:', error)
  }
}

/**
 * 更新状态分布图
 */
const updateStatusChart = async () => {
  if (!statusChart.value) return
  
  if (!statusChartInstance) {
    statusChartInstance = echarts.init(statusChart.value)
  }
  
  try {
    const data = await workflowStore.getStatusDistribution({
      project_id: selectedProject.value,
      time_range: timeRange.value
    })
    
    const option = {
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      legend: {
        orient: 'vertical',
        left: 'left'
      },
      series: [
        {
          name: '执行状态',
          type: 'pie',
          radius: '50%',
          data: [
            { value: data.success || 0, name: '成功', itemStyle: { color: '#67C23A' } },
            { value: data.failed || 0, name: '失败', itemStyle: { color: '#F56C6C' } },
            { value: data.running || 0, name: '运行中', itemStyle: { color: '#409EFF' } },
            { value: data.pending || 0, name: '等待中', itemStyle: { color: '#E6A23C' } },
            { value: data.cancelled || 0, name: '已取消', itemStyle: { color: '#909399' } }
          ],
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)'
            }
          }
        }
      ]
    }
    
    statusChartInstance.setOption(option)
  } catch (error) {
    console.error('更新状态分布图失败:', error)
  }
}

/**
 * 更新资源监控图
 */
const updateResourceChart = async () => {
  if (!resourceChart.value) return
  
  if (!resourceChartInstance) {
    resourceChartInstance = echarts.init(resourceChart.value)
  }
  
  try {
    const data = await workflowStore.getResourceUsage({
      type: resourceType.value,
      time_range: timeRange.value
    })
    
    const option = {
      tooltip: {
        trigger: 'axis',
        formatter: function (params) {
          return `${params[0].name}<br/>${params[0].seriesName}: ${params[0].value}%`
        }
      },
      grid: {
        left: '3%',
        right: '4%',
        bottom: '3%',
        containLabel: true
      },
      xAxis: {
        type: 'category',
        data: data.labels || []
      },
      yAxis: {
        type: 'value',
        max: 100,
        axisLabel: {
          formatter: '{value}%'
        }
      },
      series: [
        {
          name: resourceType.value.toUpperCase() + '使用率',
          type: 'line',
          data: data.values || [],
          smooth: true,
          areaStyle: {
            opacity: 0.3
          },
          itemStyle: {
            color: resourceType.value === 'cpu' ? '#409EFF' : 
                   resourceType.value === 'memory' ? '#67C23A' : '#E6A23C'
          }
        }
      ]
    }
    
    resourceChartInstance.setOption(option)
  } catch (error) {
    console.error('更新资源监控图失败:', error)
  }
}

/**
 * 刷新数据
 */
const refreshData = () => {
  fetchMonitoringData()
  fetchLogs()
}

/**
 * 停止工作流
 */
const stopWorkflow = async (workflowId) => {
  try {
    await workflowStore.stopWorkflow(workflowId)
    ElMessage.success('工作流已停止')
    refreshData()
  } catch (error) {
    ElMessage.error('停止工作流失败')
  }
}

/**
 * 查看工作流详情
 */
const viewWorkflowDetail = (workflowId) => {
  router.push(`/workflows/${workflowId}`)
}

/**
 * 查看所有工作流
 */
const viewAllWorkflows = () => {
  router.push('/workflows')
}

/**
 * 清除所有警告
 */
const clearAlerts = async () => {
  try {
    await workflowStore.clearSystemAlerts()
    alerts.value = []
    ElMessage.success('警告已清除')
  } catch (error) {
    ElMessage.error('清除警告失败')
  }
}

/**
 * 移除单个警告
 */
const removeAlert = async (alertId) => {
  try {
    await workflowStore.removeSystemAlert(alertId)
    alerts.value = alerts.value.filter(alert => alert.id !== alertId)
  } catch (error) {
    ElMessage.error('移除警告失败')
  }
}

/**
 * 计算成功率
 */
const calculateSuccessRate = () => {
  const total = systemStats.value.total_executions || 0
  const success = systemStats.value.success_executions || 0
  return total > 0 ? Math.round((success / total) * 100) : 0
}

/**
 * 格式化状态
 */
const formatStatus = (status) => {
  const statuses = {
    running: '运行中',
    pending: '等待中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return statuses[status] || status
}

/**
 * 获取状态颜色
 */
const getStatusColor = (status) => {
  const colors = {
    running: 'primary',
    pending: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return colors[status] || ''
}

/**
 * 获取日志级别颜色
 */
const getLogLevelColor = (level) => {
  const colors = {
    error: 'danger',
    warn: 'warning',
    info: 'primary',
    debug: 'info'
  }
  return colors[level] || ''
}

/**
 * 格式化时间
 */
const formatTime = (timestamp) => {
  return new Date(timestamp).toLocaleTimeString()
}

/**
 * 启动自动刷新
 */
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    fetchMonitoringData()
  }, 30000) // 30秒刷新一次
  
  if (autoRefreshLogs.value) {
    logTimer = setInterval(() => {
      fetchLogs()
    }, 5000) // 5秒刷新一次日志
  }
}

/**
 * 停止自动刷新
 */
const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
  if (logTimer) {
    clearInterval(logTimer)
    logTimer = null
  }
}

/**
 * 窗口大小变化时重新调整图表
 */
const handleResize = () => {
  if (executionChartInstance) executionChartInstance.resize()
  if (statusChartInstance) statusChartInstance.resize()
  if (resourceChartInstance) resourceChartInstance.resize()
}

// 监听参数变化
watch([selectedProject, timeRange], () => {
  fetchMonitoringData()
})

watch(executionChartType, () => {
  updateExecutionChart()
})

watch(resourceType, () => {
  updateResourceChart()
})

watch(autoRefreshLogs, (newValue) => {
  if (newValue) {
    logTimer = setInterval(() => {
      fetchLogs()
    }, 5000)
  } else {
    if (logTimer) {
      clearInterval(logTimer)
      logTimer = null
    }
  }
})

onMounted(async () => {
  await fetchProjects()
  await fetchMonitoringData()
  await fetchLogs()
  startAutoRefresh()
  
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  stopAutoRefresh()
  
  if (executionChartInstance) {
    executionChartInstance.dispose()
  }
  if (statusChartInstance) {
    statusChartInstance.dispose()
  }
  if (resourceChartInstance) {
    resourceChartInstance.dispose()
  }
  
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.monitoring {
  padding: 20px;
}

.monitoring-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.monitoring-header h2 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  align-items: center;
}

.overview-section {
  margin-bottom: 20px;
}

.overview-card {
  height: 100px;
}

.overview-item {
  display: flex;
  align-items: center;
  gap: 16px;
  height: 100%;
}

.overview-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  border-radius: 12px;
}

.overview-icon.running {
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
}

.overview-icon.pending {
  background: var(--el-color-warning-light-8);
  color: var(--el-color-warning);
}

.overview-icon.success {
  background: var(--el-color-success-light-8);
  color: var(--el-color-success);
}

.overview-icon.error {
  background: var(--el-color-danger-light-8);
  color: var(--el-color-danger);
}

.overview-info {
  flex: 1;
}

.overview-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.overview-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.chart-card,
.table-card,
.log-card,
.alert-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-container {
  height: 300px;
  width: 100%;
}

.log-card {
  height: 400px;
}

.log-container {
  height: 320px;
  overflow: hidden;
}

.empty-logs {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.log-list {
  height: 100%;
  overflow-y: auto;
}

.log-item {
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.log-item:last-child {
  border-bottom: none;
}

.log-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-bottom: 2px;
}

.log-level {
  margin-bottom: 4px;
}

.log-message {
  font-size: 12px;
  color: var(--el-text-color-regular);
  line-height: 1.4;
  word-break: break-all;
}

.alert-list {
  max-height: 300px;
  overflow-y: auto;
}

.alert-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.alert-message {
  flex: 1;
}

.alert-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-left: 12px;
}
</style>