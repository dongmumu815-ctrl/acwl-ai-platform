<template>
  <el-dialog
    v-model="visible"
    :title="project?.name || '项目详情'"
    width="1200px"
    @close="handleClose"
  >
    <div v-if="project" class="project-detail">
      <!-- 项目基本信息 -->
      <el-card class="detail-card">
        <template #header>
          <div class="card-header">
            <span>基本信息</span>
            <el-button type="primary" size="small" @click="handleEditProject">
              <el-icon><Edit /></el-icon>
              编辑项目
            </el-button>
          </div>
        </template>
        
        <el-descriptions :column="3" border>
          <el-descriptions-item label="项目名称">
            {{ project.name }}
          </el-descriptions-item>
          <el-descriptions-item label="项目类型">
            <el-tag :type="getProjectTypeConfig(project.project_type).type">
              {{ getProjectTypeLabel(project.project_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="项目状态">
            <el-tag :type="getProjectStatusConfig(project.status).type">
              {{ getProjectStatusConfig(project.status).label }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getProjectPriorityConfig(project.priority).type">
              {{ getProjectPriorityConfig(project.priority).label }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="团队成员">
            {{ project.members_count || 0 }}人
          </el-descriptions-item>
          <el-descriptions-item label="进度">
            <el-progress
              :percentage="calculateProjectProgress(project.start_date, project.end_date)"
              :status="project.status === 'completed' ? 'success' : undefined"
            />
          </el-descriptions-item>
          <el-descriptions-item label="开始日期">
            {{ project.start_date ? formatDate(project.start_date) : '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="结束日期">
            <span :class="{ 'text-danger': isProjectOverdue(project.end_date), 'text-warning': isProjectNearDeadline(project.end_date) }">
              {{ project.end_date ? formatDate(project.end_date) : '-' }}
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="创建者">
            {{ project.creator_username || '-' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间" :span="3">
            {{ formatDateTime(project.created_at) }}
          </el-descriptions-item>
          <el-descriptions-item label="项目描述" :span="3">
            {{ project.description || '暂无描述' }}
          </el-descriptions-item>
          <el-descriptions-item label="标签" :span="3">
            <el-tag
              v-for="tag in Object.keys(project.tags || {})"
              :key="tag"
              size="small"
              style="margin-right: 8px;"
            >
              {{ tag }}
            </el-tag>
            <span v-if="!project.tags || Object.keys(project.tags).length === 0">暂无标签</span>
          </el-descriptions-item>
        </el-descriptions>
      </el-card>

      <!-- 标签页 -->
      <el-card class="detail-card">
        <el-tabs v-model="activeTab" type="border-card">
          <!-- 项目成员 -->
          <el-tab-pane label="项目成员" name="members">
            <div class="tab-header">
              <span>成员列表</span>
              <el-button type="primary" size="small" @click="showAddMemberDialog = true">
                <el-icon><Plus /></el-icon>
                添加成员
              </el-button>
            </div>
            
            <el-table v-loading="membersLoading" :data="memberList" stripe>
              <el-table-column prop="username" label="用户名" />
              <el-table-column prop="email" label="邮箱" />
              <el-table-column prop="role" label="角色" width="120">
                <template #default="{ row }">
                  <el-tag :type="getProjectMemberRoleConfig(row.role).type">
                    {{ getProjectMemberRoleConfig(row.role).label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="备注" show-overflow-tooltip />
              <el-table-column prop="inviter_name" label="邀请人" />
              <el-table-column prop="joined_at" label="加入时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.joined_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button type="warning" size="small" @click="handleEditMember(row)">
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" @click="handleRemoveMember(row)">
                    移除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 项目数据源 -->
          <el-tab-pane label="数据源" name="datasources">
            <div class="tab-header">
              <span>数据源列表</span>
              <el-button type="primary" size="small" @click="handleShowAssignDatasourceDialog">
                <el-icon><Plus /></el-icon>
                分配数据源
              </el-button>
            </div>
            
            <el-table v-loading="datasourcesLoading" :data="datasourceList" stripe>
              <el-table-column prop="datasource_name" label="数据源名称" />
              <el-table-column prop="datasource_type" label="数据源类型" width="120">
                <template #default="{ row }">
                  <el-tag>{{ row.datasource_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="access_type" label="访问权限" width="120">
                <template #default="{ row }">
                  <el-tag :type="getAccessTypeConfig(row.access_type).type">
                    {{ getAccessTypeConfig(row.access_type).label }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="notes" label="备注" show-overflow-tooltip />
              <el-table-column prop="assigner_name" label="分配人" />
              <el-table-column prop="assigned_at" label="分配时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.assigned_at) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="150">
                <template #default="{ row }">
                  <el-button type="warning" size="small" @click="handleEditDatasource(row)">
                    编辑
                  </el-button>
                  <el-button type="danger" size="small" @click="handleRemoveDatasource(row)">
                    移除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <!-- 活动日志 -->
          <el-tab-pane label="活动日志" name="activities">
            <el-table v-loading="activitiesLoading" :data="activityList" stripe>
              <el-table-column prop="username" label="操作人" width="120" />
              <el-table-column prop="activity_type" label="操作类型" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.activity_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="target_type" label="目标类型" width="100">
                <template #default="{ row }">
                  <el-tag size="small" type="info">{{ row.target_type }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="操作描述" show-overflow-tooltip />
              <el-table-column prop="created_at" label="操作时间" width="160">
                <template #default="{ row }">
                  {{ formatDateTime(row.created_at) }}
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </el-card>
    </div>

    <!-- 添加成员对话框 -->
    <el-dialog
      v-model="showAddMemberDialog"
      title="添加项目成员"
      width="500px"
      @close="handleMemberDialogClose"
    >
      <el-form
        ref="memberFormRef"
        :model="memberForm"
        :rules="memberFormRules"
        label-width="80px"
      >
        <el-form-item label="用户" prop="user_id">
          <el-select
            v-model="memberForm.user_id"
            placeholder="请选择用户"
            filterable
            remote
            :remote-method="searchUsers"
            :loading="userSearchLoading"
            style="width: 100%"
          >
            <el-option
              v-for="user in userOptions"
              :key="user.id"
              :label="`${user.username} (${user.email})`"
              :value="user.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="memberForm.role" placeholder="请选择角色">
            <el-option
              v-for="role in PROJECT_MEMBER_ROLE_OPTIONS"
              :key="role.value"
              :label="role.label"
              :value="role.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="memberForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMemberDialog = false">取消</el-button>
        <el-button type="primary" :loading="memberSubmitting" @click="handleAddMember">
          添加
        </el-button>
      </template>
    </el-dialog>

    <!-- 分配数据源对话框 -->
    <el-dialog
      v-model="showAssignDatasourceDialog"
      title="分配数据源"
      width="500px"
      @close="handleDatasourceDialogClose"
    >
      <el-form
        ref="datasourceFormRef"
        :model="datasourceForm"
        :rules="datasourceFormRules"
        label-width="80px"
      >
        <el-form-item label="数据源" prop="datasource_id">
          <el-select
            v-model="datasourceForm.datasource_id"
            placeholder="请选择数据源"
            filterable
            style="width: 100%"
          >
            <el-option
              v-for="datasource in availableDatasources"
              :key="datasource.id"
              :label="`${datasource.name} (${datasource.datasource_type})`"
              :value="datasource.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="访问权限" prop="access_type">
          <el-select v-model="datasourceForm.access_type" placeholder="请选择访问权限">
            <el-option
              v-for="access in DATASOURCE_ACCESS_TYPES"
              :key="access.value"
              :label="access.label"
              :value="access.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="datasourceForm.notes"
            type="textarea"
            :rows="3"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAssignDatasourceDialog = false">取消</el-button>
        <el-button type="primary" :loading="datasourceSubmitting" @click="handleAssignDatasource">
          分配
        </el-button>
      </template>
    </el-dialog>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Plus } from '@element-plus/icons-vue'
import {
  type Project,
  type ProjectMember,
  type ProjectDatasource,
  type ProjectActivity,
  type ProjectMemberForm,
  type ProjectDatasourceForm,
  ProjectDatasourceAccessType,
  getProjectMembers,
  addProjectMember,
  removeProjectMember,
  getProjectDatasources,
  assignProjectDatasource,
  removeProjectDatasource,
  getProjectActivities,
  PROJECT_MEMBER_ROLE_OPTIONS,
  getProjectTypeLabel,
  getProjectStatusConfig,
  getProjectPriorityConfig,
  getProjectMemberRoleConfig,
  calculateProjectProgress,
  isProjectNearDeadline,
  isProjectOverdue
} from '@/api/projects'
import { getDatasources, type Datasource } from '@/api/datasource'
import { formatDate, formatDateTime } from '@/utils/date'

// Props
interface Props {
  modelValue: boolean
  project: Project | null
}

const props = defineProps<Props>()

// Emits
interface Emits {
  (e: 'update:modelValue', value: boolean): void
  (e: 'refresh'): void
}

const emit = defineEmits<Emits>()

// 响应式数据
const visible = ref(false)
const activeTab = ref('members')
const membersLoading = ref(false)
const datasourcesLoading = ref(false)
const activitiesLoading = ref(false)
const memberSubmitting = ref(false)
const datasourceSubmitting = ref(false)
const userSearchLoading = ref(false)

// 对话框状态
const showAddMemberDialog = ref(false)
const showAssignDatasourceDialog = ref(false)

// 列表数据
const memberList = ref<ProjectMember[]>([])
const datasourceList = ref<ProjectDatasource[]>([])
const activityList = ref<ProjectActivity[]>([])

const userOptions = ref<any[]>([])
const availableDatasources = ref<Datasource[]>([])

// 表单数据
const memberForm = reactive<ProjectMemberForm>({
  user_id: 0,
  role: 'member',
  notes: ''
})

const datasourceForm = reactive<ProjectDatasourceForm>({
  datasource_id: 0,
  access_type: ProjectDatasourceAccessType.READ,
  notes: ''
})

// 表单引用
const memberFormRef = ref()
const datasourceFormRef = ref()

// 表单验证规则
const memberFormRules = {
  user_id: [
    { required: true, message: '请选择用户', trigger: 'change' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

const datasourceFormRules = {
  datasource_id: [
    { required: true, message: '请选择数据源', trigger: 'change' }
  ],
  access_type: [
    { required: true, message: '请选择访问权限', trigger: 'change' }
  ]
}

// 数据源访问类型选项
const DATASOURCE_ACCESS_TYPES = [
  { value: ProjectDatasourceAccessType.READ, label: '只读', type: 'info' },
  { value: ProjectDatasourceAccessType.WRITE, label: '读写', type: 'warning' },
  { value: ProjectDatasourceAccessType.ADMIN, label: '管理员', type: 'danger' }
]

// 计算属性
const getProjectTypeConfig = computed(() => {
  return (type: string) => ({ type: 'info' })
})

const getAccessTypeConfig = computed(() => {
  return (accessType: string) => {
    const config = DATASOURCE_ACCESS_TYPES.find(item => item.value === accessType)
    return config || { label: accessType, type: 'info' }
  }
})

// 监听器
watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
    if (val && props.project) {
      loadProjectData()
    }
  },
  { immediate: true }
)

watch(visible, (val) => {
  emit('update:modelValue', val)
})

watch(activeTab, (tab) => {
  if (tab === 'members' && memberList.value.length === 0) {
    loadMembers()
  } else if (tab === 'datasources' && datasourceList.value.length === 0) {
    loadDatasources()
  } else if (tab === 'activities' && activityList.value.length === 0) {
    loadActivities()
  }
})

// 方法

/**
 * 加载项目数据
 */
const loadProjectData = () => {
  if (activeTab.value === 'members') {
    loadMembers()
  }
}

/**
 * 加载项目成员
 */
const loadMembers = async () => {
  if (!props.project) return
  
  try {
    membersLoading.value = true
    const response = await getProjectMembers(props.project.id)
    memberList.value = response.items
  } catch (error) {
    console.error('加载项目成员失败:', error)
    ElMessage.error('加载项目成员失败')
  } finally {
    membersLoading.value = false
  }
}

/**
 * 加载项目数据源
 */
const loadDatasources = async () => {
  if (!props.project) return
  
  try {
    datasourcesLoading.value = true
    const response = await getProjectDatasources(props.project.id)
    datasourceList.value = response.items
  } catch (error) {
    console.error('加载项目数据源失败:', error)
    ElMessage.error('加载项目数据源失败')
  } finally {
    datasourcesLoading.value = false
  }
}

/**
 * 加载项目活动
 */
const loadActivities = async () => {
  if (!props.project) return
  
  try {
    activitiesLoading.value = true
    const response = await getProjectActivities(props.project.id)
    activityList.value = response.items
  } catch (error) {
    console.error('加载项目活动失败:', error)
    ElMessage.error('加载项目活动失败')
  } finally {
    activitiesLoading.value = false
  }
}

/**
 * 加载可用数据源
 */
const loadAvailableDatasources = async () => {
  try {
    const response = await getDatasources({ is_enabled: true })
    availableDatasources.value = response.items
  } catch (error) {
    console.error('加载可用数据源失败:', error)
    ElMessage.error('加载可用数据源失败')
  }
}

/**
 * 搜索用户
 */
const searchUsers = async (query: string) => {
  if (!query) {
    userOptions.value = []
    return
  }
  
  try {
    userSearchLoading.value = true
    // 这里应该调用用户搜索API
    // const response = await searchUsers({ search: query })
    // userOptions.value = response.items
    
    // 模拟数据
    userOptions.value = [
      { id: 1, username: 'user1', email: 'user1@example.com' },
      { id: 2, username: 'user2', email: 'user2@example.com' }
    ].filter(user => 
      user.username.includes(query) || user.email.includes(query)
    )
  } catch (error) {
    console.error('搜索用户失败:', error)
  } finally {
    userSearchLoading.value = false
  }
}

/**
 * 显示分配数据源对话框
 */
const handleShowAssignDatasourceDialog = async () => {
  showAssignDatasourceDialog.value = true
  await loadAvailableDatasources()
}

/**
 * 编辑项目
 */
const handleEditProject = () => {
  // 触发父组件的编辑事件
  emit('refresh')
  visible.value = false
}

/**
 * 编辑成员
 */
const handleEditMember = (member: ProjectMember) => {
  // 实现编辑成员逻辑
  console.log('编辑成员:', member)
}

/**
 * 移除成员
 */
const handleRemoveMember = async (member: ProjectMember) => {
  if (!props.project) return
  
  try {
    await ElMessageBox.confirm(
      `确定要移除成员 "${member.username}" 吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await removeProjectMember(props.project.id, member.id)
    ElMessage.success('移除成功')
    loadMembers()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除成员失败:', error)
      ElMessage.error('移除成员失败')
    }
  }
}

/**
 * 添加成员
 */
const handleAddMember = async () => {
  if (!props.project) return
  
  try {
    await memberFormRef.value?.validate()
    memberSubmitting.value = true
    
    await addProjectMember(props.project.id, memberForm)
    ElMessage.success('添加成功')
    showAddMemberDialog.value = false
    loadMembers()
  } catch (error) {
    console.error('添加成员失败:', error)
    ElMessage.error('添加成员失败')
  } finally {
    memberSubmitting.value = false
  }
}

/**
 * 编辑数据源
 */
const handleEditDatasource = (datasource: ProjectDatasource) => {
  // 实现编辑数据源逻辑
  console.log('编辑数据源:', datasource)
}

/**
 * 移除数据源
 */
const handleRemoveDatasource = async (datasource: ProjectDatasource) => {
  if (!props.project) return
  
  try {
    await ElMessageBox.confirm(
      `确定要移除数据源 "${datasource.datasource_name}" 吗？`,
      '确认移除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await removeProjectDatasource(props.project.id, datasource.id)
    ElMessage.success('移除成功')
    loadDatasources()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('移除数据源失败:', error)
      ElMessage.error('移除数据源失败')
    }
  }
}

/**
 * 分配数据源
 */
const handleAssignDatasource = async () => {
  if (!props.project) return
  
  try {
    await datasourceFormRef.value?.validate()
    datasourceSubmitting.value = true
    
    await assignProjectDatasource(props.project.id, datasourceForm)
    ElMessage.success('分配成功')
    showAssignDatasourceDialog.value = false
    loadDatasources()
  } catch (error) {
    console.error('分配数据源失败:', error)
    ElMessage.error('分配数据源失败')
  } finally {
    datasourceSubmitting.value = false
  }
}

/**
 * 成员对话框关闭
 */
const handleMemberDialogClose = () => {
  memberFormRef.value?.resetFields()
  Object.assign(memberForm, {
    user_id: 0,
    role: 'member',
    notes: ''
  })
  userOptions.value = []
}

/**
 * 数据源对话框关闭
 */
const handleDatasourceDialogClose = () => {
  datasourceFormRef.value?.resetFields()
  Object.assign(datasourceForm, {
    datasource_id: 0,
    access_type: 'read_only',
    notes: ''
  })
}

/**
 * 对话框关闭
 */
const handleClose = () => {
  activeTab.value = 'members'
  memberList.value = []
  datasourceList.value = []
  activityList.value = []
}
</script>

<style scoped>
.project-detail {
  max-height: 70vh;
  overflow-y: auto;
}

.detail-card {
  margin-bottom: 20px;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tab-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  font-weight: 500;
}

.text-danger {
  color: #f56c6c;
}

.text-warning {
  color: #e6a23c;
}

:deep(.el-descriptions__label) {
  font-weight: 500;
}

:deep(.el-tabs__content) {
  padding: 20px 0;
}

:deep(.el-table .el-table__cell) {
  padding: 8px 0;
}
</style>