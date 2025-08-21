<template>
  <div class="workflow-detail">
    <el-page-header @back="goBack" :content="workflow?.name || '工作流详情'">
      <template #extra>
        <el-space>
          <el-button type="primary" @click="executeWorkflow" :loading="executing">
            <el-icon><VideoPlay /></el-icon>
            执行工作流
          </el-button>
          <el-button @click="editWorkflow">
            <el-icon><Edit /></el-icon>
            编辑
          </el-button>
          <el-button @click="cloneWorkflow">
            <el-icon><CopyDocument /></el-icon>
            克隆
          </el-button>
          <el-dropdown @command="handleCommand">
            <el-button>
              更多操作
              <el-icon class="el-icon--right"><ArrowDown /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="export">导出配置</el-dropdown-item>
                <el-dropdown-item command="delete" divided>删除工作流</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </el-space>
      </template>
    </el-page-header>

    <div class="detail-content" v-loading="loading">
      <el-row :gutter="20">
        <el-col :span="16">
          <!-- 工作流信息 -->
          <el-card class="info-card">
            <template #header>
              <span>基本信息</span>
            </template>
            <el-descriptions :column="2" border>
              <el-descriptions-item label="工作流名称">{{ workflow?.name }}</el-descriptions-item>
              <el-descriptions-item label="所属项目">{{ workflow?.project_name }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(workflow?.status)">{{ getStatusText(workflow?.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="优先级">
                <el-tag :type="getPriorityType(workflow?.priority)">{{ getPriorityText(workflow?.priority) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">{{ formatTime(workflow?.created_at) }}</el-descriptions-item>
              <el-descriptions-item label="更新时间">{{ formatTime(workflow?.updated_at) }}</el-descriptions-item>
              <el-descriptions-item label="描述" :span="2">{{ workflow?.description || '暂无描述' }}</el-descriptions-item>
            </el-descriptions>
          </el-card>

          <!-- 任务列表 -->
          <el-card class="tasks-card">
            <template #header>
              <span>任务列表 ({{ workflow?.tasks?.length || 0 }})</span>
            </template>
            <div class="task-flow">
              <div v-for="(task, index) in workflow?.tasks" :key="task.id" class="task-item">
                <div class="task-card">
                  <div class="task-header">
                    <span class="task-name">{{ task.name }}</span>
                    <el-tag size="small" :type="getTaskStatusType(task.status)">{{ getTaskStatusText(task.status) }}</el-tag>
                  </div>
                  <div class="task-content">
                    <p class="task-description">{{ task.description }}</p>
                    <div class="task-meta">
                      <span>类型: {{ task.task_type }}</span>
                      <span>超时: {{ task.timeout }}s</span>
                    </div>
                  </div>
                </div>
                <div v-if="index < workflow.tasks.length - 1" class="task-arrow">
                  <el-icon><ArrowRight /></el-icon>
                </div>
              </div>
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
                <div class="stat-value">{{ stats.total_executions }}</div>
                <div class="stat-label">总执行次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value success">{{ stats.success_executions }}</div>
                <div class="stat-label">成功次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value danger">{{ stats.failed_executions }}</div>
                <div class="stat-label">失败次数</div>
              </div>
              <div class="stat-item">
                <div class="stat-value warning">{{ stats.running_executions }}</div>
                <div class="stat-label">运行中</div>
              </div>
            </div>
          </el-card>

          <!-- 最近执行 -->
          <el-card class="executions-card">
            <template #header>
              <div class="card-header">
                <span>最近执行</span>
                <el-button text @click="viewAllExecutions">查看全部</el-button>
              </div>
            </template>
            <div class="execution-list">
              <div v-for="execution in recentExecutions" :key="execution.id" class="execution-item" @click="viewExecution(execution.id)">
                <div class="execution-info">
                  <div class="execution-status">
                    <el-tag size="small" :type="getExecutionStatusType(execution.status)">{{ getExecutionStatusText(execution.status) }}</el-tag>
                  </div>
                  <div class="execution-time">{{ formatTime(execution.created_at) }}</div>
                </div>
                <div class="execution-duration">
                  {{ execution.duration ? `${execution.duration}s` : '-' }}
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
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { VideoPlay, Edit, CopyDocument, ArrowDown, ArrowRight } from '@element-plus/icons-vue'
import { useWorkflowStore } from '@/stores/workflow'
import { formatTime } from '@/utils'

const route = useRoute()
const router = useRouter()
const workflowStore = useWorkflowStore()

const loading = ref(false)
const executing = ref(false)
const workflow = ref(null)
const stats = ref({
  total_executions: 0,
  success_executions: 0,
  failed_executions: 0,
  running_executions: 0
})
const recentExecutions = ref([])

/**
 * 获取工作流详情
 */
const fetchWorkflowDetail = async () => {
  try {
    loading.value = true
    const id = route.params.id
    workflow.value = await workflowStore.getWorkflowDetail(id)
    
    // 获取执行统计
    stats.value = await workflowStore.getWorkflowStats(id)
    
    // 获取最近执行记录
    recentExecutions.value = await workflowStore.getWorkflowExecutions(id, { limit: 5 })
  } catch (error) {
    ElMessage.error('获取工作流详情失败')
  } finally {
    loading.value = false
  }
}

/**
 * 返回上一页
 */
const goBack = () => {
  router.back()
}

/**
 * 执行工作流
 */
const executeWorkflow = async () => {
  try {
    executing.value = true
    await workflowStore.executeWorkflow(workflow.value.id)
    ElMessage.success('工作流执行成功')
    // 刷新执行记录
    fetchWorkflowDetail()
  } catch (error) {
    ElMessage.error('工作流执行失败')
  } finally {
    executing.value = false
  }
}

/**
 * 编辑工作流
 */
const editWorkflow = () => {
  router.push(`/workflows/${workflow.value.id}/edit`)
}

/**
 * 克隆工作流
 */
const cloneWorkflow = async () => {
  try {
    await workflowStore.cloneWorkflow(workflow.value.id)
    ElMessage.success('工作流克隆成功')
    router.push('/workflows')
  } catch (error) {
    ElMessage.error('工作流克隆失败')
  }
}

/**
 * 处理下拉菜单命令
 */
const handleCommand = async (command) => {
  switch (command) {
    case 'export':
      // 导出配置逻辑
      ElMessage.info('导出功能开发中')
      break
    case 'delete':
      await deleteWorkflow()
      break
  }
}

/**
 * 删除工作流
 */
const deleteWorkflow = async () => {
  try {
    await ElMessageBox.confirm('确定要删除这个工作流吗？', '确认删除', {
      type: 'warning'
    })
    
    await workflowStore.deleteWorkflow(workflow.value.id)
    ElMessage.success('工作流删除成功')
    router.push('/workflows')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('工作流删除失败')
    }
  }
}

/**
 * 查看所有执行记录
 */
const viewAllExecutions = () => {
  router.push(`/workflows/${workflow.value.id}/executions`)
}

/**
 * 查看执行详情
 */
const viewExecution = (executionId) => {
  router.push(`/workflows/${workflow.value.id}/executions/${executionId}`)
}

/**
 * 获取状态类型
 */
const getStatusType = (status) => {
  const statusMap = {
    'active': 'success',
    'inactive': 'info',
    'draft': 'warning'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    'active': '激活',
    'inactive': '未激活',
    'draft': '草稿'
  }
  return statusMap[status] || status
}

/**
 * 获取优先级类型
 */
const getPriorityType = (priority) => {
  const priorityMap = {
    'high': 'danger',
    'medium': 'warning',
    'low': 'info'
  }
  return priorityMap[priority] || 'info'
}

/**
 * 获取优先级文本
 */
const getPriorityText = (priority) => {
  const priorityMap = {
    'high': '高',
    'medium': '中',
    'low': '低'
  }
  return priorityMap[priority] || priority
}

/**
 * 获取任务状态类型
 */
const getTaskStatusType = (status) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning',
    'success': 'success',
    'failed': 'danger'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取任务状态文本
 */
const getTaskStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'success': '成功',
    'failed': '失败'
  }
  return statusMap[status] || status
}

