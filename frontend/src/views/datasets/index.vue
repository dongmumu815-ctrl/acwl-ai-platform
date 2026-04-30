<template>
  <div class="datasets-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><FolderOpened /></el-icon>
            数据集管理
          </h1>
          <p class="page-description">管理和处理您的训练数据集</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="showUploadDialog">
            <el-icon><Upload /></el-icon>
            上传数据集
          </el-button>
          <el-button @click="refreshDatasets">
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
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总数据集</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon samples">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.totalSamples) }}</div>
              <div class="stat-label">总样本数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon storage">
              <el-icon><Files /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatSize(stats.totalSize) }}</div>
              <div class="stat-label">存储占用</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon processing">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.processing }}</div>
              <div class="stat-label">处理中</div>
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
              placeholder="搜索数据集名称或描述"
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
              placeholder="选择数据类型"
              clearable
              style="width: 150px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="文本" value="text" />
              <el-option label="图像" value="image" />
              <el-option label="音频" value="audio" />
              <el-option label="视频" value="video" />
              <el-option label="表格" value="tabular" />
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
              <el-option label="就绪" value="ready" />
              <el-option label="处理中" value="processing" />
              <el-option label="错误" value="error" />
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
              <el-option label="数据集大小" value="size" />
              <el-option label="样本数量" value="sample_count" />
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
    
    <!-- 数据集列表 -->
    <div class="datasets-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>数据集列表</span>
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
        <div v-if="viewMode === 'grid'" class="grid-view" v-loading="loading">
          <el-row :gutter="20">
            <el-col
              v-for="dataset in datasets"
              :key="dataset.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="dataset-card">
                <div class="dataset-header">
                  <div class="dataset-type">
                    <el-icon class="type-icon">
                      <component :is="getTypeIcon(dataset.dataset_type)" />
                    </el-icon>
                  </div>
                  <div class="dataset-status">
                    <el-tag
                      :type="getStatusType(dataset.status)"
                      size="small"
                      :class="{ 'status-processing': dataset.status === 'processing' }"
                    >
                      {{ getStatusText(dataset.status) }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="dataset-content">
                  <h3 class="dataset-name">{{ dataset.name }}</h3>
                  <p class="dataset-description">{{ dataset.description }}</p>
                  
                  <div class="dataset-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(dataset.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Document /></el-icon>
                      <span>{{ formatNumber(dataset.record_count) }} 样本</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Files /></el-icon>
                      <span>{{ formatSize(dataset.size) }}</span>
                    </div>
                  </div>
                  
                  <div class="dataset-tags" v-if="dataset.tags && dataset.tags.length">
                    <el-tag
                      v-for="tag in dataset.tags"
                      :key="tag"
                      size="small"
                      class="tag-item"
                    >
                      {{ tag }}
                    </el-tag>
                  </div>
                  
                  <!-- 数据预览 -->
                  <div class="dataset-preview" v-if="dataset.preview">
                    <div class="preview-label">数据预览:</div>
                    <div class="preview-content">
                      <div
                        v-if="dataset.dataset_type === 'image'"
                        class="image-preview"
                      >
                        <img
                          v-for="(img, index) in dataset.preview.slice(0, 4)"
                          :key="index"
                          :src="img"
                          :alt="`Sample ${index + 1}`"
                          class="preview-image"
                        />
                      </div>
                      <div
                        v-else-if="dataset.dataset_type === 'text'"
                        class="text-preview"
                      >
                        <div
                          v-for="(text, index) in dataset.preview.slice(0, 3)"
                          :key="index"
                          class="preview-text"
                        >
                          {{ text }}
                        </div>
                      </div>
                      <div v-else class="generic-preview">
                        <el-icon><View /></el-icon>
                        <span>{{ dataset.preview.length }} 个样本</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div class="dataset-actions">
                  <el-button
                    size="small"
                    @click="previewDataset(dataset)"
                  >
                    预览数据
                  </el-button>
                  <el-button
                    size="small"
                    @click="editDataset(dataset)"
                  >
                    编辑
                  </el-button>
                  <el-button
                    size="small"
                    @click="downloadDataset(dataset)"
                  >
                    下载
                  </el-button>
                  <el-button
                    size="small"
                    type="danger"
                    @click="deleteDatasetAction(dataset)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </el-col>
          </el-row>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            :data="datasets"
            style="width: 100%"
            v-loading="loading"
            @sort-change="handleTableSort"
          >
            <el-table-column prop="name" label="数据集名称" sortable="custom">
              <template #default="{ row }">
                <div class="dataset-name-cell">
                  <div class="dataset-type-icon">
                    <el-icon>
                      <component :is="getTypeIcon(row.dataset_type)" />
                    </el-icon>
                  </div>
                  <div class="dataset-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="description">{{ row.description }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="dataset_type" label="类型" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ getTypeText(row.dataset_type) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="getStatusType(row.status)"
                  size="small"
                  :class="{ 'status-processing': row.status === 'processing' }"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="record_count" label="样本数" width="120" sortable="custom">
              <template #default="{ row }">
                {{ formatNumber(row.record_count) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="size" label="大小" width="120" sortable="custom">
              <template #default="{ row }">
                {{ formatSize(row.size) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="180" sortable="custom">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="140" fixed="right">
              <template #default="{ row }">
                <el-button
                  size="small"
                  @click="previewDataset(row)"
                >
                  预览数据
                </el-button>
                <el-dropdown trigger="click">
                  <el-button size="small" text>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="editDataset(row)">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item @click="downloadDataset(row)">
                        <el-icon><Download /></el-icon>
                        下载
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="deleteDatasetAction(row)"
                      >
                        <el-icon><Delete /></el-icon>
                        删除
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
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
    
    <!-- 上传数据集对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传数据集"
      width="600px"
      :before-close="handleCloseUpload"
    >
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-width="100px"
      >
        <el-form-item label="数据集名称" prop="name">
          <el-input
            v-model="uploadForm.name"
            placeholder="请输入数据集名称"
          />
        </el-form-item>
        
        <el-form-item label="数据类型" prop="type">
          <el-select
            v-model="uploadForm.type"
            placeholder="请选择数据类型"
            style="width: 100%"
          >
            <el-option label="文本" value="text" />
            <el-option label="图像" value="image" />
            <el-option label="音频" value="audio" />
            <el-option label="视频" value="video" />
            <el-option label="表格" value="tabular" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="uploadForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入数据集描述"
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
        
        <el-form-item label="数据文件" prop="files">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :show-file-list="true"
            :limit="10"
            multiple
            accept=".csv,.json,.txt,.zip,.tar.gz,.jpg,.png,.mp3,.wav,.mp4"
            @change="handleFileChange"
          >
            <el-button>
              <el-icon><Upload /></el-icon>
              选择文件
            </el-button>
            <template #tip>
              <div class="el-upload__tip">
                支持 CSV, JSON, TXT, ZIP, 图像, 音频, 视频等格式，单个文件不超过 1GB
              </div>
            </template>
          </el-upload>
        </el-form-item>
        
        <el-form-item label="数据处理">
          <el-checkbox-group v-model="uploadForm.processing">
            <el-checkbox label="auto_clean">自动清洗</el-checkbox>
            <el-checkbox label="auto_split">自动分割</el-checkbox>
            <el-checkbox label="auto_validate">自动验证</el-checkbox>
          </el-checkbox-group>
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

    <!-- 数据集编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑数据集"
      width="600px"
      :before-close="handleCloseEdit"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        label-width="100px"
      >
        <el-form-item label="数据集名称" prop="name">
          <el-input
            v-model="editForm.name"
            placeholder="请输入数据集名称"
          />
        </el-form-item>

        <el-form-item label="数据类型" prop="type">
          <el-select
            v-model="editForm.type"
            placeholder="请选择数据类型"
            style="width: 100%"
          >
            <el-option label="文本" value="text" />
            <el-option label="图像" value="image" />
            <el-option label="音频" value="audio" />
            <el-option label="视频" value="video" />
            <el-option label="表格" value="tabular" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入数据集描述"
          />
        </el-form-item>

        <el-form-item label="标签">
          <el-select
            v-model="editForm.tags"
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
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button
            type="primary"
            @click="submitEdit"
            :loading="editLoading"
          >
            保存
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 数据集预览抽屉 -->
    <el-drawer
      v-model="previewDialogVisible"
      :title="`预览数据集: ${currentPreviewDataset?.name || ''}`"
      direction="rtl"
      size="60%"
    >
      <div v-loading="previewLoading" class="preview-drawer-content">
        <template v-if="previewData && previewData.samples && previewData.samples.length">
          <div v-if="currentPreviewDataset?.dataset_type === 'image'" class="image-preview-grid">
            <el-image
              v-for="(img, index) in previewData.samples"
              :key="index"
              :src="img"
              fit="cover"
              class="preview-img-item"
              :preview-src-list="previewData.samples"
              :initial-index="index"
            />
          </div>
          <div v-else-if="currentPreviewDataset?.dataset_type === 'tabular'" class="tabular-preview">
            <el-table :data="previewData.samples" border style="width: 100%" height="400">
              <el-table-column
                v-for="field in previewData.sample_fields"
                :key="field"
                :prop="field"
                :label="field"
              />
            </el-table>
          </div>
          <div v-else class="text-preview-list">
            <el-card
              v-for="(sample, index) in previewData.samples"
              :key="index"
              class="preview-text-card"
              shadow="hover"
            >
              <pre>{{ typeof sample === 'object' ? JSON.stringify(sample, null, 2) : sample }}</pre>
            </el-card>
          </div>

          <div class="preview-footer-info">
            <el-text type="info" size="small">
              显示前 {{ previewData.samples.length }} 条样本，共计 {{ previewData.total_count }} 条记录
            </el-text>
          </div>
        </template>
        <el-empty v-else description="暂无预览数据" />
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import {
  getDatasets,
  getDatasetStats,
  createDataset,
  updateDataset,
  uploadDatasetFiles,
  deleteDataset,
  getDatasetPreview,
  downloadDatasetFile,
  type Dataset,
  type DatasetListParams
} from '@/api/datasets'
import {
  FolderOpened,
  Upload,
  Refresh,
  Document,
  Files,
  Loading,
  Search,
  RefreshLeft,
  Grid,
  List,
  Calendar,
  View,
  MoreFilled,
  Edit,
  CopyDocument,
  Download,
  Delete,
  Picture,
  Headset,
  VideoCamera,
  Tickets
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const viewMode = ref('grid')
const uploadDialogVisible = ref(false)
const uploadFormRef = ref<FormInstance>()
const uploading = ref(false)
const loading = ref(false)

// 统计数据
const stats = reactive({
  total: 0,
  totalSamples: 0,
  totalSize: 0,
  processing: 0
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

// 数据集列表
const datasets = ref<Dataset[]>([])

// 上传表单
const uploadForm = reactive({
  name: '',
  type: '',
  description: '',
  tags: [] as string[],
  files: [] as File[],
  processing: [] as string[]
})

// 常用标签
const commonTags = [
  '训练集', '测试集', '验证集', '标注数据', '原始数据',
  '图像分类', '目标检测', '语义分割', '自然语言处理', '语音识别'
]

// 预览相关数据
const previewDialogVisible = ref(false)
const previewLoading = ref(false)
const currentPreviewDataset = ref<Dataset | null>(null)
const previewData = ref<any>(null)

// 编辑相关数据
const editDialogVisible = ref(false)
const editFormRef = ref<FormInstance>()
const editLoading = ref(false)
const currentEditDataset = ref<Dataset | null>(null)
const editForm = reactive({
  name: '',
  type: '',
  description: '',
  tags: [] as string[]
})

// 表单验证规则
const uploadRules: FormRules = {
  name: [
    { required: true, message: '请输入数据集名称', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择数据类型', trigger: 'change' }
  ],
  description: [
    { required: true, message: '请输入数据集描述', trigger: 'blur' }
  ],
  files: [
    { required: true, message: '请选择数据文件', trigger: 'change' }
  ]
}

// 方法
const formatNumber = (num: number | null | undefined) => {
  if (!num) return '0'
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatSize = (bytes: number | null | undefined) => {
  if (!bytes) return '0 B'
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
    processing: 'warning',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    ready: '就绪',
    processing: '处理中',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const getTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    text: '文本',
    image: '图像',
    audio: '音频',
    video: '视频',
    tabular: '表格'
  }
  return typeMap[type] || type
}

const getTypeIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    text: Document,
    image: Picture,
    audio: Headset,
    video: VideoCamera,
    tabular: Tickets
  }
  return iconMap[type] || Document
}

// 自动刷新定时器
let refreshTimer: ReturnType<typeof setInterval> | null = null

const startAutoRefresh = () => {
  if (refreshTimer) return
  // 每10秒刷新一次
  refreshTimer = setInterval(() => {
    // 只有当有状态为 processing 的数据集时才刷新列表
    const hasProcessing = datasets.value.some(d => d.status === 'processing')
    if (hasProcessing) {
      fetchDatasets()
      fetchStats()
    } else {
      stopAutoRefresh()
    }
  }, 10000)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const fetchDatasets = async () => {
  loading.value = true
  try {
    const params: DatasetListParams = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      sort_by: filters.sortBy,
      sort_order: 'desc'
    }
    
    if (filters.search) params.search = filters.search
    if (filters.type) params.dataset_type = filters.type
    if (filters.status) params.status = filters.status

    const response = await getDatasets(params)
    // 兼容不同的返回格式，有的接口直接返回数据，有的可能包在 data 字段中
    const responseData = (response as any).data || response
    datasets.value = responseData.items || []
    pagination.total = responseData.total || 0
    
    // 如果列表里有处理中的数据集，启动自动刷新
    if (datasets.value.some(d => d.status === 'processing')) {
      startAutoRefresh()
    }
  } catch (error) {
    console.error('获取数据集列表失败:', error)
    ElMessage.error('获取数据集列表失败')
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const response = await getDatasetStats()
    const responseData = (response as any).data || response
    stats.total = responseData.total || 0
    stats.totalSamples = responseData.total_samples || 0
    stats.totalSize = responseData.total_size || 0
    stats.processing = responseData.processing || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const handleSearch = () => {
  pagination.currentPage = 1
  fetchDatasets()
}

const handleFilter = () => {
  pagination.currentPage = 1
  fetchDatasets()
}

const handleSort = () => {
  pagination.currentPage = 1
  fetchDatasets()
}

const resetFilters = () => {
  filters.search = ''
  filters.type = ''
  filters.status = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
  fetchDatasets()
}

const handleTableSort = ({ prop, order }: any) => {
  if (order) {
    filters.sortBy = prop
    fetchDatasets()
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  fetchDatasets()
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  fetchDatasets()
}

const refreshDatasets = async () => {
  await Promise.all([fetchDatasets(), fetchStats()])
  ElMessage.success('数据集列表已刷新')
}

const showUploadDialog = () => {
  uploadDialogVisible.value = true
}

const handleCloseUpload = () => {
  if (uploadFormRef.value) {
    uploadFormRef.value.resetFields()
  }
  uploadForm.tags = []
  uploadForm.files = []
  uploadForm.processing = []
  uploadDialogVisible.value = false
}

const handleFileChange = (file: any, fileList: any[]) => {
  uploadForm.files = fileList.map(f => f.raw)
}

const submitUpload = async () => {
  if (!uploadFormRef.value) return
  
  try {
    await uploadFormRef.value.validate()
    uploading.value = true
    
    // 1. 创建数据集记录
    const createResponse = await createDataset({
      name: uploadForm.name,
      description: uploadForm.description,
      dataset_type: uploadForm.type,
      tags: uploadForm.tags
    })
    
    // 兼容返回数据直接包含或包在 data 中
    const datasetData = (createResponse as any).data || createResponse
    
    // 2. 如果有文件，上传文件
    if (uploadForm.files.length > 0 && datasetData && datasetData.id) {
      await uploadDatasetFiles(datasetData.id, uploadForm.files)
    }
    
    ElMessage.success('数据集创建成功')
    handleCloseUpload()
    refreshDatasets()
  } catch (error: any) {
    console.error('上传数据集失败:', error)
    ElMessage.error(error.response?.data?.detail || '上传失败，请稍后重试')
  } finally {
    uploading.value = false
  }
}

const previewDataset = async (dataset: Dataset) => {
  currentPreviewDataset.value = dataset
  previewDialogVisible.value = true
  previewLoading.value = true
  previewData.value = null
  
  try {
    const response = await getDatasetPreview(dataset.id, 10)
    previewData.value = (response as any).data || response
  } catch (error) {
    console.error('获取预览数据失败:', error)
    ElMessage.error('无法获取该数据集的预览数据')
  } finally {
    previewLoading.value = false
  }
}

const editDataset = (dataset: Dataset) => {
  currentEditDataset.value = dataset
  editForm.name = dataset.name
  editForm.type = dataset.dataset_type || ''
  editForm.description = dataset.description || ''
  editForm.tags = dataset.tags || []
  editDialogVisible.value = true
}

const handleCloseEdit = () => {
  if (editFormRef.value) {
    editFormRef.value.resetFields()
  }
  editForm.tags = []
  currentEditDataset.value = null
  editDialogVisible.value = false
}

const submitEdit = async () => {
  if (!editFormRef.value || !currentEditDataset.value) return

  try {
    await editFormRef.value.validate()
    editLoading.value = true

    await updateDataset(currentEditDataset.value.id, {
      name: editForm.name,
      dataset_type: editForm.type,
      description: editForm.description,
      tags: editForm.tags
    })

    ElMessage.success('数据集更新成功')
    handleCloseEdit()
    refreshDatasets()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('更新数据集失败:', error)
      ElMessage.error(error.response?.data?.detail || '更新失败，请稍后重试')
    }
  } finally {
    editLoading.value = false
  }
}

const downloadDataset = async (dataset: Dataset) => {
  if (!dataset.storage_path) {
    ElMessage.warning('该数据集尚未上传任何文件，无法下载')
    return
  }

  try {
    ElMessage.info('正在下载数据集...')
    await downloadDatasetFile(dataset.id, `${dataset.name}.zip`)
    ElMessage.success('数据集下载完成')
  } catch (error: any) {
    console.error('下载数据集失败:', error)
    ElMessage.error(error.response?.data?.detail || '下载失败，请稍后重试')
  }
}

const deleteDatasetAction = async (dataset: Dataset) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除数据集 "${dataset.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteDataset(dataset.id)
    
    ElMessage.success('数据集删除成功')
    refreshDatasets()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除数据集失败:', error)
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

onMounted(() => {
  fetchDatasets()
  fetchStats()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.datasets-page {
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
        
        &.samples {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        &.storage {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.processing {
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
  
  .datasets-list {
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
      .dataset-card {
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
        
        .dataset-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          
          .dataset-type {
            .type-icon {
              width: 32px;
              height: 32px;
              border-radius: 6px;
              background: var(--el-color-primary-light-9);
              color: var(--el-color-primary);
              display: flex;
              align-items: center;
              justify-content: center;
              font-size: 16px;
            }
          }
          
          .dataset-status {
            .status-processing {
              animation: pulse 1.5s infinite;
            }
          }
        }
        
        .dataset-content {
          flex: 1;
          
          .dataset-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 8px 0;
            line-height: 1.4;
          }
          
          .dataset-description {
            font-size: 14px;
            color: var(--el-text-color-regular);
            line-height: 1.5;
            margin: 0 0 12px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          
          .dataset-meta {
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
          
          .dataset-tags {
            margin-bottom: 16px;
            
            .tag-item {
              margin-right: 6px;
              margin-bottom: 6px;
            }
          }
          
          .dataset-preview {
            margin-bottom: 16px;
            
            .preview-label {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 8px;
            }
            
            .preview-content {
              .image-preview {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 4px;
                
                .preview-image {
                  width: 100%;
                  height: 40px;
                  object-fit: cover;
                  border-radius: 4px;
                  background: var(--el-fill-color-light);
                }
              }
              
              .text-preview {
                .preview-text {
                  font-size: 12px;
                  color: var(--el-text-color-secondary);
                  background: var(--el-fill-color-light);
                  padding: 6px 8px;
                  border-radius: 4px;
                  margin-bottom: 4px;
                  display: -webkit-box;
                  -webkit-line-clamp: 1;
                  -webkit-box-orient: vertical;
                  overflow: hidden;
                  
                  &:last-child {
                    margin-bottom: 0;
                  }
                }
              }
              
              .generic-preview {
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 12px;
                color: var(--el-text-color-secondary);
                background: var(--el-fill-color-light);
                padding: 8px;
                border-radius: 4px;
                
                .el-icon {
                  font-size: 16px;
                }
              }
            }
          }
        }
        
        .dataset-actions {
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
      .dataset-name-cell {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .dataset-type-icon {
          width: 32px;
          height: 32px;
          border-radius: 6px;
          background: var(--el-color-primary-light-9);
          color: var(--el-color-primary);
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          
          .el-icon {
            font-size: 16px;
          }
        }
        
        .dataset-info {
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
  }
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .datasets-page {
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
    
    .datasets-list {
      .grid-view {
        .dataset-card {
          .dataset-actions {
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
  .datasets-page {
    .stats-cards {
      .stat-card {
        background: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
      }
    }
    
    .datasets-list {
      .grid-view {
        .dataset-card {
          background: var(--el-bg-color-page);
          border-color: var(--el-border-color);
        }
      }
    }
  }
}

.preview-drawer-content {
  overflow-x: auto;

  .text-preview-list {
    .preview-text-card {
      overflow-x: auto;

      pre {
        margin: 0;
        white-space: pre-wrap;
        word-break: break-all;
      }
    }
  }

  .tabular-preview {
    overflow-x: auto;
    min-width: 100%;

    :deep(.el-table) {
      min-width: 500px;
    }
  }
}
</style>