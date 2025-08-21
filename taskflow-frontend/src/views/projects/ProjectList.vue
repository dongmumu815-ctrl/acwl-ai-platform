<template>
  <div class="project-list">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h2>项目管理</h2>
        <p>管理和监控所有项目</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="createProject">
          <el-icon><Plus /></el-icon>
          新建项目
        </el-button>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <el-card class="search-card">
      <el-form :model="searchForm" inline>
        <el-form-item label="项目名称">
          <el-input
            v-model="searchForm.name"
            placeholder="请输入项目名称"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.status" placeholder="选择状态" clearable style="width: 120px">
            <el-option label="激活" value="active" />
            <el-option label="停用" value="inactive" />
            <el-option label="归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item label="创建时间">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 240px"
          />
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

    <!-- 项目列表 -->
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <span>项目列表 ({{ pagination.total }})</span>
          <div class="header-actions">
            <el-button
              text
              type="primary"
              @click="toggleBatchMode"
              :disabled="projects.length === 0"
            >
              {{ batchMode ? '取消批量' : '批量操作' }}
            </el-button>
            <el-dropdown v-if="batchMode && selectedProjects.length > 0" @command="handleBatchCommand">
              <el-button type="primary">
                批量操作 ({{ selectedProjects.length }})
                <el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="activate">
                    <el-icon><Check /></el-icon>
                    激活项目
                  </el-dropdown-item>
                  <el-dropdown-item command="deactivate">
                    <el-icon><Close /></el-icon>
                    停用项目
                  </el-dropdown-item>
                  <el-dropdown-item command="archive" divided>
                    <el-icon><Box /></el-icon>
                    归档项目
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <el-icon><Delete /></el-icon>
                    删除项目
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </template>

      <div v-loading="loading" class="table-container">
        <el-table
          :data="projects"
          style="width: 100%"
          @selection-change="handleSelectionChange"
          empty-text="暂无项目数据"
        >
          <el-table-column v-if="batchMode" type="selection" width="55" />
          
          <el-table-column label="项目名称" min-width="200">
            <template #default="{ row }">
              <div class="project-info">
                <div class="project-name">
                  <el-link @click="viewProject(row.id)" type="primary">
                    {{ row.name }}
                  </el-link>
                </div>
                <div class="project-description">{{ row.description || '暂无描述' }}</div>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusColor(row.status)">{{ formatStatus(row.status) }}</el-tag>
            </template>
          </el-table-column>
          
          <el-table-column label="工作流数量" width="120" align="center">
            <template #default="{ row }">
              <el-link @click="viewWorkflows(row.id)" type="primary">
                {{ row.workflow_count || 0 }}
              </el-link>
            </template>
          </el-table-column>
          
          <el-table-column label="任务数量" width="120" align="center">
            <template #default="{ row }">
              <el-link @click="viewTasks(row.id)" type="primary">
                {{ row.task_count || 0 }}
              </el-link>
            </template>
          </el-table-column>
          
          <el-table-column label="负责人" width="120">
            <template #default="{ row }">
              <div class="owner-info">
                <el-avatar :size="24" :src="row.owner_avatar">
                  {{ row.owner_name?.charAt(0) }}
                </el-avatar>
                <span class="owner-name">{{ row.owner_name }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="最后更新" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_at) }}
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-space>
                <el-button text type="primary" @click="viewProject(row.id)">
                  查看
                </el-button>
                <el-button text type="primary" @click="editProject(row.id)">
                  编辑
                </el-button>
                <el-dropdown @command="(command) => handleCommand(command, row)">
                  <el-button text type="primary">
                    更多
                    <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="clone">
                        <el-icon><CopyDocument /></el-icon>
                        克隆项目
                      </el-dropdown-item>
                      <el-dropdown-item command="export">
                        <el-icon><Download /></el-icon>
                        导出配置
                      </el-dropdown-item>
                      <el-dropdown-item command="archive" v-if="row.status !== 'archived'">
                        <el-icon><Box /></el-icon>
                        归档项目
                      </el-dropdown-item>
                      <el-dropdown-item command="activate" v-if="row.status !== 'active'">
                        <el-icon><Check /></el-icon>
                        激活项目
                      </el-dropdown-item>
                      <el-dropdown-item command="deactivate" v-if="row.status === 'active'">
                        <el-icon><Close /></el-icon>
                        停用项目
                      </el-dropdown-item>
                      <el-dropdown-item command="delete" divided>
                        <el-icon><Delete /></el-icon>
                        删除项目
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </el-space>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  ArrowDown,
  Check,
  Close,
  Box,
  Delete,
  CopyDocument,
  Download
} from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { formatDateTime, downloadFile } from '@/utils'

const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const batchMode = ref(false)
const projects = ref([])
const selectedProjects = ref([])

// 搜索表单
const searchForm = reactive({
  name: '',
  status: '',
  dateRange: []
})

// 分页信息
const pagination = reactive({
  page: 1,
  size: 20,
  total: 0
})

/**
 * 获取项目列表
 */
