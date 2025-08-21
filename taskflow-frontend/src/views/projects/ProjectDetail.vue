<template>
  <div class="project-detail">
    <el-page-header @back="goBack" :content="project?.name || '项目详情'">
      <template #extra>
        <el-space>
          <el-button @click="editProject" type="primary">
            <el-icon><Edit /></el-icon>
            编辑项目
          </el-button>
          <el-dropdown @command="handleCommand">
            <el-button>
              更多操作
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
                <el-dropdown-item command="archive" v-if="project?.status !== 'archived'">
                  <el-icon><Box /></el-icon>
                  归档项目
                </el-dropdown-item>
                <el-dropdown-item command="activate" v-if="project?.status !== 'active'">
                  <el-icon><Check /></el-icon>
                  激活项目
                </el-dropdown-item>
                <el-dropdown-item command="deactivate" v-if="project?.status === 'active'">
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
    </el-page-header>

    <div class="detail-content" v-loading="loading">
      <el-row :gutter="20" v-if="project">
        <el-col :span="16">
          <!-- 基本信息 -->
          <el-card class="info-card">
            <template #header>
              <span>基本信息</span>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="项目名称">
                {{ project.name }}
              </el-descriptions-item>
              <el-descriptions-item label="项目ID">
                {{ project.id }}
              </el-descriptions-item>
              <el-descriptions-item label="项目状态">
                <el-tag :type="getStatusColor(project.status)">{{ formatStatus(project.status) }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="可见性">
                <el-tag :type="project.visibility === 'public' ? 'success' : 'warning'">
                  {{ project.visibility === 'public' ? '公开' : '私有' }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="项目负责人">
                <div class="owner-info">
                  <el-avatar :size="24" :src="project.owner_avatar">
                    {{ project.owner_name?.charAt(0) }}
                  </el-avatar>
                  <span class="owner-name">{{ project.owner_name }}</span>
                </div>
              </el-descriptions-item>
              <el-descriptions-item label="创建时间">
                {{ formatDateTime(project.created_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="更新时间" :span="2">
                {{ formatDateTime(project.updated_at) }}
              </el-descriptions-item>
              <el-descriptions-item label="项目描述" :span="2">
                {{ project.description || '暂无描述' }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div v-if="project.tags && project.tags.length > 0" class="tags-section">
              <h4>项目标签</h4>
              <el-tag
                v-for="tag in project.tags"
                :key="tag"
                style="margin-right: 8px; margin-bottom: 8px"
              >
                {{ tag }}
              </el-tag>
            </div>
          </el-card>

          <!-- 项目设置 -->
          <el-card class="info-card">
            <template #header>
              <span>项目设置</span>
            </template>
            
            <el-descriptions :column="2" border>
              <el-descriptions-item label="最大并发数">
                {{ project.settings?.max_concurrent_workflows || 10 }}
              </el-descriptions-item>
              <el-descriptions-item label="默认超时">
                {{ project.settings?.default_timeout || 3600 }}秒
              </el-descriptions-item>
              <el-descriptions-item label="默认重试次数">
                {{ project.settings?.default_retry_count || 3 }}次
              </el-descriptions-item>
              <el-descriptions-item label="执行记录保留">
                {{ project.settings?.execution_retention_days || 30 }}天
              </el-descriptions-item>
              <el-descriptions-item label="日志保留">
                {{ project.settings?.log_retention_days || 7 }}天
              </el-descriptions-item>
              <el-descriptions-item label="通知邮箱">
                {{ project.settings?.notification_emails || '未设置' }}
              </el-descriptions-item>
            </el-descriptions>
            
            <div v-if="project.settings?.notifications && project.settings.notifications.length > 0" class="notifications-section">
              <h4>通知设置</h4>
              <el-tag
                v-for="notification in project.settings.notifications"
                :key="notification"
                type="info"
                style="margin-right: 8px; margin-bottom: 8px"
              >
                {{ formatNotification(notification) }}
              </el-tag>
            </div>
          </el-card>

          <!-- 项目成员 -->
          <el-card class="info-card" v-if="project.visibility === 'private' && project.members">
            <template #header>
              <div class="card-header">
                <span>项目成员 ({{ project.members.length }})</span>
                <el-button text type="primary" @click="manageMembers">
                  管理成员
                </el-button>
              </div>
            </template>
            
            <div class="members-grid">
              <div v-for="member in project.members" :key="member.user_id" class="member-item">
                <el-avatar :size="40" :src="member.avatar">
                  {{ member.name?.charAt(0) }}
                </el-avatar>
                <div class="member-info">
                  <div class="member-name">{{ member.name }}</div>
                  <div class="member-role">
                    <el-tag :type="getRoleColor(member.role)" size="small">
                      {{ formatRole(member.role) }}
                    </el-tag>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- 项目统计 -->
          <el-card class="info-card">
            <template #header>
              <span>项目统计</span>
            </template>
            
            <div class="stats-grid">
              <div class="stat-item" @click="viewWorkflows">
                <div class="stat-icon workflows">
                  <el-icon :size="24"><Share /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ project.workflow_count || 0 }}</div>
                  <div class="stat-label">工作流</div>
                </div>
              </div>
              
              <div class="stat-item" @click="viewTasks">
                <div class="stat-icon tasks">
                  <el-icon :size="24"><List /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ project.task_count || 0 }}</div>
                  <div class="stat-label">任务</div>
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-icon executions">
                  <el-icon :size="24"><VideoPlay /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ project.execution_count || 0 }}</div>
                  <div class="stat-label">总执行次数</div>
                </div>
              </div>
              
              <div class="stat-item">
                <div class="stat-icon success">
                  <el-icon :size="24"><SuccessFilled /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value success">{{ calculateSuccessRate() }}%</div>
                  <div class="stat-label">成功率</div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 最近活动 -->
          <el-card class="info-card">
            <template #header>
              <div class="card-header">
                <span>最近活动</span>
                <el-button text type="primary" @click="viewAllActivities">
                  查看全部
                </el-button>
              </div>
            </template>
            
            <div v-if="activities.length === 0" class="empty-state">
              <el-empty description="暂无活动记录" :image-size="80" />
            </div>
            
            <div v-else class="activity-list">
              <div v-for="activity in activities" :key="activity.id" class="activity-item">
                <div class="activity-icon">
                  <el-icon :size="16"><component :is="getActivityIcon(activity.type)" /></el-icon>
                </div>
                <div class="activity-content">
                  <div class="activity-title">{{ activity.title }}</div>
                  <div class="activity-description">{{ activity.description }}</div>
                  <div class="activity-time">{{ formatDateTime(activity.created_at) }}</div>
                </div>
              </div>
            </div>
          </el-card>

          <!-- 快速操作 -->
          <el-card class="info-card">
            <template #header>
              <span>快速操作</span>
            </template>
            
            <div class="quick-actions">
              <el-button type="primary" @click="createWorkflow" style="width: 100%; margin-bottom: 12px">
                <el-icon><Plus /></el-icon>
                创建工作流
              </el-button>
              <el-button @click="createTask" style="width: 100%; margin-bottom: 12px">
                <el-icon><Plus /></el-icon>
                创建任务
              </el-button>
              <el-button @click="viewMonitoring" style="width: 100%; margin-bottom: 12px">
                <el-icon><Monitor /></el-icon>
                监控面板
              </el-button>
              <el-button @click="viewSettings" style="width: 100%">
                <el-icon><Setting /></el-icon>
                项目设置
              </el-button>
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
  Edit,
  ArrowDown,
  CopyDocument,
  Download,
  Box,
  Check,
  Close,
  Delete,
  Share,
  List,
  VideoPlay,
  SuccessFilled,
  Plus,
  Monitor,
  Setting,
  User,
  Document,
  Warning
} from '@element-plus/icons-vue'
import { useProjectStore } from '@/stores/project'
import { formatDateTime, downloadFile } from '@/utils'

