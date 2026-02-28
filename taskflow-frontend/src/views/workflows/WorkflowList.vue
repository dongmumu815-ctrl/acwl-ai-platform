<template>
  <div class="workflow-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>工作流管理</h1>
        <p>管理和监控您的工作流程</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="$router.push('/workflows/create')">
          <el-icon><Plus /></el-icon>
          创建工作流
        </el-button>
      </div>
    </div>
    
    <!-- 搜索和筛选 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-content">
        <div class="filter-left">
          <el-input
            v-model="searchForm.keyword"
            placeholder="搜索工作流名称或描述"
            clearable
            style="width: 300px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          
          <el-select
            v-model="searchForm.status"
            placeholder="状态筛选"
            clearable
            style="width: 120px"
            @change="handleSearch"
          >
            <el-option label="草稿" value="draft" />
            <el-option label="活跃" value="active" />
            <el-option label="未激活" value="inactive" />
            <el-option label="已归档" value="archived" />
          </el-select>
          
          <el-select
            v-model="searchForm.project_id"
            placeholder="项目筛选"
            clearable
            style="width: 150px"
            @change="handleSearch"
          >
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </div>
        
        <div class="filter-right">
          <el-button @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </div>
      </div>
    </el-card>
    
    <!-- 工作流列表 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="workflowList"
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="工作流名称" min-width="200">
          <template #default="{ row }">
            <div class="workflow-name">
              <h4 @click="handleView(row)" class="name-link">{{ row.name }}</h4>
              <p class="description">{{ row.description || '暂无描述' }}</p>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="project_name" label="所属项目" width="150">
          <template #default="{ row }">
            <el-tag v-if="row.project_name" type="info" size="small">
              {{ row.project_name }}
            </el-tag>
            <span v-else class="text-muted">未分配</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="workflow_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.workflow_status)"
              size="small"
            >
              {{ getStatusText(row.workflow_status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="task_count" label="任务数量" width="100">
          <template #default="{ row }">
            <span class="task-count">{{ row.task_count || 0 }}</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="last_execution" label="最后执行" width="150">
          <template #default="{ row }">
            <span v-if="row.last_execution" class="execution-time">
              {{ formatTime(row.last_execution) }}
            </span>
            <span v-else class="text-muted">从未执行</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="150">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <div class="action-buttons">
              <el-tooltip content="查看详情" placement="top">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="handleView(row)"
                >
                  <el-icon><View /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="编辑" placement="top">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="handleEdit(row)"
                >
                  <el-icon><Edit /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip 
                :content="row.workflow_status === 'active' ? '停用' : '发布'" 
                placement="top"
              >
                <el-button
                  :type="row.workflow_status === 'active' ? 'warning' : 'success'"
                  link
                  size="small"
                  @click="handleStatusChange(row)"
                >
                  <el-icon><SwitchButton /></el-icon>
                </el-button>
              </el-tooltip>

              <el-tooltip content="调度管理" placement="top">
                <el-button
                  type="info"
                  link
                  size="small"
                  @click="handleSchedule(row)"
                >
                  <el-icon><Timer /></el-icon>
                </el-button>
              </el-tooltip>

              <el-tooltip content="执行" placement="top">
                <el-button
                  type="success"
                  link
                  size="small"
                  :disabled="row.workflow_status !== 'active'"
                  @click="handleExecute(row)"
                >
                  <el-icon><VideoPlay /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="克隆" placement="top">
                <el-button
                  type="warning"
                  link
                  size="small"
                  @click="handleClone(row)"
                >
                  <el-icon><CopyDocument /></el-icon>
                </el-button>
              </el-tooltip>
              
              <el-tooltip content="删除" placement="top">
                <el-button
                  type="danger"
                  link
                  size="small"
                  @click="handleDelete(row)"
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 批量操作 -->
      <div v-if="selectedWorkflows.length > 0" class="batch-actions">
        <div class="batch-info">
          已选择 {{ selectedWorkflows.length }} 个工作流
        </div>
        <div class="batch-buttons">
          <el-button type="success" @click="handleBatchExecute">
            <el-icon><VideoPlay /></el-icon>
            批量执行
          </el-button>
          <el-button type="primary" @click="handleBatchStatusChange('active')">
            <el-icon><SwitchButton /></el-icon>
            批量发布
          </el-button>
          <el-button type="warning" @click="handleBatchStatusChange('inactive')">
            <el-icon><SwitchButton /></el-icon>
            批量停用
          </el-button>
          <el-button type="danger" @click="handleBatchDelete">
            <el-icon><Delete /></el-icon>
            批量删除
          </el-button>
        </div>
      </div>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 调度管理抽屉 -->
    <el-drawer
      v-model="scheduleDrawerVisible"
      title="调度管理"
      size="50%"
      destroy-on-close
    >
      <div class="schedule-header" style="margin-bottom: 20px;">
        <el-button type="primary" @click="handleCreateSchedule">
          <el-icon><Plus /></el-icon> 创建调度
        </el-button>
      </div>
      
      <el-table :data="schedules" v-loading="schedulesLoading" style="width: 100%">
        <el-table-column prop="schedule_name" label="名称" />
        <el-table-column prop="schedule_type" label="类型">
          <template #default="{ row }">
            <el-tag size="small">{{ row.schedule_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="详情">
          <template #default="{ row }">
            <span v-if="row.schedule_type === 'cron'">{{ row.cron_expression }}</span>
            <span v-else-if="row.schedule_type === 'interval'">每 {{ row.interval_seconds }} 秒</span>
            <span v-else>--</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_enabled" label="状态">
          <template #default="{ row }">
            <el-tag :type="row.is_enabled ? 'success' : 'danger'" size="small">
              {{ row.is_enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button link type="primary" size="small" @click="handleEditSchedule(row)">编辑</el-button>
            <el-button link type="danger" size="small" @click="handleDeleteSchedule(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <WorkflowScheduleDialog
      v-model:visible="scheduleDialogVisible"
      :workflow-id="currentWorkflow?.id"
      :schedule-data="currentSchedule"
      @success="loadSchedules"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkflowStore, useProjectStore } from '@/stores'
import { ElMessage, ElMessageBox } from 'element-plus'
import { formatDistanceToNow, format } from 'date-fns'
import { zhCN } from 'date-fns/locale'
import {
  Plus, Search, Refresh, View, Edit, VideoPlay, 
  CopyDocument, Delete, Timer, SwitchButton
} from '@element-plus/icons-vue'
import WorkflowScheduleDialog from './components/WorkflowScheduleDialog.vue'

/**
 * 工作流列表页面组件
 */
const router = useRouter()
const workflowStore = useWorkflowStore()
const projectStore = useProjectStore()

// 加载状态
const loading = ref(false)

// 工作流列表
const workflowList = ref([])

// 项目列表
const projects = ref([])

// 选中的工作流
const selectedWorkflows = ref([])

// 调度相关状态
const scheduleDrawerVisible = ref(false)
const scheduleDialogVisible = ref(false)
const schedules = ref([])
const schedulesLoading = ref(false)
const currentWorkflow = ref(null)
const currentSchedule = ref(null)

// 搜索表单
const searchForm = reactive({
  keyword: '',
  status: '',
  project_id: ''
})

// 分页信息
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

/**
 * 获取状态类型
 */
const getStatusType = (status) => {
  const statusMap = {
    'draft': 'warning',
    'active': 'success',
    'inactive': 'info',
    'archived': 'info'
  }
  return statusMap[status] || 'info'
}

/**
 * 获取状态文本
 */
const getStatusText = (status) => {
  const statusMap = {
    'draft': '草稿',
    'active': '活跃',
    'inactive': '未激活',
    'archived': '已归档'
  }
  return statusMap[status] || '未知'
}

/**
 * 格式化时间
 */
const formatTime = (time) => {
  if (!time) return ''
  return formatDistanceToNow(new Date(time), {
    addSuffix: true,
    locale: zhCN
  })
}

/**
 * 格式化日期
 */
const formatDate = (date) => {
  if (!date) return ''
  return format(new Date(date), 'yyyy-MM-dd HH:mm', { locale: zhCN })
}

/**
 * 加载工作流列表
 */
const loadWorkflowList = async () => {
  try {
    loading.value = true
    
    // 构建查询参数，过滤掉空值并映射到后端期望的参数名
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    // 只添加非空的搜索参数，映射前端参数名到后端参数名
    if (searchForm.keyword && searchForm.keyword.trim()) {
      params.name = searchForm.keyword.trim()  // 前端keyword映射到后端name
    }
    if (searchForm.status) {
      params.workflow_status = searchForm.status  // 前端status映射到后端workflow_status
    }
    if (searchForm.project_id) {
      params.project_id = parseInt(searchForm.project_id)  // project_id保持不变
    }
    
    const response = await workflowStore.getWorkflowList(params)
    workflowList.value = response.items || []
    pagination.total = response.total || 0
  } catch (error) {
    ElMessage.error('加载工作流列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载项目列表
 */
const loadProjects = async () => {
  try {
    const response = await projectStore.getProjectList({ page: 1, size: 100 })
    projects.value = response.data || []
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

/**
 * 处理搜索
 */
const handleSearch = () => {
  pagination.page = 1
  loadWorkflowList()
}

/**
 * 处理重置
 */
const handleReset = () => {
  Object.assign(searchForm, {
    keyword: '',
    status: '',
    project_id: ''
  })
  pagination.page = 1
  loadWorkflowList()
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection) => {
  selectedWorkflows.value = selection
}

/**
 * 处理页码变化
 */
const handlePageChange = (page) => {
  pagination.page = page
  loadWorkflowList()
}

/**
 * 处理页大小变化
 */
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  loadWorkflowList()
}

/**
 * 查看工作流详情
 */
const handleView = (workflow) => {
  router.push(`/workflows/${workflow.id}`)
}

/**
 * 编辑工作流
 */
const handleEdit = (workflow) => {
  router.push(`/workflows/${workflow.id}/edit`)
}

/**
 * 切换工作流状态
 */
const handleStatusChange = async (workflow) => {
  const isToActive = workflow.workflow_status !== 'active'
  const actionText = isToActive ? '发布' : '停用'
  const newStatus = isToActive ? 'active' : 'inactive'
  
  try {
    await ElMessageBox.confirm(
      `确定要${actionText}工作流 "${workflow.name}" 吗？`,
      `确认${actionText}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: isToActive ? 'success' : 'warning'
      }
    )
    
    await workflowStore.updateWorkflow(workflow.id, { workflow_status: newStatus })
    ElMessage.success(`工作流${actionText}成功`)
    // 不需要重新加载整个列表，因为 store 里的 updateWorkflow 已经更新了本地状态
    // 但为了确保万无一失，或者如果有其他副作用，也可以刷新
    // loadWorkflowList() 
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || `${actionText}工作流失败`)
    }
  }
}

/**
 * 执行工作流
 */
const handleExecute = async (workflow) => {
  try {
    await ElMessageBox.confirm(
      `确定要执行工作流 "${workflow.name}" 吗？`,
      '确认执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await workflowStore.executeWorkflow(workflow.id)
    ElMessage.success('工作流执行成功')
    loadWorkflowList()
  } catch (error) {
    if (error !== 'cancel') {
      // 移除这里的 ElMessage.error，因为 request.js 拦截器中已经统一处理了错误显示
      // ElMessage.error(error.message || '执行工作流失败')
    }
  }
}

/**
 * 克隆工作流
 */
const handleClone = async (workflow) => {
  try {
    await workflowStore.cloneWorkflow(workflow.id)
    ElMessage.success('工作流克隆成功')
    loadWorkflowList()
  } catch (error) {
    ElMessage.error(error.message || '克隆工作流失败')
  }
}

/**
 * 删除工作流
 */
const handleDelete = async (workflow) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除工作流 "${workflow.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await workflowStore.deleteWorkflow(workflow.id)
    ElMessage.success('工作流删除成功')
    loadWorkflowList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除工作流失败')
    }
  }
}

/**
 * 批量执行
 */
const handleBatchExecute = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要执行选中的 ${selectedWorkflows.value.length} 个工作流吗？`,
      '确认批量执行',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedWorkflows.value.map(item => item.id)
    await workflowStore.batchExecuteWorkflows(ids)
    ElMessage.success('批量执行成功')
    loadWorkflowList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量执行失败')
    }
  }
}

/**
 * 批量更新状态
 */
const handleBatchStatusChange = async (status) => {
  const actionText = status === 'active' ? '发布' : '停用'
  try {
    await ElMessageBox.confirm(
      `确定要${actionText}选中的 ${selectedWorkflows.value.length} 个工作流吗？`,
      `确认批量${actionText}`,
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedWorkflows.value.map(item => item.id)
    await workflowStore.batchUpdateStatusWorkflows(ids, status)
    ElMessage.success(`批量${actionText}成功`)
    loadWorkflowList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || `批量${actionText}失败`)
    }
  }
}

/**
 * 批量删除
 */
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedWorkflows.value.length} 个工作流吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    const ids = selectedWorkflows.value.map(item => item.id)
    await workflowStore.batchDeleteWorkflows(ids)
    ElMessage.success('批量删除成功')
    loadWorkflowList()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '批量删除失败')
    }
  }
}

/**
 * 打开调度管理
 */
const handleSchedule = (workflow) => {
  currentWorkflow.value = workflow
  scheduleDrawerVisible.value = true
  loadSchedules()
}

/**
 * 加载调度列表
 */
const loadSchedules = async () => {
  if (!currentWorkflow.value) return
  try {
    schedulesLoading.value = true
    const response = await workflowStore.getWorkflowSchedules(currentWorkflow.value.id)
    schedules.value = response || []
  } catch (error) {
    ElMessage.error('加载调度列表失败')
  } finally {
    schedulesLoading.value = false
  }
}

/**
 * 创建调度
 */
const handleCreateSchedule = () => {
  currentSchedule.value = null
  scheduleDialogVisible.value = true
}

/**
 * 编辑调度
 */
const handleEditSchedule = (schedule) => {
  currentSchedule.value = schedule
  scheduleDialogVisible.value = true
}

/**
 * 删除调度
 */
const handleDeleteSchedule = async (schedule) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除调度 "${schedule.schedule_name}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await workflowStore.deleteWorkflowSchedule(currentWorkflow.value.id, schedule.id)
    ElMessage.success('调度删除成功')
    loadSchedules()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.message || '删除调度失败')
    }
  }
}

