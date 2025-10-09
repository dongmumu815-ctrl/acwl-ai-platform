<template>
  <div class="models-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Box /></el-icon>
            模型管理
          </h1>
          <p class="page-description">管理和部署您的AI模型</p>
        </div>
        <div class="header-right">
          <PermissionButton 
            permission="model:create"
            type="primary" 
            @click="showUploadDialog"
          >
            <el-icon><Upload /></el-icon>
            上传模型
          </PermissionButton>
          <el-button @click="refreshModels">
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
              <el-icon><Box /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总模型数</div>
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
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon training">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.training }}</div>
              <div class="stat-label">训练中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon storage">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatSize(stats.totalSize) }}</div>
              <div class="stat-label">存储占用</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>
    
    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <el-card shadow="never">
        <el-form :model="filters" inline>
          <el-form-item label="搜索">
            <el-input
              v-model="filters.search"
              placeholder="搜索模型名称或描述"
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
              v-model="filters.type"
              placeholder="选择模型类型"
              clearable
              style="width: 150px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="大语言模型" :value="ModelType.LLM" />
              <el-option label="向量模型" :value="ModelType.EMBEDDING" />
              <el-option label="多模态模型" :value="ModelType.MULTIMODAL" />
              <el-option label="其他模型" :value="ModelType.OTHER" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="状态">
            <el-select
              v-model="filters.status"
              placeholder="选择状态"
              clearable
              style="width: 120px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="已激活" value="active" />
              <el-option label="未激活" value="inactive" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="filters.sortBy"
              style="width: 150px"
              @change="handleSort"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="更新时间" value="updated_at" />
              <el-option label="模型大小" value="size" />
              <el-option label="使用次数" value="usage_count" />
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
    
    <!-- 模型列表 -->
    <div class="models-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>模型列表</span>
            <div class="header-actions">
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
              v-for="model in paginatedModels"
              :key="model.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="model-card">
                <div class="model-header">
                  <div class="model-avatar">
                    <img
                      v-if="model.avatar"
                      :src="model.avatar"
                      :alt="model.name"
                    />
                    <el-icon v-else><Box /></el-icon>
                  </div>
                  <div class="model-status">
                    <el-tag
                      :type="model.is_active ? 'success' : 'info'"
                      size="small"
                    >
                      {{ model.is_active ? '已激活' : '未激活' }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="model-content">
                  <h3 class="model-name">{{ model.name }}</h3>
                  <p class="model-description">{{ model.description }}</p>
                  
                  <div class="model-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(model.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                    <el-icon><FolderOpened /></el-icon>
                    <span>{{ formatSize(model.model_size || 0) }}</span>
                  </div>
                  <div class="meta-item">
                    <el-icon><View /></el-icon>
                    <span>{{ getTypeText(model.model_type) }}</span>
                  </div>
                  </div>
                  
                  <div class="model-tags">
                    <el-tag
                      size="small"
                      class="tag-item"
                    >
                      {{ model.framework || 'Unknown' }}
                    </el-tag>
                    <el-tag
                      v-if="model.quantization"
                      size="small"
                      class="tag-item"
                      type="warning"
                    >
                      {{ model.quantization }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="model-actions">
                  <el-button
                    size="small"
                    @click="viewModel(model)"
                  >
                    查看
                  </el-button>
                  <el-button
                    v-if="model.is_active"
                    type="primary"
                    size="small"
                    @click="deployModel(model)"
                  >
                    部署
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="editModel(model)">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item @click="cloneModel(model)">
                          <el-icon><CopyDocument /></el-icon>
                          克隆
                        </el-dropdown-item>
                        <el-dropdown-item @click="downloadModel(model)">
                          <el-icon><Download /></el-icon>
                          下载
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="deleteModel(model)"
                        >
                          <el-icon><Delete /></el-icon>
                          删除
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
            :data="paginatedModels"
            style="width: 100%"
            @sort-change="handleTableSort"
          >
            <el-table-column prop="name" label="模型名称" sortable>
              <template #default="{ row }">
                <div class="model-name-cell">
                  <div class="model-avatar-small">
                    <img
                      v-if="row.avatar"
                      :src="row.avatar"
                      :alt="row.name"
                    />
                    <el-icon v-else><Box /></el-icon>
                  </div>
                  <div class="model-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="description">{{ row.description }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="model_type" label="类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getTypeText(row.model_type) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="is_active" label="状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="row.is_active ? 'success' : 'info'"
                  size="small"
                >
                  {{ row.is_active ? '已激活' : '未激活' }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="model_size" label="大小" width="120" sortable>
              <template #default="{ row }">
                {{ formatSize(row.model_size || 0) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="framework" label="框架" width="120">
              <template #default="{ row }">
                {{ row.framework || 'Unknown' }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="250" fixed="right">
              <template #default="{ row }">
                <div class="table-actions">
                  <PermissionButton 
                    permission="model:read"
                    size="small" 
                    @click="viewModel(row)"
                  >
                    查看
                  </PermissionButton>
                  <PermissionButton
                    v-if="row.is_active"
                    permission="model:deploy"
                    type="primary"
                    size="small"
                    @click="deployModel(row)"
                  >
                    部署
                  </PermissionButton>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <PermissionWrapper permission="model:update">
                          <el-dropdown-item @click="editModel(row)">
                            <el-icon><Edit /></el-icon>
                            编辑
                          </el-dropdown-item>
                        </PermissionWrapper>
                        <PermissionWrapper permission="model:create">
                          <el-dropdown-item @click="cloneModel(row)">
                            <el-icon><CopyDocument /></el-icon>
                            克隆
                          </el-dropdown-item>
                        </PermissionWrapper>
                        <PermissionWrapper permission="model:read">
                          <el-dropdown-item @click="downloadModel(row)">
                            <el-icon><Download /></el-icon>
                            下载
                          </el-dropdown-item>
                        </PermissionWrapper>
                        <PermissionWrapper permission="model:delete">
                          <el-dropdown-item
                            divided
                            @click="deleteModel(row)"
                          >
                            <el-icon><Delete /></el-icon>
                            删除
                          </el-dropdown-item>
                        </PermissionWrapper>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="pagination.currentPage"
            v-model:page-size="pagination.pageSize"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
    
    <!-- 上传模型对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传模型"
      width="600px"
      :before-close="handleCloseUpload"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-width="100px"
      >
        <el-form-item label="模型名称" prop="name">
          <el-input
            v-model="uploadForm.name"
            placeholder="请输入模型名称"
          />
        </el-form-item>
        
        <el-form-item label="模型类型" prop="type">
          <el-select
            v-model="uploadForm.type"
            placeholder="请选择模型类型"
            style="width: 100%"
          >
            <el-option label="大语言模型" :value="ModelType.LLM" />
            <el-option label="向量模型" :value="ModelType.EMBEDDING" />
            <el-option label="多模态模型" :value="ModelType.MULTIMODAL" />
            <el-option label="其他模型" :value="ModelType.OTHER" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入模型描述"
          />
        </el-form-item>
        
        <el-form-item label="标签">
          <el-select
            v-model="uploadForm.tags"
            multiple
            filterable
            allow-create
            placeholder="请选择或输入标签"
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
        
        <el-form-item label="模型文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            accept=".bin,.safetensors,.ckpt,.pth,.pt"
            @change="handleFileChange"
          >
            <el-button>
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 .bin, .safetensors, .ckpt, .pth, .pt 格式，文件大小不超过 10GB
              </div>
            </template>
          </el-upload>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitUpload"
            :loading="uploading"
          >
            上传
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadInstance, FormInstance, FormRules } from 'element-plus'
import {
  Box,
  Upload,
  Refresh,
  VideoPlay,
  Loading,
  FolderOpened,
  Search,
  RefreshLeft,
  Grid,
  List,
  Calendar,
  View,
  MoreFilled,
  Edit,
  Download,
  Delete,
  CopyDocument
} from '@element-plus/icons-vue'
import { modelApi, type Model, ModelType } from '@/api/models'
import { PermissionButton, PermissionWrapper } from '@/components/Permission'

const router = useRouter()

// 响应式数据
const viewMode = ref('grid')
const uploadDialogVisible = ref(false)
const uploadFormRef = ref()
const uploading = ref(false)
const loading = ref(false)

// 统计数据
const stats = reactive({
  total: 0,
  active: 0,
  training: 0,
  totalSize: 0
})

// 筛选条件
const filters = reactive({
  search: '',
  type: '',
  status: '',
  sortBy: 'created_at'
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 模型列表
const models = ref<Model[]>([])

// 上传表单
const uploadForm = reactive({
  name: '',
  version: '1.0',
  type: ModelType.LLM,
  description: '',
  framework: '',
  tags: [] as string[],
  file: null as File | null
})

// 常用标签
const commonTags = [
  'GPT', 'BERT', 'Transformer', 'CNN', 'RNN',
  '自然语言处理', '计算机视觉', '语音识别', '推荐系统'
]

// 表单验证规则
const uploadRules: FormRules = {
  name: [
    { required: true, message: '请输入模型名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择模型类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入模型描述', trigger: 'blur' }
  ],
  file: [
    { required: true, message: '请选择模型文件', trigger: 'change' }
  ]
}

// 计算属性
const filteredModels = computed(() => {
  let result = [...models.value]
  
  // 搜索过滤
  if (filters.search) {
    const searchTerm = filters.search.toLowerCase()
    result = result.filter(
      model => 
        model.name.toLowerCase().includes(searchTerm) ||
        model.description?.toLowerCase().includes(searchTerm)
    )
  }
  
  // 类型过滤
  if (filters.type) {
    result = result.filter(model => model.model_type === filters.type)
  }
  
  // 状态过滤
  if (filters.status) {
    if (filters.status === 'active') {
      result = result.filter(model => model.is_active)
    } else if (filters.status === 'inactive') {
      result = result.filter(model => !model.is_active)
    }
  }
  
  // 排序
  result.sort((a, b) => {
    const field = filters.sortBy
    if (field === 'created_at' || field === 'updated_at') {
      return new Date(b[field]).getTime() - new Date(a[field]).getTime()
    }
    if (field === 'size') {
      return (b.model_size || 0) - (a.model_size || 0)
    }
    return 0
  })
  
  return result
})

const paginatedModels = computed(() => {
  // 由于使用服务器端分页，直接返回从API获取的模型列表
  return models.value
})

// 方法
const formatSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    ready: 'success',
    running: 'primary',
    training: 'warning',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    ready: '就绪',
    running: '运行中',
    training: '训练中',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const getTypeText = (type: ModelType) => {
  const typeMap: Record<ModelType, string> = {
    [ModelType.LLM]: '大语言模型',
    [ModelType.EMBEDDING]: '向量模型',
    [ModelType.MULTIMODAL]: '多模态模型',
    [ModelType.OTHER]: '其他模型'
  }
  return typeMap[type] || type
}

const handleSearch = () => {
  pagination.currentPage = 1
  refreshModels()
}

const handleFilter = () => {
  pagination.currentPage = 1
  refreshModels()
}

const handleSort = () => {
  pagination.currentPage = 1
  refreshModels()
}

const resetFilters = () => {
  filters.search = ''
  filters.type = ''
  filters.status = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
  refreshModels()
}

const handleTableSort = ({ prop, order }: any) => {
  if (order) {
    filters.sortBy = prop
    pagination.currentPage = 1
    refreshModels()
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  refreshModels()
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  refreshModels()
}

const refreshModels = async () => {
  try {
    loading.value = true
    
    // 调用实际的API
    const response = await modelApi.getModels({
      page: pagination.currentPage,
      size: pagination.pageSize,
      search: filters.search || undefined,
      model_type: filters.type as ModelType || undefined,
      is_active: filters.status === 'active' ? true : filters.status === 'inactive' ? false : undefined
    })
    
    console.log('API响应:', response)
    
    // 检查响应数据结构
    if (!response || typeof response !== 'object') {
      throw new Error('API响应格式错误：响应为空或不是对象')
    }
    
    if (!response.items || !Array.isArray(response.items)) {
      throw new Error('API响应格式错误：缺少items字段或items不是数组')
    }
    
    models.value = response.items
    pagination.total = response.total || 0
    
    // 更新统计数据
    updateStats()
  } catch (error: any) {
    console.error('刷新模型列表失败:', error)
    ElMessage.error(error.response?.data?.message || error.message || '刷新失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const updateStats = () => {
  stats.total = models.value.length
  stats.active = models.value.filter(m => m.is_active).length
  stats.training = 0 // 训练中的模型需要从部署状态获取
  stats.totalSize = models.value.reduce((sum, m) => sum + (m.model_size || 0), 0)
}

const showUploadDialog = () => {
  uploadDialogVisible.value = true
}

const handleCloseUpload = () => {
  uploadForm.name = ''
  uploadForm.version = '1.0'
  uploadForm.type = ModelType.LLM
  uploadForm.description = ''
  uploadForm.framework = ''
  uploadForm.tags = []
  uploadForm.file = null
  uploadDialogVisible.value = false
}

const handleFileChange = (file: any) => {
  uploadForm.file = file.raw
}

const submitUpload = async () => {
  if (!uploadFormRef.value) return
  
  try {
    await uploadFormRef.value.validate()
    uploading.value = true
    
    // 调用实际的API上传文件
    const formData = new FormData()
    formData.append('file', uploadForm.file!)
    formData.append('name', uploadForm.name)
    formData.append('version', uploadForm.version)
    formData.append('model_type', uploadForm.type)
    formData.append('description', uploadForm.description)
    formData.append('framework', uploadForm.framework)
    if (uploadForm.tags.length > 0) {
      formData.append('tags', JSON.stringify(uploadForm.tags))
    }
    
    await modelApi.uploadModel(formData)
    
    ElMessage.success('模型上传成功')
    handleCloseUpload()
    refreshModels()
  } catch (error: any) {
    console.error('上传模型失败:', error)
    ElMessage.error(error.response?.data?.message || '上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
}

const viewModel = (model: Model) => {
  router.push(`/models/${model.id}`)
}

const deployModel = (model: Model) => {
  router.push(`/deployments/create?modelId=${model.id}`)
}

const editModel = (model: Model) => {
  router.push(`/models/${model.id}/edit`)
}

const cloneModel = async (model: Model) => {
  try {
    const { value: newName } = await ElMessageBox.prompt(
      `请输入克隆模型的新名称：`,
      '克隆模型',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: `${model.name}-copy`,
        inputPattern: /^.{1,100}$/,
        inputErrorMessage: '模型名称长度应在1-100个字符之间'
      }
    )
    
    await modelApi.cloneModel(model.id, newName)
    
    ElMessage.success('模型克隆成功')
    refreshModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('克隆模型失败:', error)
      ElMessage.error(error.response?.data?.message || '克隆失败，请稍后重试')
    }
  }
}

const downloadModel = async (model: Model) => {
  try {
    ElMessage.info('正在准备下载链接...')
    const response = await modelApi.getDownloadUrl(model.id)
    window.open(response.data.url)
  } catch (error: any) {
    console.error('获取下载链接失败:', error)
    ElMessage.error(error.response?.data?.message || '下载失败，请稍后重试')
  }
}

const deleteModel = async (model: Model) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除模型 "${model.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await modelApi.deleteModel(model.id)
    
    ElMessage.success('模型删除成功')
    refreshModels()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除模型失败:', error)
      ElMessage.error(error.response?.data?.message || '删除失败，请稍后重试')
    }
  }
}

onMounted(() => {
  refreshModels()
})
</script>

<style lang="scss" scoped>
.models-page {
  padding: 20px;
  
  .page-header {
    margin-bottom: 20px;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      
      .header-left {
        .page-title {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin: 0 0 8px 0;
        }
        
        .page-description {
          color: var(--el-text-color-regular);
          margin: 0;
        }
      }
      
      .header-right {
        display: flex;
        gap: 12px;
      }
    }
  }
  
  .stats-cards {
    margin-bottom: 20px;
    
    .stat-card {
      display: flex;
      align-items: center;
      padding: 20px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      .stat-icon {
        width: 48px;
        height: 48px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 16px;
        
        .el-icon {
          font-size: 24px;
          color: white;
        }
        
        &.total {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        
        &.active {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.training {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.storage {
          background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }
      }
      
      .stat-content {
        .stat-value {
          font-size: 24px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
        }
      }
    }
  }
  
  .filter-section {
    margin-bottom: 20px;
    
    :deep(.el-card__body) {
      padding: 16px 20px;
    }
  }
  
  .models-list {
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .header-actions {
        display: flex;
        align-items: center;
        gap: 12px;
      }
    }
    
    .grid-view {
      .model-card {
        background: white;
        border: 1px solid var(--el-border-color-light);
        border-radius: 8px;
        padding: 16px;
        transition: all 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
        
        &:hover {
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
          transform: translateY(-2px);
        }
        
        .model-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          
          .model-avatar {
            width: 48px;
            height: 48px;
            border-radius: 8px;
            background: var(--el-fill-color-light);
            display: flex;
            align-items: center;
            justify-content: center;
            
            img {
              width: 100%;
              height: 100%;
              border-radius: 8px;
              object-fit: cover;
            }
            
            .el-icon {
              font-size: 24px;
              color: var(--el-text-color-placeholder);
            }
          }
        }
        
        .model-content {
          flex: 1;
          
          .model-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 8px 0;
            line-height: 1.4;
          }
          
          .model-description {
            font-size: 14px;
            color: var(--el-text-color-regular);
            line-height: 1.5;
            margin: 0 0 12px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          
          .model-meta {
            margin-bottom: 12px;
            
            .meta-item {
              display: flex;
              align-items: center;
              gap: 4px;
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 4px;
              
              &:last-child {
                margin-bottom: 0;
              }
              
              .el-icon {
                font-size: 14px;
              }
            }
          }
          
          .model-tags {
            margin-bottom: 16px;
            
            .tag-item {
              margin-right: 6px;
              margin-bottom: 6px;
            }
          }
        }
        
        .model-actions {
          display: flex;
          justify-content: space-between;
          align-items: center;
          gap: 8px;
          
          .el-button {
            flex: 1;
            
            &:last-child {
              flex: none;
              width: auto;
            }
          }
        }
      }
    }
    
    .list-view {
      .model-name-cell {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .model-avatar-small {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          background: var(--el-fill-color-light);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          
          img {
            width: 100%;
            height: 100%;
            border-radius: 6px;
            object-fit: cover;
          }
          
          .el-icon {
            font-size: 16px;
            color: var(--el-text-color-placeholder);
          }
        }
        
        .model-info {
          .name {
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 2px;
          }
          
          .description {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            display: -webkit-box;
            -webkit-line-clamp: 1;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
        }
      }
    }
    
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 20px;
    }
    
    .table-actions {
      display: flex;
      gap: 8px;
      align-items: center;
      
      .el-button {
        margin: 0;
      }
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .models-page {
    padding: 16px;
    
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-right {
          width: 100%;
          justify-content: flex-end;
        }
      }
    }
    
    .filter-section {
      :deep(.el-form) {
        .el-form-item {
          margin-bottom: 16px;
          
          .el-input,
          .el-select {
            width: 100% !important;
          }
        }
      }
    }
    
    .models-list {
      .grid-view {
        .model-card {
          .model-actions {
            flex-direction: column;
            
            .el-button {
              width: 100%;
            }
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .models-page {
    .stats-cards {
      .stat-card {
        background: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
      }
    }
    
    .models-list {
      .grid-view {
        .model-card {
          background: var(--el-bg-color-page);
          border-color: var(--el-border-color);
        }
      }
    }
  }
}
</style>