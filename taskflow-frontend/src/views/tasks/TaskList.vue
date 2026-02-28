<template>
  <div class="task-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>任务定义</h2>
        <p>管理任务的定义和配置</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="createTask">
          <el-icon><Plus /></el-icon>
          创建任务
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选 -->
    <el-card class="filter-card">
      <el-form :model="filterForm" inline>
        <el-form-item label="任务名称">
          <el-input
            v-model="filterForm.name"
            placeholder="请输入任务名称"
            clearable
            style="width: 200px"
          />
        </el-form-item>
        <el-form-item label="任务类型">
          <el-select v-model="filterForm.task_type" placeholder="选择任务类型" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option label="HTTP请求" value="http" />
            <el-option label="脚本执行" value="script" />
            <el-option label="数据处理" value="data" />
            <el-option label="文件操作" value="file" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="选择状态" clearable style="width: 120px">
            <el-option label="全部" value="" />
            <el-option label="激活" value="active" />
            <el-option label="未激活" value="inactive" />
            <el-option label="草稿" value="draft" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属项目">
          <el-select v-model="filterForm.project_id" placeholder="选择项目" clearable style="width: 150px">
            <el-option label="全部" value="" />
            <el-option
              v-for="project in projects"
              :key="project.id"
              :label="project.name"
              :value="project.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="handleReset">
            <el-icon><Refresh /></el-icon>
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 任务列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>任务列表 ({{ pagination.total }})</span>
          <div class="header-actions">
            <el-button
              :disabled="selectedTasks.length === 0"
              @click="batchExecute"
            >
              批量执行
            </el-button>
            <el-button
              :disabled="selectedTasks.length === 0"
              type="danger"
              @click="batchDelete"
            >
              批量删除
            </el-button>
          </div>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="taskList"
        stripe
        @selection-change="handleSelectionChange"
        @row-click="viewTask"
        style="cursor: pointer"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="name" label="任务名称" min-width="200">
          <template #default="{ row }">
            <div class="task-name-cell">
              <el-icon class="task-icon"><Operation /></el-icon>
              <div>
                <div class="task-name">{{ row.name }}</div>
                <div class="task-description">{{ row.description || '暂无描述' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="task_type" label="任务类型" width="120">
          <template #default="{ row }">
            <el-tag size="small" :type="getTaskTypeColor(row.task_type)">{{ getTaskTypeText(row.task_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="project_name" label="所属项目" width="150" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="执行次数" width="100">
          <template #default="{ row }">
            <span class="execution-count">{{ row.execution_count || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="last_execution" label="最后执行" width="180">
          <template #default="{ row }">
            {{ formatTime(row.last_execution) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click.stop="viewTask(row)"
            >
              查看
            </el-button>
            <el-button
              size="small"
              text
              @click.stop="editTask(row)"
            >
              编辑
            </el-button>
            <el-button
              type="success"
              size="small"
              text
              @click.stop="executeTask(row)"
            >
              执行
            </el-button>
            <el-dropdown @command="(command) => handleCommand(command, row)" @click.stop>
              <el-button size="small" text>
                更多
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="clone">克隆</el-dropdown-item>
                  <el-dropdown-item command="export">导出</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Refresh, Operation, ArrowDown } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/task'
import { useProjectStore } from '@/stores/project'
import { formatTime } from '@/utils'

const router = useRouter()
const taskStore = useTaskStore()
const projectStore = useProjectStore()

const loading = ref(false)
const taskList = ref([])
const projects = ref([])
const selectedTasks = ref([])

const filterForm = reactive({
  name: '',
  task_type: '',
  status: '',
  project_id: ''
})

const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

/**
 * 获取任务列表
 */
const fetchTasks = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size
    }
    
    if (filterForm.name) params.name = filterForm.name
    if (filterForm.task_type) params.task_type = filterForm.task_type
    if (filterForm.status) params.status = filterForm.status
    if (filterForm.project_id) params.project_id = filterForm.project_id
    
    const result = await taskStore.getTaskList(params)
    taskList.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    // 错误已由全局拦截器处理，无需再次显示 ElMessage
    // ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 获取项目列表
 */
const fetchProjects = async () => {
  try {
    const result = await projectStore.getProjectList({ page: 1, size: 100 })
    projects.value = result.items || []
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

/**
 * 创建任务
 */
const createTask = () => {
  router.push('/tasks/create')
}

/**
 * 查看任务
 */
const viewTask = (row) => {
  router.push(`/tasks/${row.id}`)
}

/**
 * 编辑任务
 */
const editTask = (row) => {
  router.push(`/tasks/${row.id}/edit`)
}

/**
 * 执行任务
 */
const executeTask = async (row) => {
  try {
    await taskStore.executeTask(row.id)
    ElMessage.success('任务执行成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('任务执行失败')
  }
}

/**
 * 搜索
 */
const handleSearch = () => {
  pagination.page = 1
  fetchTasks()
}

/**
 * 重置
 */
const handleReset = () => {
  Object.assign(filterForm, {
    name: '',
    task_type: '',
    status: '',
    project_id: ''
  })
  pagination.page = 1
  fetchTasks()
}

/**
 * 页面大小改变
 */
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchTasks()
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page) => {
  pagination.page = page
  fetchTasks()
}

/**
 * 选择改变
 */
const handleSelectionChange = (selection) => {
  selectedTasks.value = selection
}

/**
 * 批量执行
 */
const batchExecute = async () => {
  try {
    await ElMessageBox.confirm(`确定要执行选中的 ${selectedTasks.value.length} 个任务吗？`, '确认执行', {
      type: 'warning'
    })
    
    const taskIds = selectedTasks.value.map(task => task.id)
    await taskStore.batchExecuteTasks(taskIds)
    ElMessage.success('批量执行成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量执行失败')
    }
  }
}

/**
 * 批量删除
 */
const batchDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`, '确认删除', {
      type: 'warning'
    })
    
    const taskIds = selectedTasks.value.map(task => task.id)
    await taskStore.batchDeleteTasks(taskIds)
    ElMessage.success('批量删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 处理下拉菜单命令
 */
const handleCommand = async (command, row) => {
  switch (command) {
    case 'clone':
      await cloneTask(row)
      break
    case 'export':
      await exportTask(row)
      break
    case 'delete':
      await deleteTask(row)
      break
  }
}

/**
 * 克隆任务
 */
const cloneTask = async (row) => {
  try {
    await taskStore.cloneTask(row.id)
    ElMessage.success('任务克隆成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error('任务克隆失败')
  }
}

/**
 * 导出任务
 */
const exportTask = async (row) => {
  try {
    const result = await taskStore.exportTask(row.id)
    // 创建下载链接
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `task_${row.name}.json`
    link.click()
    window.URL.revokeObjectURL(url)
    ElMessage.success('任务导出成功')
  } catch (error) {
    ElMessage.error('任务导出失败')
  }
}

/**
 * 删除任务
 */
const deleteTask = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除任务 "${row.name}" 吗？`, '确认删除', {
      type: 'warning'
    })
    
    await taskStore.deleteTask(row.id)
    ElMessage.success('任务删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('任务删除失败')
    }
  }
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
 * 获取任务类型颜色
 */
const getTaskTypeColor = (taskType) => {
  const colorMap = {
    'http': 'primary',
    'script': 'success',
    'data': 'warning',
    'file': 'info'
  }
  return colorMap[taskType] || 'info'
}

/**
 * 获取任务类型文本
 */
const getTaskTypeText = (taskType) => {
  const textMap = {
    'http': 'HTTP请求',
    'script': '脚本执行',
    'data': '数据处理',
    'file': '文件操作'
  }
  return textMap[taskType] || taskType
}

onMounted(() => {
  fetchTasks()
  fetchProjects()
})
</script>

<style scoped>
.task-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  color: var(--el-text-color-primary);
}

.header-left p {
  margin: 0;
  color: var(--el-text-color-regular);
}

.filter-card {
  margin-bottom: 20px;
}

.list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.task-name-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.task-icon {
  font-size: 20px;
  color: var(--el-color-primary);
}

.task-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.task-description {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-top: 4px;
}

.execution-count {
  font-weight: 500;
  color: var(--el-color-primary);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

:deep(.el-table__row) {
  cursor: pointer;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-table-row-hover-bg-color);
}
</style>