/**
 * 组件挂载时加载数据
 */
onMounted(() => {
  // 如果有当前选中的项目，设置为默认筛选条件
  if (projectStore.currentProject) {
    searchForm.project_id = projectStore.currentProject.id
  }
  loadWorkflowList()
  loadProjects()
})

/**
 * 监听当前项目变化，自动刷新工作流列表
 */
watch(
  () => projectStore.currentProject,
  (newProject, oldProject) => {
    if (newProject?.id !== oldProject?.id) {
      // 更新搜索条件中的项目ID
      searchForm.project_id = newProject?.id || null
      // 重新加载工作流列表
      loadWorkflowList()
    }
  },
  { deep: true }
)
</script>

<style scoped>
.workflow-list {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}

.header-content h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
}

.header-content p {
  margin: 0;
  color: #6b7280;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 24px;
  border: 1px solid #e5e7eb;
}

.filter-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-left {
  display: flex;
  gap: 16px;
  align-items: center;
}

.filter-right {
  display: flex;
  gap: 12px;
}

.table-card {
  border: 1px solid #e5e7eb;
}

.workflow-name {
  padding: 8px 0;
}

.name-link {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 500;
  color: #1890ff;
  cursor: pointer;
  transition: color 0.3s;
}

.name-link:hover {
  color: #40a9ff;
}

.description {
  margin: 0;
  font-size: 12px;
  color: #8c8c8c;
  line-height: 1.4;
}

.text-muted {
  color: #8c8c8c;
  font-size: 12px;
}

.task-count {
  font-weight: 500;
  color: #1f2937;
}

.execution-time {
  font-size: 12px;
  color: #6b7280;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.batch-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-top: 1px solid #e9ecef;
  margin-top: 16px;
}

.batch-info {
  font-size: 14px;
  color: #495057;
}

.batch-buttons {
  display: flex;
  gap: 12px;
}

.pagination-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .filter-content {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-left {
    flex-wrap: wrap;
  }
  
  .filter-right {
    justify-content: flex-end;
  }
}

@media (max-width: 768px) {
  .workflow-list {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .filter-left {
    flex-direction: column;
    gap: 12px;
  }
  
  .batch-actions {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .batch-buttons {
    justify-content: center;
  }
}
</style>