/**
 * 获取执行状态类型
 */
const getExecutionStatusType = (status) => {
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
 * 获取执行状态文本
 */
const getExecutionStatusText = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '运行中',
    'success': '成功',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

onMounted(() => {
  fetchWorkflowDetail()
})
</script>

<style scoped>
.workflow-detail {
  padding: 20px;
}

.detail-content {
  margin-top: 20px;
}

.info-card,
.tasks-card,
.stats-card,
.executions-card {
  margin-bottom: 20px;
}

.task-flow {
  display: flex;
  align-items: center;
  overflow-x: auto;
  padding: 20px 0;
}

.task-item {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.task-card {
  width: 200px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  padding: 12px;
  background: var(--el-bg-color);
}

.task-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.task-name {
  font-weight: 500;
  font-size: 14px;
}

.task-content {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.task-description {
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.task-meta {
  display: flex;
  justify-content: space-between;
}

.task-arrow {
  margin: 0 15px;
  color: var(--el-text-color-placeholder);
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

.execution-list {
  max-height: 300px;
  overflow-y: auto;
}

.execution-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  cursor: pointer;
  transition: background-color 0.2s;
}

.execution-item:hover {
  background-color: var(--el-fill-color-lighter);
}

.execution-item:last-child {
  border-bottom: none;
}

.execution-info {
  flex: 1;
}

.execution-time {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.execution-duration {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
</style>