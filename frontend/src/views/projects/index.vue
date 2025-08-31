<template>
  <div class="projects-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Folder /></el-icon>
            项目管理
          </h1>
          <p class="page-description">管理和监控您的AI项目</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            创建项目
          </el-button>
          <el-button @click="refreshProjects">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总项目数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon active">
              <el-icon><VideoPlay /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.active }}</div>
              <div class="stat-label">进行中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon completed">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.completed }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon resources">
              <el-icon><User /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.totalMembers) }}</div>
              <div class="stat-label">团队成员</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="searchForm" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="searchForm.search"
              placeholder="搜索项目名称或描述"
              clearable
              style="width: 250px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-form-item>
          
          <el-form-item label="类型">
            <el-select
              v-model="searchForm.project_type"
              placeholder="选择类型"
              clearable
              style="width: 140px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="type in PROJECT_TYPES"
                :key="type.value"
                :label="type.label"
                :value="type.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.status"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="status in PROJECT_STATUS_OPTIONS"
                :key="status.value"
                :label="status.label"
                :value="status.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="优先级">
            <el-select
              v-model="searchForm.priority"
              placeholder="选择优先级"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option
                v-for="priority in PROJECT_PRIORITY_OPTIONS"
                :key="priority.value"
                :label="priority.label"
                :value="priority.value"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="searchForm.sortBy"
              style="width: 150px"
              @change="handleSort"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="更新时间" value="updated_at" />
              <el-option label="项目名称" value="name" />
              <el-option label="截止日期" value="end_date" />
            </el-select>
          </el-form-item>
          
          <el-form-item>
            <el-button @click="resetFilters">
              <el-icon><RefreshLeft /></el-icon>
              重置
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>

    <!-- 项目列表 -->
    <div class="projects-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>项目列表</span>
            <div class="header-actions">
              <el-button
                v-if="selectedRows.length > 0"
                type="danger"
                size="small"
                @click="handleBatchDelete"
              >
                批量删除
              </el-button>
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button value="grid">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
                <el-radio-button value="list">
                  <el-icon><List /></el-icon>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </template>
        
        <!-- 网格视图 -->
        <div v-if="viewMode === 'grid'" class="grid-view">
          <el-row :gutter="20">
            <el-col
              v-for="project in paginatedProjects"
              :key="project.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="project-card">
                <div class="project-header">
                  <div class="project-info">
                    <h3 class="project-name">{{ project.name }}</h3>
                    <p class="project-description">{{ project.description || '暂无描述' }}</p>
                  </div>
                  <div class="project-status">
                    <el-tag
                      :type="getProjectStatusConfig(project.status).type"
                      size="small"
                    >
                      {{ getProjectStatusConfig(project.status).label }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="project-content">
                  <div class="project-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(project.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><User /></el-icon>
                      <span>{{ project.creator_username }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Flag /></el-icon>
                      <span>{{ getProjectPriorityConfig(project.priority).label }}</span>
                    </div>
                  </div>
                  
                  <!-- 项目类型和预算 -->
                  <div class="project-details">
                    <div class="detail-item">
                      <div class="detail-label">
                        <el-icon><Box /></el-icon>
                        <span>类型</span>
                      </div>
                      <div class="detail-value">
                        <el-tag :type="getProjectTypeConfig(project.project_type).type" size="small">
                          {{ getProjectTypeLabel(project.project_type) }}
                        </el-tag>
                      </div>
                    </div>
                    
                    <div class="detail-item" v-if="project.members_count">
                      <div class="detail-label">
                        <el-icon><User /></el-icon>
                        <span>成员</span>
                      </div>
                      <div class="detail-value">
                        {{ project.members_count }}人
                      </div>
                    </div>
                    
                    <div class="detail-item" v-if="project.end_date">
                      <div class="detail-label">
                        <el-icon><Clock /></el-icon>
                        <span>截止</span>
                      </div>
                      <div class="detail-value" :class="{ 'text-danger': isProjectOverdue(project.end_date), 'text-warning': isProjectNearDeadline(project.end_date) }">
                        {{ formatDate(project.end_date) }}
                      </div>
                    </div>
                  </div>
                  
                  <!-- 项目标签 -->
                  <div class="project-tags" v-if="project.tags && Object.keys(project.tags).length > 0">
                    <el-tag
                      v-for="tag in Object.keys(project.tags).slice(0, 3)"
                      :key="tag"
                      size="small"
                      effect="plain"
                    >
                      {{ tag }}
                    </el-tag>
                    <el-tag v-if="Object.keys(project.tags).length > 3" size="small" effect="plain">
                      +{{ Object.keys(project.tags).length - 3 }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="project-actions">
                  <el-button size="small" @click="handleViewProject(project)">
                    查看
                  </el-button>
                  <el-button type="warning" size="small" @click="handleEditProject(project)">
                    编辑
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="handleViewProject(project)">
                          <el-icon><View /></el-icon>
                          查看详情
                        </el-dropdown-item>
                        <el-dropdown-item @click="handleEditProject(project)">
                          <el-icon><Edit /></el-icon>
                          编辑项目
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="handleDeleteProject(project)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除项目
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            v-loading="loading"
            :data="paginatedProjects"
            @selection-change="handleSelectionChange"
            stripe
          >
          <el-table-column type="selection" width="55" />
          <el-table-column prop="name" label="项目名称" min-width="150">
            <template #default="{ row }">
              <el-link type="primary" @click="handleViewProject(row)">
                {{ row.name }}
              </el-link>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="项目描述" min-width="200" show-overflow-tooltip />
          <el-table-column prop="project_type" label="项目类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getProjectTypeConfig(row.project_type).type">
                {{ getProjectTypeLabel(row.project_type) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getProjectStatusConfig(row.status).type">
                {{ getProjectStatusConfig(row.status).label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="priority" label="优先级" width="100">
            <template #default="{ row }">
              <el-tag :type="getProjectPriorityConfig(row.priority).type">
                {{ getProjectPriorityConfig(row.priority).label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="members_count" label="成员数" width="120">
            <template #default="{ row }">
              {{ row.members_count || 0 }}人
            </template>
          </el-table-column>
          <el-table-column prop="start_date" label="开始日期" width="120">
            <template #default="{ row }">
              {{ row.start_date ? formatDate(row.start_date) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="end_date" label="结束日期" width="120">
            <template #default="{ row }">
              <span :class="{ 'text-danger': isProjectOverdue(row.end_date), 'text-warning': isProjectNearDeadline(row.end_date) }">
                {{ row.end_date ? formatDate(row.end_date) : '-' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="creator_name" label="创建者" width="120" />
          <el-table-column prop="created_at" label="创建时间" width="160">
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="200" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="handleViewProject(row)">
                查看
              </el-button>
              <el-button type="warning" size="small" @click="handleEditProject(row)">
                编辑
              </el-button>
              <el-button type="danger" size="small" @click="handleDeleteProject(row)">
                删除
              </el-button>
            </template>
          </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.size"
            :total="filteredProjects.length"
            :page-sizes="[10, 20, 50, 100]"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>

    <!-- 创建/编辑项目对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editingProject ? '编辑项目' : '创建项目'"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="projectFormRef"
        :model="projectForm"
        :rules="projectFormRules"
        label-width="100px"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="projectForm.name" placeholder="请输入项目名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="项目类型" prop="project_type">
              <el-select v-model="projectForm.project_type" placeholder="请选择项目类型">
                <el-option
                  v-for="type in PROJECT_TYPES"
                  :key="type.value"
                  :label="type.label"
                  :value="type.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="项目状态" prop="status">
              <el-select v-model="projectForm.status" placeholder="请选择项目状态">
                <el-option
                  v-for="status in PROJECT_STATUS_OPTIONS"
                  :key="status.value"
                  :label="status.label"
                  :value="status.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="projectForm.priority" placeholder="请选择优先级">
                <el-option
                  v-for="priority in PROJECT_PRIORITY_OPTIONS"
                  :key="priority.value"
                  :label="priority.label"
                  :value="priority.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="开始日期">
              <el-date-picker
                v-model="projectForm.start_date"
                type="date"
                placeholder="请选择开始日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="结束日期">
              <el-date-picker
                v-model="projectForm.end_date"
                type="date"
                placeholder="请选择结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="团队规模">
          <el-input-number
            v-model="projectForm.members_count"
            :min="1"
            :max="100"
            placeholder="请输入团队成员数量"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input
            v-model="projectForm.description"
            type="textarea"
            :rows="4"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="标签">
          <el-select
            v-model="tempTags"
            multiple
            filterable
            allow-create
            placeholder="请输入或选择标签"
            style="width: 100%"
          >
            <el-option
              v-for="tag in commonTags"
              :key="tag"
              :label="tag"
              :value="tag"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">
          {{ editingProject ? '更新' : '创建' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 项目详情对话框 -->
    <ProjectDetailDialog
      v-model="showDetailDialog"
      :project="selectedProject"
      @refresh="loadProjects"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Search,
  Refresh,
  Folder,
  VideoPlay,
  CircleCheck,
  RefreshLeft,
  Grid,
  List,
  Calendar,
  User,
  Flag,
  Box,
  Clock,
  MoreFilled,
  View,
  Edit,
  Delete
} from '@element-plus/icons-vue'
import {
  getProjects,
  createProject,
  updateProject,
  deleteProject,
  type Project,
  type ProjectForm,
  type ProjectQueryParams,
  ProjectType,
  ProjectStatus,
  ProjectPriority,
  PROJECT_TYPES,
  PROJECT_STATUS_OPTIONS,
  PROJECT_PRIORITY_OPTIONS,
  getProjectTypeLabel,
  getProjectStatusConfig,
  getProjectPriorityConfig,
  isProjectNearDeadline,
  isProjectOverdue
} from '@/api/projects'
import { formatDate, formatDateTime } from '@/utils/date'
import ProjectDetailDialog from './components/ProjectDetailDialog.vue'

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const editingProject = ref<Project | null>(null)
const selectedProject = ref<Project | null>(null)
const selectedRows = ref<Project[]>([])
const projectFormRef = ref()
const viewMode = ref('grid')

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  completed: 0,
  totalMembers: 0
})

// 项目列表数据
const projectList = ref<Project[]>([])

// 分页数据
const pagination = reactive({
  page: 1,
  size: 10,
  total: 0
})

// 排序选项
const sortOptions = [
  { label: '创建时间', value: 'created_at' },
  { label: '更新时间', value: 'updated_at' },
  { label: '项目名称', value: 'name' },
  { label: '截止日期', value: 'end_date' }
]

// 搜索表单
const searchForm = reactive({
  search: '',
  project_type: undefined,
  status: undefined,
  priority: undefined,
  sortBy: 'created_at'
})

// 项目表单
const projectForm = reactive<ProjectForm>({
  name: '',
  description: '',
  project_type: ProjectType.GENERAL,
  status: ProjectStatus.ACTIVE,
  priority: ProjectPriority.MEDIUM,
  start_date: '',
  end_date: '',
  members_count: undefined,
  tags: {}
})

// 表单验证规则
const projectFormRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 100, message: '项目名称长度在 2 到 100 个字符', trigger: 'blur' }
  ],
  project_type: [
    { required: true, message: '请选择项目类型', trigger: 'change' }
  ],
  status: [
    { required: true, message: '请选择项目状态', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  members_count: [
    { type: 'number', min: 1, max: 100, message: '团队成员数量应在 1-100 人之间', trigger: 'blur' }
  ]
}

// 常用标签
const commonTags = ref([
  'AI', '机器学习', '深度学习', '自然语言处理', '计算机视觉',
  '数据挖掘', '推荐系统', '语音识别', '图像识别', '预测分析'
])

// 临时标签数组（用于UI显示）
const tempTags = ref<string[]>([])

// 计算属性
const filteredProjects = computed(() => {
  let filtered = projectList.value

  if (searchForm.search) {
    filtered = filtered.filter(project => 
      project.name.toLowerCase().includes(searchForm.search.toLowerCase()) ||
      project.description?.toLowerCase().includes(searchForm.search.toLowerCase())
    )
  }

  if (searchForm.project_type) {
    filtered = filtered.filter(project => project.project_type === searchForm.project_type)
  }

  if (searchForm.status) {
    filtered = filtered.filter(project => project.status === searchForm.status)
  }

  if (searchForm.priority) {
    filtered = filtered.filter(project => project.priority === searchForm.priority)
  }

  // 排序
  if (searchForm.sortBy) {
    filtered.sort((a, b) => {
      const aValue = a[searchForm.sortBy as keyof Project]
      const bValue = b[searchForm.sortBy as keyof Project]
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return bValue.localeCompare(aValue) // 降序
      }
      
      if (aValue instanceof Date && bValue instanceof Date) {
        return bValue.getTime() - aValue.getTime() // 降序
      }
      
      return 0
    })
  }

  return filtered
})

// 分页后的项目列表
const paginatedProjects = computed(() => {
  const start = (pagination.page - 1) * pagination.size
  const end = start + pagination.size
  return filteredProjects.value.slice(start, end)
})

const getProjectTypeConfig = computed(() => {
  return (type: string) => {
    const typeOption = PROJECT_TYPES.find(t => t.value === type)
    return typeOption ? { type: 'info' } : { type: 'info' }
  }
})

// 方法

// 更新统计数据
const updateStats = () => {
  stats.total = projectList.value.length
  stats.active = projectList.value.filter(p => p.status === 'in_progress').length
  stats.completed = projectList.value.filter(p => p.status === 'completed').length
  stats.totalMembers = projectList.value.reduce((sum, p) => sum + (p.members_count || 0), 0)
}

/**
 * 加载项目列表
 */
const loadProjects = async () => {
  try {
    loading.value = true
    const params = {
      ...searchForm,
      page: pagination.page,
      size: pagination.size
    }
    const response = await getProjects(params)
    projectList.value = response.items
    pagination.total = response.total
    updateStats()
  } catch (error) {
    console.error('加载项目列表失败:', error)
    ElMessage.error('加载项目列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 搜索项目
 */
const handleSearch = () => {
  pagination.page = 1
}

/**
 * 筛选项目
 */
const handleFilter = () => {
  pagination.page = 1
}

/**
 * 排序项目
 */
const handleSort = () => {
  pagination.page = 1
}

/**
 * 重置筛选
 */
const resetFilters = () => {
  Object.assign(searchForm, {
    search: '',
    project_type: undefined,
    status: undefined,
    priority: undefined,
    sortBy: 'created_at'
  })
  pagination.page = 1
}

/**
 * 刷新项目列表
 */
const refreshProjects = () => {
  loadProjects()
}

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

/**
 * 分页大小改变
 */
const handleSizeChange = (size: number) => {
  pagination.size = size
  pagination.page = 1
  loadProjects()
}

/**
 * 当前页改变
 */
const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadProjects()
}

/**
 * 选择行改变
 */
const handleSelectionChange = (selection: Project[]) => {
  selectedRows.value = selection
}

/**
 * 查看项目详情
 */
const handleViewProject = (project: Project) => {
  selectedProject.value = project
  showDetailDialog.value = true
}

/**
 * 编辑项目
 */
const handleEditProject = (project: Project) => {
  editingProject.value = project
  
  // 将字典格式的tags转换为数组格式用于UI显示
  const tagsArray = project.tags && typeof project.tags === 'object' 
    ? Object.keys(project.tags) 
    : []
  tempTags.value = tagsArray
  
  Object.assign(projectForm, {
    name: project.name,
    description: project.description || '',
    project_type: project.project_type,
    status: project.status,
    priority: project.priority,
    start_date: project.start_date || '',
    end_date: project.end_date || '',
    members_count: project.members_count,
    tags: project.tags || {}
  })
  showCreateDialog.value = true
}

/**
 * 删除项目
 */
const handleDeleteProject = async (project: Project) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteProject(project.id)
    ElMessage.success('删除成功')
    loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
      ElMessage.error('删除项目失败')
    }
  }
}

/**
 * 批量删除
 */
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个项目吗？此操作不可恢复。`,
      '确认批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用批量删除API，暂时逐个删除
    for (const project of selectedRows.value) {
      await deleteProject(project.id)
    }
    
    ElMessage.success('批量删除成功')
    loadProjects()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
      ElMessage.error('批量删除失败')
    }
  }
}

/**
 * 提交表单
 */
const handleSubmit = async () => {
  try {
    await projectFormRef.value?.validate()
    submitting.value = true
    
    // 将标签数组转换为字典格式
    const tagsDict: Record<string, any> = {}
    tempTags.value.forEach((tag, index) => {
      tagsDict[tag] = true
    })
    
    const submitData = {
      ...projectForm,
      tags: tagsDict
    }
    
    if (editingProject.value) {
      await updateProject(editingProject.value.id, submitData)
      ElMessage.success('更新成功')
    } else {
      await createProject(submitData)
      ElMessage.success('创建成功')
    }
    
    showCreateDialog.value = false
    loadProjects()
  } catch (error) {
    console.error('提交失败:', error)
    ElMessage.error(editingProject.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

/**
 * 对话框关闭
 */
const handleDialogClose = () => {
  editingProject.value = null
  projectFormRef.value?.resetFields()
  tempTags.value = []
  Object.assign(projectForm, {
    name: '',
    description: '',
    project_type: 'general',
    status: 'active',
    priority: 'medium',
    start_date: '',
    end_date: '',
    members_count: undefined,
    tags: {}
  })
}

// 生命周期
onMounted(() => {
  loadProjects()
})
</script>

<style scoped>
.projects-page {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}

/* 页面头部 */
.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.header-left {
  flex: 1;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 统计卡片 */
.stats-cards {
  margin-bottom: 24px;
}

.stat-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.3s ease;
  height: 100%;
}

.stat-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.stat-icon.total {
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

.stat-icon.active {
  background-color: var(--el-color-success-light-9);
  color: var(--el-color-success);
}

.stat-icon.completed {
  background-color: var(--el-color-info-light-9);
  color: var(--el-color-info);
}

.stat-icon.resources {
  background-color: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 4px 0;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin: 0;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 24px;
}

.filter-section .el-card {
  border: 1px solid var(--el-border-color-light);
}

/* 项目列表 */
.projects-list {
  margin-bottom: 24px;
}

.projects-list .el-card {
  border: 1px solid var(--el-border-color-light);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* 网格视图 */
.grid-view {
  min-height: 400px;
}

.project-card {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 20px;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
  gap: 12px;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-name {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin: 0 0 8px 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.project-description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  line-height: 1.4;
}

.project-status {
  flex-shrink: 0;
}

.project-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-meta {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.project-details {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.detail-label {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-regular);
  flex-shrink: 0;
}

.detail-value {
  font-size: 12px;
  color: var(--el-text-color-primary);
  text-align: right;
}

.project-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.project-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: auto;
  padding-top: 16px;
  border-top: 1px solid var(--el-border-color-lighter);
  gap: 8px;
}

/* 列表视图 */
.list-view {
  min-height: 400px;
}

/* 分页 */
.pagination-wrapper {
  margin-top: 20px;
  text-align: center;
}

/* 工具类 */
.text-danger {
  color: var(--el-color-danger) !important;
}

.text-warning {
  color: var(--el-color-warning) !important;
}

/* 表单样式 */
:deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 16px;
}

:deep(.el-table .el-table__cell) {
  padding: 12px 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .projects-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-right {
    justify-content: center;
  }
  
  .card-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .header-actions {
    justify-content: center;
  }
  
  .project-header {
    flex-direction: column;
    align-items: stretch;
    gap: 8px;
  }
  
  .project-status {
    align-self: flex-start;
  }
  
  .detail-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .detail-value {
    text-align: left;
  }
  
  .project-actions {
    flex-direction: column;
    gap: 8px;
  }
  
  :deep(.el-form--inline) {
    display: flex;
    flex-direction: column;
  }
  
  :deep(.el-form--inline .el-form-item) {
    margin-right: 0;
    width: 100%;
  }
}

@media (max-width: 480px) {
  .page-title {
    font-size: 24px;
  }
  
  .stat-value {
    font-size: 20px;
  }
  
  .project-card {
    padding: 16px;
  }
}

/* 暗色主题适配 */
.dark .projects-page {
  background-color: var(--el-bg-color-page);
}

.dark .stat-card,
.dark .project-card {
  background: var(--el-bg-color);
  border-color: var(--el-border-color);
}

.dark .stat-card:hover,
.dark .project-card:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
</style>