const route = useRoute()
const router = useRouter()
const projectStore = useProjectStore()

const loading = ref(false)
const project = ref(null)
const activities = ref([])

/**
 * 获取项目详情
 */
const fetchProjectDetail = async () => {
  try {
    loading.value = true
    const projectId = route.params.id
    project.value = await projectStore.getProjectDetail(projectId)
    await fetchRecentActivities()
  } catch (error) {
    ElMessage.error('获取项目详情失败')
    console.error('获取项目详情失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 获取最近活动
 */
const fetchRecentActivities = async () => {
  try {
    const projectId = route.params.id
    const result = await projectStore.getProjectActivities(projectId, { page: 1, size: 10 })
    activities.value = result.items || []
  } catch (error) {
    console.error('获取活动记录失败:', error)
  }
}

/**
 * 处理更多操作命令
 */
const handleCommand = async (command) => {
  switch (command) {
    case 'clone':
      await cloneProject()
      break
    case 'export':
      await exportProject()
      break
    case 'archive':
      await updateProjectStatus('archived')
      break
    case 'activate':
      await updateProjectStatus('active')
      break
    case 'deactivate':
      await updateProjectStatus('inactive')
      break
    case 'delete':
      await deleteProject()
      break
  }
}

/**
 * 克隆项目
 */
const cloneProject = async () => {
  try {
    const clonedProject = {
      ...project.value,
      name: `${project.value.name} - 副本`,
      id: undefined,
      created_at: undefined,
      updated_at: undefined
    }
    await projectStore.createProject(clonedProject)
    ElMessage.success('项目克隆成功')
    router.push('/projects')
  } catch (error) {
    ElMessage.error('项目克隆失败')
  }
}

/**
 * 导出项目配置
 */
const exportProject = async () => {
  try {
    const exportData = {
      name: project.value.name,
      description: project.value.description,
      settings: project.value.settings,
      workflows: project.value.workflows,
      tasks: project.value.tasks
    }
    
    const content = JSON.stringify(exportData, null, 2)
    const filename = `project_${project.value.name}_${Date.now()}.json`
    downloadFile(content, filename, 'application/json')
    ElMessage.success('项目配置导出成功')
  } catch (error) {
    ElMessage.error('项目配置导出失败')
  }
}

/**
 * 更新项目状态
 */
const updateProjectStatus = async (status) => {
  try {
    await projectStore.updateProjectStatus(project.value.id, status)
    ElMessage.success('项目状态更新成功')
    project.value.status = status
  } catch (error) {
    ElMessage.error('项目状态更新失败')
  }
}

/**
 * 删除项目
 */
const deleteProject = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.value.name}" 吗？删除后无法恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await projectStore.deleteProject(project.value.id)
    ElMessage.success('项目删除成功')
    router.push('/projects')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('项目删除失败')
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
 * 编辑项目
 */
const editProject = () => {
  router.push(`/projects/${project.value.id}/edit`)
}

/**
 * 管理成员
 */
const manageMembers = () => {
  router.push(`/projects/${project.value.id}/members`)
}

/**
 * 查看工作流
 */
const viewWorkflows = () => {
  router.push(`/workflows?project_id=${project.value.id}`)
}

/**
 * 查看任务
 */
const viewTasks = () => {
  router.push(`/tasks?project_id=${project.value.id}`)
}

/**
 * 查看所有活动
 */
const viewAllActivities = () => {
  router.push(`/projects/${project.value.id}/activities`)
}

/**
 * 创建工作流
 */
const createWorkflow = () => {
  router.push(`/workflows/create?project_id=${project.value.id}`)
}

/**
 * 创建任务
 */
const createTask = () => {
  router.push(`/tasks/create?project_id=${project.value.id}`)
}

/**
 * 查看监控面板
 */
const viewMonitoring = () => {
  router.push(`/monitoring?project_id=${project.value.id}`)
}

/**
 * 查看项目设置
 */
const viewSettings = () => {
  router.push(`/projects/${project.value.id}/settings`)
}

/**
 * 计算成功率
 */
const calculateSuccessRate = () => {
  if (!project.value || !project.value.execution_count) return 0
  return Math.round((project.value.success_count / project.value.execution_count) * 100)
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

/**
 * 格式化通知类型
 */
const formatNotification = (notification) => {
  const notifications = {
    workflow_success: '工作流成功',
    workflow_failure: '工作流失败',
    task_failure: '任务失败',
    daily_report: '每日报告'
  }
  return notifications[notification] || notification
}

/**
 * 格式化角色
 */
const formatRole = (role) => {
  const roles = {
    admin: '管理员',
    editor: '编辑者',
    viewer: '查看者'
  }
  return roles[role] || role
}

/**
 * 获取角色颜色
 */
const getRoleColor = (role) => {
  const colors = {
    admin: 'danger',
    editor: 'warning',
    viewer: 'info'
  }
  return colors[role] || ''
}

/**
 * 获取活动图标
 */
const getActivityIcon = (type) => {
  const icons = {
    workflow_created: 'Plus',
    workflow_executed: 'VideoPlay',
    task_created: 'Document',
    task_executed: 'VideoPlay',
    member_added: 'User',
    settings_updated: 'Setting',
    error: 'Warning'
  }
  return icons[type] || 'Document'
}

onMounted(() => {
  fetchProjectDetail()
})
</script>

<style scoped>
.project-detail {
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

.tags-section,
.notifications-section {
  margin-top: 20px;
}

.tags-section h4,
.notifications-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.owner-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.owner-name {
  font-weight: 500;
}

.members-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
}

.member-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}

.member-info {
  flex: 1;
}

.member-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.stat-item:hover {
  background: var(--el-fill-color-light);
  transform: translateY(-2px);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
}

.stat-icon.workflows {
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
}

.stat-icon.tasks {
  background: var(--el-color-success-light-8);
  color: var(--el-color-success);
}

.stat-icon.executions {
  background: var(--el-color-warning-light-8);
  color: var(--el-color-warning);
}

.stat-icon.success {
  background: var(--el-color-success-light-8);
  color: var(--el-color-success);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 20px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.stat-value.success {
  color: var(--el-color-success);
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

.activity-list {
  max-height: 300px;
  overflow-y: auto;
}

.activity-item {
  display: flex;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
}

.activity-item:last-child {
  border-bottom: none;
}

.activity-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--el-color-primary-light-8);
  color: var(--el-color-primary);
  border-radius: 50%;
  flex-shrink: 0;
}

.activity-content {
  flex: 1;
}

.activity-title {
  font-weight: 500;
  font-size: 14px;
  margin-bottom: 4px;
}

.activity-description {
  font-size: 12px;
  color: var(--el-text-color-regular);
  margin-bottom: 4px;
}

.activity-time {
  font-size: 11px;
  color: var(--el-text-color-placeholder);
}

.quick-actions {
  display: flex;
  flex-direction: column;
}
</style>