<template>
  <div class="execution-detail">
    <el-page-header @back="goBack" :content="`执行详情 #${executionId}`">
      <template #extra>
        <el-space>
          <el-button v-if="execution?.status === 'running'" type="danger" @click="cancelExecution">
            <el-icon><Close /></el-icon>
            取消执行
          </el-button>
          <el-button v-if="['failed', 'cancelled'].includes(execution?.status)" type="primary" @click="retryExecution">
            <el-icon><Refresh /></el-icon>
            重新执行
          </el-button>
          <el-button @click="downloadLogs">
            <el-icon><Download /></el-icon>
            下载日志
          </el-button>
        </el-space>
      </template>
    </el-page-header>

    <div class="detail-content" v-loading="loading">
      <el-row :gutter="20">
        <el-col :span="16">
          <!-- 执行信息 -->
          <el-card class="info-card">
            <template #header>
              <span>执行信息</span>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="执行ID">{{ execution?.id }}</el-descriptions-item>
              <el-descriptions-item label="工作流名称">{{ execution?.workflow_name }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(execution?.status)">{{ getStatusText(execution?.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="触发方式">
                <el-tag size="small" :type="getTriggerType(execution?.trigger_type)">{{ getTriggerText(execution?.trigger_type) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="开始时间">{{ formatTime(execution?.started_at) }}</el-descriptions-item>
              <el-descriptions-item label="结束时间">{{ formatTime(execution?.finished_at) }}</el-descriptions-item>
              <el-descriptions-item label="执行时长">{{ getDuration(execution?.started_at, execution?.finished_at) }}</el-descriptions-item>
              <el-descriptions-item label="进度">
                <el-progress
                  :percentage="execution?.progress || 0"
                  :status="getProgressStatus(execution?.status)"
                  :stroke-width="8"
                />
              </el-descriptions-item>
              <el-descriptions-item v-if="execution?.error_message" label="错误信息" :span="2">
                <el-alert :title="execution.error_message" type="error" :closable="false" />
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 工作流图 -->
          <el-card class="graph-card">
            <template #header>
              <span>执行可视化</span>
            </template>
            <div id="execution-canvas" class="canvas"></div>
          </el-card>

          <!-- 任务执行详情 -->
          <el-card class="tasks-card">
            <template #header>
              <span>任务执行详情</span>
            </template>
            <div class="task-timeline">
              <el-timeline>
                <el-timeline-item
                  v-for="task in taskExecutions"
                  :key="task.id"
                  :type="getTaskTimelineType(task.status)"
                  :icon="getTaskIcon(task.status)"
                  :timestamp="formatTime(task.started_at)"
                >
                  <el-card class="task-execution-card">
                    <div class="task-header">
                      <div class="task-info">
                        <h4>{{ task.task_name }}</h4>
                        <el-tag size="small" :type="getStatusType(task.status)">{{ getStatusText(task.status) }}</el-tag>
                      </div>
                      <div class="task-duration">
                        {{ getDuration(task.started_at, task.finished_at) }}
                      </div>
                    </div>
                    
                    <div class="task-content">
                      <el-descriptions :column="1" size="small">
                        <el-descriptions-item label="任务类型">{{ task.task_type }}</el-descriptions-item>
                        <el-descriptions-item label="执行节点">{{ task.executor_node || '-' }}</el-descriptions-item>
                        <el-descriptions-item v-if="task.input_data" label="输入数据">
                          <el-button text @click="viewTaskData(task, 'input')">查看输入</el-button>
                        </el-descriptions-item>
                        <el-descriptions-item v-if="task.output_data" label="输出数据">
                          <el-button text @click="viewTaskData(task, 'output')">查看输出</el-button>
                        </el-descriptions-item>
                        <el-descriptions-item v-if="task.error_message" label="错误信息">
                          <el-alert :title="task.error_message" type="error" :closable="false" />
                        </el-descriptions-item>
                      </el-descriptions>
                    </div>
                    
                    <div class="task-actions">
                      <el-button size="small" text @click="viewTaskLogs(task)">查看日志</el-button>
                      <el-button v-if="task.status === 'failed'" size="small" text type="primary" @click="retryTask(task)">重试任务</el-button>
                    </div>
                  </el-card>
                </el-timeline-item>
              </el-timeline>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- 执行统计 -->
          <el-card class="stats-card">
            <template #header>
              <span>执行统计</span>
            </template>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ taskExecutions.length }}</div>
                <div class="stat-label">总任务数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value success">{{ getTaskCountByStatus('success') }}</div>
                <div class="stat-label">成功</div>
              </div>
              <div class="stat-item">
                <div class="stat-value danger">{{ getTaskCountByStatus('failed') }}</div>
                <div class="stat-label">失败</div>
              </div>
              <div class="stat-item">
                <div class="stat-value warning">{{ getTaskCountByStatus('running') }}</div>
                <div class="stat-label">运行中</div>
              </div>
            </div>
          </el-card>

          <!-- 实时日志 -->
          <el-card class="logs-card">
            <template #header>
              <div class="card-header">
                <span>实时日志</span>
                <el-button size="small" text @click="refreshLogs">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
            </template>
            <div class="logs-container">
              <div class="log-line" v-for="(log, index) in logs" :key="index" :class="getLogClass(log.level)">
                <span class="log-time">{{ formatTime(log.timestamp) }}</span>
                <span class="log-level">[{{ log.level }}]</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 任务数据查看对话框 -->
    <el-dialog v-model="dataDialogVisible" :title="dataDialogTitle" width="60%">
      <el-input
        v-model="taskData"
        type="textarea"
        :rows="15"
        readonly
        placeholder="暂无数据"
      />
    </el-dialog>

    <!-- 任务日志查看对话框 -->
    <el-dialog v-model="logsDialogVisible" :title="logsDialogTitle" width="80%">
      <div class="task-logs-container">
        <div class="log-line" v-for="(log, index) in taskLogs" :key="index" :class="getLogClass(log.level)">
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">[{{ log.level }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Close, Refresh, Download, VideoPlay, CircleCheck, CircleClose, Loading } from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import { formatTime } from '@/utils'
import { Graph } from '@antv/x6'

const route = useRoute()
const router = useRouter()
const workflowStore = useWorkflowStore()

const loading = ref(false)
const execution = ref(null)
const taskExecutions = ref([])
const logs = ref([])
const executionId = route.params.executionId
const workflowId = route.params.id

// 对话框相关
const dataDialogVisible = ref(false)
const dataDialogTitle = ref('')
const taskData = ref('')
const logsDialogVisible = ref(false)
const logsDialogTitle = ref('')
const taskLogs = ref([])

// 定时器
let logTimer = null

/**
 * 获取执行详情
 */
const fetchExecutionDetail = async (showLoading = true) => {
  try {
    if (showLoading) {
      loading.value = true
    }
    const config = showLoading ? {} : { loading: false }
    execution.value = await workflowStore.getWorkflowExecutionDetail(workflowId, executionId, config)
    taskExecutions.value = await workflowStore.getTaskExecutions(workflowId, executionId, config)
    
    // 加载工作流图数据
    const workflow = await workflowStore.getWorkflowDetail(workflowId)
    if (workflow && workflow.graph_data) {
      nextTick(() => {
        initGraph(workflow.graph_data)
        updateNodeStatus()
      })
    }
  } catch (error) {
    ElMessage.error('获取执行详情失败')
  } finally {
    if (showLoading) {
      loading.value = false
    }
  }
}

/**
 * 初始化图
 */
const initGraph = (graphData) => {
  const container = document.getElementById('execution-canvas')
  if (!container) return
  
  if (graph) {
    graph.dispose()
  }

  graph = new Graph({
    container: container,
    width: container.clientWidth,
    height: 300,
    grid: true,
    panning: { enabled: true, eventTypes: ['leftMouseDown', 'mouseWheel'] },
    mousewheel: { enabled: true, modifiers: 'ctrl', factor: 1.1, maxScale: 3, minScale: 0.3 },
    interacting: false,
    connecting: { 
      router: 'manhattan', 
      connector: { name: 'rounded', args: { radius: 8 } },
      anchor: 'center',
      connectionPoint: 'boundary'
    }
  })
  
  registerCustomNodes()
  
  if (graphData) {
    try {
      graph.fromJSON(JSON.parse(graphData))
      graph.zoomToFit({ padding: 20 })
    } catch (e) {
      console.error('Failed to parse graph data', e)
    }
  }
}

/**
 * 注册自定义节点
 */
const registerCustomNodes = () => {
  try {
    Graph.unregisterNode('workflow-node')
  } catch (e) {
    // ignore
  }
  
  Graph.registerNode('workflow-node', {
    inherit: 'rect',
    width: 180,
    height: 56,
    attrs: {
      body: {
        strokeWidth: 2,
        stroke: '#d9d9d9',
        fill: '#ffffff',
        rx: 8,
        ry: 8,
      },
      text: {
        fontSize: 13,
        fill: '#262626',
        fontWeight: 500,
        textAnchor: 'middle',
        textVerticalAnchor: 'middle',
        textWrap: {
          width: 160,
          height: 40,
          ellipsis: true
        }
      }
    }
  })
}

/**
 * 更新节点状态
 */
const updateNodeStatus = () => {
  if (!graph || !taskExecutions.value) return
  
  const statusColors = {
    'success': '#52c41a',
    'failed': '#f5222d',
    'running': '#1890ff',
    'pending': '#d9d9d9',
    'cancelled': '#d9d9d9'
  }

  taskExecutions.value.forEach(task => {
    // 尝试通过任务名称匹配节点
    const nodes = graph.getNodes()
    const node = nodes.find(n => n.getData()?.name === task.task_name)
    
    if (node) {
      const color = statusColors[task.status] || '#d9d9d9'
      node.attr('body/stroke', color)
      
      // 如果是运行中或失败，加粗边框
      if (['running', 'failed'].includes(task.status)) {
        node.attr('body/strokeWidth', 3)
      } else {
        node.attr('body/strokeWidth', 2)
      }
      
      // 可以考虑修改背景色变浅
      node.attr('body/fill', color + '10') // 10% 透明度
    }
  })
}

/**
 * 获取实时日志
 */
const fetchLogs = async () => {
  try {
    const result = await workflowStore.getExecutionLogs(workflowId, executionId, { limit: 100 })
    logs.value = result.logs || []
  } catch (error) {
    console.error('获取日志失败:', error)
  }
}

/**
 * 刷新日志
 */
const refreshLogs = () => {
  fetchLogs()
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 取消执行
 */
const cancelExecution = async () => {
  try {
    await ElMessageBox.confirm('确定要取消这次执行吗？', '确认取消', {
      type: 'warning'
    })
    
    await workflowStore.cancelExecution(executionId)
    ElMessage.success('执行已取消')
    fetchExecutionDetail()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('取消执行失败')
    }
  }
}

/**
 * 重新执行
 */
const retryExecution = async () => {
  try {
    const workflowId = route.params.id
    await workflowStore.executeWorkflow(workflowId)
    ElMessage.success('重新执行成功')
    router.push(`/workflows/${workflowId}/executions`)
  } catch (error) {
    ElMessage.error('重新执行失败')
  }
}

/**
 * 下载日志
 */
const downloadLogs = async () => {
  try {
    const result = await workflowStore.getExecutionLogs(workflowId, executionId, { format: 'file' })
    // 创建下载链接
    const blob = new Blob([result.content], { type: 'text/plain' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `execution_${executionId}_logs.txt`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('日志下载成功')
  } catch (error) {
    ElMessage.error('日志下载失败')
  }
}

/**
 * 查看任务数据
 */
const viewTaskData = (task, type) => {
  dataDialogTitle.value = `${task.task_name} - ${type === 'input' ? '输入数据' : '输出数据'}`
  taskData.value = JSON.stringify(task[`${type}_data`], null, 2)
  dataDialogVisible.value = true
}

/**
 * 查看任务日志
 */
const viewTaskLogs = async (task) => {
  try {
    logsDialogTitle.value = `${task.task_name} - 执行日志`
    const result = await workflowStore.getTaskLogs(task.id)
    taskLogs.value = result.logs || []
    logsDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取任务日志失败')
  }
}

/**
 * 重试任务
 */
const retryTask = async (task) => {
  try {
    await workflowStore.retryTask(task.id)
    ElMessage.success('任务重试成功')
    fetchExecutionDetail()
  } catch (error) {
    ElMessage.error('任务重试失败')
  }
}

/**
 * 获取状态类型
 */
const getStatusType = (status) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning',
    'success': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'success': '成功',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

/**
 * 获取触发类型
 */
const getTriggerType = (triggerType) => {
  const typeMap = {
    'manual': 'primary',
    'schedule': 'success',
    'event': 'warning'
  }
  return typeMap[triggerType] || 'info'
}

/**
 * 获取触发文本
 */
const getTriggerText = (triggerType) => {
  const typeMap = {
    'manual': '手动',
    'schedule': '定时',
    'event': '事件'
  }
  return typeMap[triggerType] || triggerType
}

/**
 * 获取进度状态
 */
const getProgressStatus = (status) => {
  const statusMap = {
    'success': 'success',
    'failed': 'exception',
    'cancelled': 'exception'
  }
  return statusMap[status]
}

/**
 * 获取任务时间线类型
 */
const getTaskTimelineType = (status) => {
  const typeMap = {
    'success': 'success',
    'failed': 'danger',
    'running': 'warning',
    'pending': 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取任务图标
 */
const getTaskIcon = (status) => {
  const iconMap = {
    'success': CircleCheck,
    'failed': CircleClose,
    'running': Loading,
    'pending': VideoPlay
  }
  return iconMap[status] || VideoPlay
}

/**
 * 根据状态获取任务数量
 */
const getTaskCountByStatus = (status) => {
  return taskExecutions.value.filter(task => task.status === status).length
}

/**
 * 获取日志样式类
 */
const getLogClass = (level) => {
  return `log-${level?.toLowerCase()}`
}

/**
 * 计算执行时长
 */
const getDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '-'
  
  const start = new Date(startTime)
  const end = new Date(endTime)
  const duration = Math.floor((end - start) / 1000)
  
  if (duration < 60) {
    return `${duration}秒`
  } else if (duration < 3600) {
    return `${Math.floor(duration / 60)}分${duration % 60}秒`
  } else {
    const hours = Math.floor(duration / 3600)
    const minutes = Math.floor((duration % 3600) / 60)
    return `${hours}时${minutes}分`
  }
}

/**
 * 监听执行状态更新图表
 */
const handlePollingUpdate = async () => {
  await fetchExecutionDetail(false)
  updateNodeStatus()
}

/**
 * 启动日志轮询
 */
const startLogPolling = () => {
  if (execution.value?.status === 'running') {
    logTimer = setInterval(() => {
      fetchLogs()
      handlePollingUpdate()
    }, 5000)
  }
}

/**
 * 停止日志轮询
 */
const stopLogPolling = () => {
  if (logTimer) {
    clearInterval(logTimer)
    logTimer = null
  }
}

onMounted(async () => {
  await fetchExecutionDetail()
  await fetchLogs()
  startLogPolling()
})

onUnmounted(() => {
  stopLogPolling()
})
</script>

<style scoped>
.execution-detail {
  padding: 20px;
}

.detail-content {
  margin-top: 20px;
}

.info-card,
.tasks-card,
.stats-card,
.logs-card {
  margin-bottom: 20px;
}

.task-timeline {
  padding: 20px 0;
}

.task-execution-card {
  margin-bottom: 10px;
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.task-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-info h4 {
  margin: 0;
  font-size: 16px;
}

.task-duration {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.task-content {
  margin-bottom: 12px;
}

.task-actions {
  display: flex;
  gap: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 4px;
}

.stat-value.success {
  color: var(--el-color-success);
}

.stat-value.danger {
  color: var(--el-color-danger);
}

.stat-value.warning {
  color: var(--el-color-warning);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logs-container,
.task-logs-container {
  max-height: 400px;
  overflow-y: auto;
  background: var(--el-fill-color-lighter);
  padding: 12px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}

.log-line {
  margin-bottom: 4px;
  word-break: break-all;
}

.log-time {
  color: var(--el-text-color-placeholder);
  margin-right: 8px;
}

.log-level {
  margin-right: 8px;
  font-weight: bold;
}

.log-message {
  color: var(--el-text-color-primary);
}

.log-info .log-level {
  color: var(--el-color-info);
}

.log-warning .log-level {
  color: var(--el-color-warning);
}

.log-error .log-level {
  color: var(--el-color-danger);
}

.log-debug .log-level {
  color: var(--el-text-color-placeholder);
}
</style>