const fetchProjects = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.page,
      size: pagination.size,
      name: searchForm.name || undefined,
      status: searchForm.status || undefined,
      start_date: searchForm.dateRange?.[0] || undefined,
      end_date: searchForm.dateRange?.[1] || undefined
    }
    
    const result = await projectStore.getProjectList(params)
    projects.value = result.items || []
    pagination.total = result.total || 0
  } catch (error) {
    ElMessage.error('获取项目列表失败')
    console.error('获取项目列表失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 搜索项目
 */
const handleSearch = () => {
  pagination.page = 1
  fetchProjects()
}

/**
 * 重置搜索
 */
const handleReset = () => {
  searchForm.name = ''
  searchForm.status = ''
  searchForm.dateRange = []
  pagination.page = 1
  fetchProjects()
}

/**
 * 切换批量模式
 */
const toggleBatchMode = () => {
  batchMode.value = !batchMode.value
  selectedProjects.value = []
}

/**
 * 处理选择变化
 */
const handleSelectionChange = (selection) => {
  selectedProjects.value = selection
}

/**
 * 处理批量操作命令
 */
const handleBatchCommand = async (command) => {
  if (selectedProjects.value.length === 0) {
    ElMessage.warning('请选择要操作的项目')
    return
  }
  
  const projectIds = selectedProjects.value.map(p => p.id)
  
  try {
    switch (command) {
      case 'activate':
        await projectStore.batchUpdateProjectStatus(projectIds, 'active')
        ElMessage.success('批量激活成功')
        break
      case 'deactivate':
        await projectStore.batchUpdateProjectStatus(projectIds, 'inactive')
        ElMessage.success('批量停用成功')
        break
      case 'archive':
        await projectStore.batchUpdateProjectStatus(projectIds, 'archived')
        ElMessage.success('批量归档成功')
        break
      case 'delete':
        await ElMessageBox.confirm(
          `确定要删除选中的 ${selectedProjects.value.length} 个项目吗？删除后无法恢复。`,
          '确认删除',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await projectStore.batchDeleteProjects(projectIds)
        ElMessage.success('批量删除成功')
        break
    }
    
    selectedProjects.value = []
    await fetchProjects()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量操作失败')
    }
  }
}

/**
 * 处理单个操作命令
 */
const handleCommand = async (command, project) => {
  try {
    switch (command) {
      case 'clone':
        await cloneProject(project)
        break
      case 'export':
        await exportProject(project)
        break
      case 'archive':
        await updateProjectStatus(project.id, 'archived')
        break
      case 'activate':
        await updateProjectStatus(project.id, 'active')
        break
      case 'deactivate':
        await updateProjectStatus(project.id, 'inactive')
        break
      case 'delete':
        await deleteProject(project)
        break
    }
  } catch (error) {
    console.error('操作失败:', error)
  }
}

/**
 * 克隆项目
 */
const cloneProject = async (project) => {
  try {
    const clonedProject = {
      ...project,
      name: `${project.name} - 副本`,
      id: undefined,
      created_at: undefined,
      updated_at: undefined
    }
    await projectStore.createProject(clonedProject)
    ElMessage.success('项目克隆成功')
    await fetchProjects()
  } catch (error) {
    ElMessage.error('项目克隆失败')
  }
}

/**
 * 导出项目配置
 */
const exportProject = async (project) => {
  try {
    const projectDetail = await projectStore.getProjectDetail(project.id)
    const exportData = {
      name: projectDetail.name,
      description: projectDetail.description,
      settings: projectDetail.settings,
      workflows: projectDetail.workflows,
      tasks: projectDetail.tasks
    }
    
    const content = JSON.stringify(exportData, null, 2)
    const filename = `project_${project.name}_${Date.now()}.json`
    downloadFile(content, filename, 'application/json')
    ElMessage.success('项目配置导出成功')
  } catch (error) {
    ElMessage.error('项目配置导出失败')
  }
}

/**
 * 更新项目状态
 */
const updateProjectStatus = async (projectId, status) => {
  try {
    await projectStore.updateProjectStatus(projectId, status)
    ElMessage.success('项目状态更新成功')
    await fetchProjects()
  } catch (error) {
    ElMessage.error('项目状态更新失败')
  }
}

/**
 * 删除项目
 */
const deleteProject = async (project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？删除后无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await projectStore.deleteProject(project.id)
    ElMessage.success('项目删除成功')
    await fetchProjects()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('项目删除失败')
    }
  }
}

/**
 * 创建项目
 */
const createProject = () => {
  router.push('/projects/create')
}

/**
 * 查看项目详情
 */
const viewProject = (projectId) => {
  router.push(`/projects/${projectId}`)
}

/**
 * 编辑项目
 */
const editProject = (projectId) => {
  router.push(`/projects/${projectId}/edit`)
}

/**
 * 查看项目工作流
 */
const viewWorkflows = (projectId) => {
  router.push(`/workflows?project_id=${projectId}`)
}

/**
 * 查看项目任务
 */
const viewTasks = (projectId) => {
  router.push(`/tasks?project_id=${projectId}`)
}

/**
 * 分页大小改变
 */
const handleSizeChange = (size) => {
  pagination.size = size
  pagination.page = 1
  fetchProjects()
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page) => {
  pagination.page = page
  fetchProjects()
}

/**
 * 格式化状态
 */
const formatStatus = (status) => {
  const statuses = {
    active: '激活',
    inactive: '停用',
    archived: '归档'
  }
  return statuses[status] || status
}

/**
 * 获取状态颜色
 */
const getStatusColor = (status) => {
  const colors = {
    active: 'success',
    inactive: 'warning',
    archived: 'info'
  }
  return colors[status] || ''
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.project-list {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
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

.search-card {
  margin-bottom: 20px;
}

.list-card {
  min-height: 600px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.table-container {
  min-height: 400px;
}

.project-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-name {
  font-weight: 500;
  font-size: 14px;
}

.project-description {
  font-size: 12px;
  color: var(--el-text-color-regular);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.owner-name {
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
</style>