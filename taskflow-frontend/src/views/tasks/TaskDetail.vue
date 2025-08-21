<template>
  <div class="task-detail">
    <el-page-header @back="goBack" :content="task?.name || '任务详情'">
      <template #extra>
        <el-space>
          <el-button @click="executeTask" type="primary" :loading="executing">
            <el-icon><VideoPlay /></el-icon>
            执行任务
          </el-button>
          <el-dropdown @command="handleCommand">
            <el-button>
              更多操作
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit">
                  <el-icon><Edit /></el-icon>
                  编辑任务
                </el-dropdown-item>
                <el-dropdown-item command="clone">
                  <el-icon><CopyDocument /></el-icon>
                  克隆任务
                </el-dropdown-item>
                <el-dropdown-item command="export">
                  <el-icon><Download /></el-icon>
                  导出配置
                </el-dropdown-item>
                <el-dropdown-item command="delete" divided>
                  <el-icon><Delete /></el-icon>
                  删除任务
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-space>
      </template>
    </el-page-header>

    <div class="detail-content" v-loading="loading">
      <el-row :gutter="20" v-if="task">
        <el-col :span="16">
          <!-- 基本信息 -->
          <el-card class="info-card">
            <template #header>
              <span>基本信息</span>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="任务名称">
                {{ task.name }}
              </el-descriptions-item>
              <el-descriptions-item label="任务ID">
                {{ task.id }}
              </el-descriptions-item>
              <el-descriptions-item label="所属项目">
                <el-link @click="goToProject(task.project_id)" type="primary">
                  {{ task.project_name }}
                </el-link>
              </el-descriptions-item>
              <el-descriptions-item label="任务类型">
                <el-tag :type="getTaskTypeColor(task.task_type)">{{ formatTaskType(task.task_type) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusColor(task.status)">{{ formatStatus(task.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="优先级">
                <el-tag :type="getPriorityColor(task.priority)">{{ formatPriority(task.priority) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="超时时间">
                {{ task.timeout }}秒
              </el-descriptions-item>
              <el-descriptions-item label="重试次数">
                {{ task.retry_count }}次
              </el-descriptions-item>
              <el-descriptions-item label="创建时间" :span="2">
                {{ formatDateTime(task.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间" :span="2">
                {{ formatDateTime(task.updated_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="任务描述" :span="2">
                {{ task.description || '暂无描述' }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div v-if="task.tags && task.tags.length > 0" class="tags-section">
              <h4>标签</h4>
              <el-tag
                v-for="tag in task.tags"
                :key="tag"
                style="margin-right: 8px; margin-bottom: 8px"
              >
                {{ tag }}
              </el-tag>
            </div>
          </el-card>

          <!-- 任务配置 -->
          <el-card class="info-card">
            <template #header>
              <span>任务配置</span>
            </template>
            
            <!-- HTTP请求配置 -->
            <div v-if="task.task_type === 'http'">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="请求方法">
                  <el-tag>{{ task.config.method }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="请求URL">
                  <el-link :href="task.config.url" target="_blank" type="primary">
                    {{ task.config.url }}
                  </el-link>
                </el-descriptions-item>
                <el-descriptions-item label="请求头" v-if="task.config.headers && task.config.headers.length > 0">
                  <div class="config-list">
                    <div v-for="header in task.config.headers" :key="header.key" class="config-item">
                      <strong>{{ header.key }}:</strong> {{ header.value }}
                    </div>
                  </div>
                </el-descriptions-item>
                <el-descriptions-item label="请求体" v-if="task.config.body">
                  <el-input
                    :model-value="task.config.body"
                    type="textarea"
                    :rows="6"
                    readonly
                  />
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <!-- 脚本执行配置 -->
            <div v-if="task.task_type === 'script'">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="脚本类型">
                  <el-tag>{{ task.config.script_type }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="环境变量" v-if="task.config.env_vars && task.config.env_vars.length > 0">
                  <div class="config-list">
                    <div v-for="env in task.config.env_vars" :key="env.key" class="config-item">
                      <strong>{{ env.key }}:</strong> {{ env.value }}
                    </div>
                  </div>
                </el-descriptions-item>
                <el-descriptions-item label="脚本内容">
                  <el-input
                    :model-value="task.config.script_content"
                    type="textarea"
                    :rows="10"
                    readonly
                  />
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <!-- 数据处理配置 -->
            <div v-if="task.task_type === 'data'">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="数据源">
                  {{ task.config.data_source }}
                </el-descriptions-item>
                <el-descriptions-item label="输出格式">
                  <el-tag>{{ task.config.output_format }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="处理规则">
                  <el-input
                    :model-value="task.config.processing_rules"
                    type="textarea"
                    :rows="6"
                    readonly
                  />
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <!-- 文件操作配置 -->
            <div v-if="task.task_type === 'file'">
              <el-descriptions :column="1" border>
                <el-descriptions-item label="操作类型">
                  <el-tag>{{ task.config.operation }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="源路径">
                  {{ task.config.source_path }}
                </el-descriptions-item>
                <el-descriptions-item label="目标路径" v-if="task.config.target_path">
                  {{ task.config.target_path }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- 执行统计 -->
          <el-card class="info-card">
            <template #header>
              <span>执行统计</span>
            </template>
            
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ task.execution_count || 0 }}</div>
                <div class="stat-label">总执行次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value success">{{ task.success_count || 0 }}</div>
                <div class="stat-label">成功次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value error">{{ task.failure_count || 0 }}</div>
                <div class="stat-label">失败次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ calculateSuccessRate() }}%</div>
                <div class="stat-label">成功率</div>
              </div>
            </div>
            
            <el-divider />
            
            <el-descriptions :column="1" size="small">
              <el-descriptions-item label="最后执行时间">
                {{ task.last_execution_time ? formatDateTime(task.last_execution_time) : '从未执行' }}
              </el-descriptions-item>
              <el-descriptions-item label="平均执行时长">
                {{ task.avg_execution_time ? `${task.avg_execution_time}秒` : '暂无数据' }}
              </el-descriptions-item>
              <el-descriptions-item label="失败处理">
                {{ formatFailureAction(task.failure_action) }}
              </el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 最近执行记录 -->
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>最近执行记录</span>
                <el-button text type="primary" @click="viewAllExecutions">
                  查看全部
                </el-button>
              </div>
            </template>
            
            <div v-if="executions.length === 0" class="empty-state">
              <el-empty description="暂无执行记录" :image-size="80" />
            </div>
            
            <div v-else class="execution-list">
              <div
                v-for="execution in executions"
                :key="execution.id"
                class="execution-item"
                @click="viewExecutionDetail(execution.id)"
              >
                <div class="execution-header">
                  <el-tag :type="getExecutionStatusColor(execution.status)" size="small">
                    {{ formatExecutionStatus(execution.status) }}
                  </el-tag>
                  <span class="execution-time">{{ formatDateTime(execution.created_at) }}</span>
                </div>
                <div class="execution-info">
                  <div>执行时长: {{ calculateDuration(execution.start_time, execution.end_time) }}</div>
                  <div v-if="execution.error_message" class="error-message">
                    错误: {{ execution.error_message }}
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  VideoPlay,
  ArrowDown,
  Edit,
  CopyDocument,
  Download,
  Delete
} from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { formatDateTime, downloadFile } from '@/utils'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()

const loading = ref(false)
const executing = ref(false)
const task = ref(null)
const executions = ref([])

/**
 * 获取任务详情
 */
const fetchTaskDetail = async () => {
  try {
    loading.value = true
    const taskId = route.params.id
    task.value = await taskStore.getTaskDetail(taskId)
    await fetchRecentExecutions()
  } catch (error) {
    ElMessage.error('获取任务详情失败')
    console.error('获取任务详情失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 获取最近执行记录
 */
const fetchRecentExecutions = async () => {
  try {
    const taskId = route.params.id
    const result = await taskStore.getTaskExecutions(taskId, { page: 1, size: 5 })
    executions.value = result.items || []
  } catch (error) {
    console.error('获取执行记录失败:', error)
  }
}

/**
 * 执行任务
 */
const executeTask = async () => {
  try {
    executing.value = true
    await taskStore.executeTask(task.value.id)
    ElMessage.success('任务执行成功')
    await fetchRecentExecutions()
  } catch (error) {
    ElMessage.error('任务执行失败')
  } finally {
    executing.value = false
  }
}

/**
 * 处理更多操作命令
 */
const handleCommand = async (command) => {
  switch (command) {
    case 'edit':
      router.push(`/tasks/${task.value.id}/edit`)
      break
    case 'clone':
      await cloneTask()
      break
    case 'export':
      await exportTask()
      break
    case 'delete':
      await deleteTask()
      break
  }
}

/**
 * 克隆任务
 */
const cloneTask = async () => {
  try {
    const clonedTask = {
      ...task.value,
      name: `${task.value.name} - 副本`,
      id: undefined,
      created_at: undefined,
      updated_at: undefined
    }
    await taskStore.createTask(clonedTask)
    ElMessage.success('任务克隆成功')
    router.push('/tasks')
  } catch (error) {
    ElMessage.error('任务克隆失败')
  }
}

/**
 * 导出任务配置
 */
const exportTask = () => {
  const exportData = {
    name: task.value.name,
    description: task.value.description,
    task_type: task.value.task_type,
    priority: task.value.priority,
    timeout: task.value.timeout,
    retry_count: task.value.retry_count,
    config: task.value.config,
    tags: task.value.tags
  }
  
  const content = JSON.stringify(exportData, null, 2)
  const filename = `task_${task.value.name}_${Date.now()}.json`
  downloadFile(content, filename, 'application/json')
}

/**
 * 删除任务
 */
const deleteTask = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个任务吗？删除后无法恢复。',
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await taskStore.deleteTask(task.value.id)
    ElMessage.success('任务删除成功')
    router.push('/tasks')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('任务删除失败')
    }
  }
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 跳转到项目详情
 */
const goToProject = (projectId) => {
  router.push(`/projects/${projectId}`)
}

/**
 * 查看所有执行记录
 */
const viewAllExecutions = () => {
  router.push(`/tasks/${task.value.id}/executions`)
}

/**
 * 查看执行详情
 */
const viewExecutionDetail = (executionId) => {
  router.push(`/tasks/${task.value.id}/executions/${executionId}`)
}

/**
 * 计算成功率
 */
const calculateSuccessRate = () => {
  if (!task.value || !task.value.execution_count) return 0
  return Math.round((task.value.success_count / task.value.execution_count) * 100)
}

/**
 * 计算执行时长
 */
const calculateDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return '未知'
  const duration = new Date(endTime) - new Date(startTime)
  return `${Math.round(duration / 1000)}秒`
}

/**
 * 格式化任务类型
 */
const formatTaskType = (type) => {
  const types = {
    http: 'HTTP请求',
    script: '脚本执行',
    data: '数据处理',
    file: '文件操作'
  }
  return types[type] || type
}

/**
 * 获取任务类型颜色
 */
const getTaskTypeColor = (type) => {
  const colors = {
    http: 'primary',
    script: 'success',
    data: 'warning',
    file: 'info'
  }
  return colors[type] || ''
}

/**
 * 格式化状态
 */
const formatStatus = (status) => {
  const statuses = {
    draft: '草稿',
    active: '激活',
    inactive: '停用'
  }
  return statuses[status] || status
}

/**
 * 获取状态颜色
 */
const getStatusColor = (status) => {
  const colors = {
    draft: 'info',
    active: 'success',
    inactive: 'danger'
  }
  return colors[status] || ''
}

/**
 * 格式化优先级
 */
const formatPriority = (priority) => {
  const priorities = {
    low: '低',
    medium: '中',
    high: '高'
  }
  return priorities[priority] || priority
}

/**
 * 获取优先级颜色
 */
const getPriorityColor = (priority) => {
  const colors = {
    low: 'info',
    medium: 'warning',
    high: 'danger'
  }
  return colors[priority] || ''
}

/**
 * 格式化失败处理方式
 */
const formatFailureAction = (action) => {
  const actions = {
    stop: '停止执行',
    continue: '继续执行',
    retry: '重试'
  }
  return actions[action] || action
}

/**
 * 格式化执行状态
 */
const formatExecutionStatus = (status) => {
  const statuses = {
    pending: '等待中',
    running: '执行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return statuses[status] || status
}

/**
 * 获取执行状态颜色
 */
const getExecutionStatusColor = (status) => {
  const colors = {
    pending: 'info',
    running: 'warning',
    success: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return colors[status] || ''
}

onMounted(() => {
  fetchTaskDetail()
})
</script>

<style scoped>
.task-detail {
  padding: 20px;
}

.detail-content {
  margin-top: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tags-section {
  margin-top: 20px;
}

.tags-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.config-list {
  background: var(--el-fill-color-lighter);
  border-radius: 4px;
  padding: 12px;
}

.config-item {
  margin-bottom: 8px;
  font-family: monospace;
  font-size: 13px;
}

.config-item:last-child {
  margin-bottom: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.stat-value.success {
  color: var(--el-color-success);
}

.stat-value.error {
  color: var(--el-color-danger);
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.empty-state {
  text-align: center;
  padding: 20px;
}

.execution-list {
  max-height: 300px;
  overflow-y: auto;
}

.execution-item {
  padding: 12px;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.execution-item:hover {
  border-color: var(--el-color-primary);
  background: var(--el-fill-color-lighter);
}

.execution-item:last-child {
  margin-bottom: 0;
}

.execution-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.execution-time {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.execution-info {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.execution-info > div {
  margin-bottom: 4px;
}

.execution-info > div:last-child {
  margin-bottom: 0;
}

.error-message {
  color: var(--el-color-danger);
  word-break: break-all;
}
</style>