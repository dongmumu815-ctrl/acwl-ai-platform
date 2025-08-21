<template>
  <div class="training-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><TrendCharts /></el-icon>
            训练管理
          </h1>
          <p class="page-description">管理和监控您的模型训练任务</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="createTraining">
            <el-icon><Plus /></el-icon>
            创建训练
          </el-button>
          <el-button @click="refreshTrainings">
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
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总训练任务</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon running">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.running }}</div>
              <div class="stat-label">运行中</div>
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
            <div class="stat-icon gpu">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.gpuUsage }}%</div>
              <div class="stat-label">GPU使用率</div>
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
              placeholder="搜索训练任务名称"
              clearable
              style="width: 250px"
              @input="handleSearch"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
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
              <el-option label="等待中" value="pending" />
              <el-option label="运行中" value="running" />
              <el-option label="已完成" value="completed" />
              <el-option label="已失败" value="failed" />
              <el-option label="已停止" value="stopped" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="模型类型">
            <el-select
              v-model="filters.modelType"
              placeholder="选择模型类型"
              clearable
              style="width: 150px"
              @change="handleFilter"
            >
              <el-option label="全部" value="" />
              <el-option label="图像分类" value="image_classification" />
              <el-option label="目标检测" value="object_detection" />
              <el-option label="文本分类" value="text_classification" />
              <el-option label="语言模型" value="language_model" />
              <el-option label="语音识别" value="speech_recognition" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="filters.sortBy"
              style="width: 150px"
              @change="handleSort"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="开始时间" value="started_at" />
              <el-option label="完成时间" value="completed_at" />
              <el-option label="训练进度" value="progress" />
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
    
    <!-- 训练任务列表 -->
    <div class="training-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>训练任务列表</span>
            <div class="header-actions">
              <el-radio-group v-model="viewMode" size="small">
                <el-radio-button label="grid">
                  <el-icon><Grid /></el-icon>
                </el-radio-button>
                <el-radio-button label="list">
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
              v-for="training in paginatedTrainings"
              :key="training.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="training-card">
                <div class="training-header">
                  <div class="training-type">
                    <el-icon class="type-icon">
                      <component :is="getTypeIcon(training.model_type)" />
                    </el-icon>
                  </div>
                  <div class="training-status">
                    <el-tag
                      :type="getStatusType(training.status)"
                      size="small"
                      :class="{ 'status-running': training.status === 'running' }"
                    >
                      {{ getStatusText(training.status) }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="training-content">
                  <h3 class="training-name">{{ training.name }}</h3>
                  <p class="training-description">{{ training.description }}</p>
                  
                  <div class="training-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(training.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Timer /></el-icon>
                      <span>{{ formatDuration(training.duration) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Monitor /></el-icon>
                      <span>{{ training.gpu_count }} GPU</span>
                    </div>
                  </div>
                  
                  <!-- 训练进度 -->
                  <div class="training-progress">
                    <div class="progress-header">
                      <span class="progress-label">训练进度</span>
                      <span class="progress-value">{{ training.progress }}%</span>
                    </div>
                    <el-progress
                      :percentage="training.progress"
                      :status="getProgressStatus(training.status)"
                      :stroke-width="6"
                    />
                  </div>
                  
                  <!-- 训练指标 -->
                  <div class="training-metrics" v-if="training.metrics">
                    <div class="metrics-header">训练指标</div>
                    <div class="metrics-grid">
                      <div class="metric-item">
                        <div class="metric-label">损失</div>
                        <div class="metric-value">{{ training.metrics.loss?.toFixed(4) || 'N/A' }}</div>
                      </div>
                      <div class="metric-item">
                        <div class="metric-label">准确率</div>
                        <div class="metric-value">{{ training.metrics.accuracy ? (training.metrics.accuracy * 100).toFixed(2) + '%' : 'N/A' }}</div>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 数据集信息 -->
                  <div class="dataset-info">
                    <div class="info-label">数据集:</div>
                    <div class="info-value">{{ training.dataset_name }}</div>
                  </div>
                </div>
                
                <div class="training-actions">
                  <el-button
                    size="small"
                    @click="viewTraining(training)"
                  >
                    查看
                  </el-button>
                  <el-button
                    v-if="training.status === 'running'"
                    type="warning"
                    size="small"
                    @click="stopTraining(training)"
                  >
                    停止
                  </el-button>
                  <el-button
                    v-else-if="training.status === 'completed'"
                    type="primary"
                    size="small"
                    @click="deployModel(training)"
                  >
                    部署
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="viewLogs(training)">
                          <el-icon><Document /></el-icon>
                          查看日志
                        </el-dropdown-item>
                        <el-dropdown-item @click="viewMetrics(training)">
                          <el-icon><TrendCharts /></el-icon>
                          训练指标
                        </el-dropdown-item>
                        <el-dropdown-item @click="cloneTraining(training)">
                          <el-icon><CopyDocument /></el-icon>
                          克隆训练
                        </el-dropdown-item>
                        <el-dropdown-item
                          v-if="training.status === 'completed'"
                          @click="downloadModel(training)"
                        >
                          <el-icon><Download /></el-icon>
                          下载模型
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="deleteTraining(training)"
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
            :data="paginatedTrainings"
            style="width: 100%"
            @sort-change="handleTableSort"
          >
            <el-table-column prop="name" label="训练任务" sortable>
              <template #default="{ row }">
                <div class="training-name-cell">
                  <div class="training-type-icon">
                    <el-icon>
                      <component :is="getTypeIcon(row.model_type)" />
                    </el-icon>
                  </div>
                  <div class="training-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="description">{{ row.description }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="model_type" label="模型类型" width="120">
              <template #default="{ row }">
                <el-tag size="small">{{ getModelTypeText(row.model_type) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag
                  :type="getStatusType(row.status)"
                  size="small"
                  :class="{ 'status-running': row.status === 'running' }"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="progress" label="进度" width="120">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.progress"
                  :status="getProgressStatus(row.status)"
                  :stroke-width="6"
                  :show-text="false"
                />
                <span class="progress-text">{{ row.progress }}%</span>
              </template>
            </el-table-column>
            
            <el-table-column prop="dataset_name" label="数据集" width="150">
              <template #default="{ row }">
                {{ row.dataset_name }}
              </template>
            </el-table-column>
            
            <el-table-column prop="gpu_count" label="GPU" width="80">
              <template #default="{ row }">
                {{ row.gpu_count }}
              </template>
            </el-table-column>
            
            <el-table-column prop="duration" label="耗时" width="120">
              <template #default="{ row }">
                {{ formatDuration(row.duration) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewTraining(row)">
                  查看
                </el-button>
                <el-button
                  v-if="row.status === 'running'"
                  type="warning"
                  size="small"
                  @click="stopTraining(row)"
                >
                  停止
                </el-button>
                <el-button
                  v-else-if="row.status === 'completed'"
                  type="primary"
                  size="small"
                  @click="deployModel(row)"
                >
                  部署
                </el-button>
                <el-dropdown trigger="click">
                  <el-button size="small" text>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="viewLogs(row)">
                        <el-icon><Document /></el-icon>
                        查看日志
                      </el-dropdown-item>
                      <el-dropdown-item @click="viewMetrics(row)">
                        <el-icon><TrendCharts /></el-icon>
                        训练指标
                      </el-dropdown-item>
                      <el-dropdown-item @click="cloneTraining(row)">
                        <el-icon><CopyDocument /></el-icon>
                        克隆训练
                      </el-dropdown-item>
                      <el-dropdown-item
                        v-if="row.status === 'completed'"
                        @click="downloadModel(row)"
                      >
                        <el-icon><Download /></el-icon>
                        下载模型
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="deleteTraining(row)"
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
            :total="filteredTrainings.length"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
          />
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  TrendCharts,
  Plus,
  Refresh,
  Loading,
  CircleCheck,
  Monitor,
  Search,
  RefreshLeft,
  Grid,
  List,
  Calendar,
  Timer,
  MoreFilled,
  Document,
  CopyDocument,
  Download,
  Delete,
  Picture,
  Headset,
  VideoCamera,
  ChatDotRound,
  Cpu
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const viewMode = ref('grid')
let refreshTimer: NodeJS.Timeout | null = null

// 统计数据
const stats = reactive({
  total: 0,
  running: 0,
  completed: 0,
  gpuUsage: 0
})

// 筛选条件
const filters = reactive({
  search: '',
  status: '',
  modelType: '',
  sortBy: 'created_at'
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 20
})

// 训练任务列表
const trainings = ref<any[]>([])

// 计算属性
const filteredTrainings = computed(() => {
  let result = [...trainings.value]
  
  // 搜索过滤
  if (filters.search) {
    const search = filters.search.toLowerCase()
    result = result.filter(training => 
      training.name.toLowerCase().includes(search) ||
      training.description.toLowerCase().includes(search)
    )
  }
  
  // 状态过滤
  if (filters.status) {
    result = result.filter(training => training.status === filters.status)
  }
  
  // 模型类型过滤
  if (filters.modelType) {
    result = result.filter(training => training.model_type === filters.modelType)
  }
  
  // 排序
  result.sort((a, b) => {
    const field = filters.sortBy
    if (field === 'created_at' || field === 'started_at' || field === 'completed_at') {
      return new Date(b[field] || 0).getTime() - new Date(a[field] || 0).getTime()
    }
    return b[field] - a[field]
  })
  
  return result
})

const paginatedTrainings = computed(() => {
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  return filteredTrainings.value.slice(start, end)
})

// 方法
const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const formatDuration = (seconds: number) => {
  if (!seconds) return 'N/A'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger',
    stopped: 'info'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    completed: '已完成',
    failed: '已失败',
    stopped: '已停止'
  }
  return statusMap[status] || '未知'
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return undefined
}

const getModelTypeText = (type: string) => {
  const typeMap: Record<string, string> = {
    image_classification: '图像分类',
    object_detection: '目标检测',
    text_classification: '文本分类',
    language_model: '语言模型',
    speech_recognition: '语音识别'
  }
  return typeMap[type] || type
}

const getTypeIcon = (type: string) => {
  const iconMap: Record<string, any> = {
    image_classification: Picture,
    object_detection: Picture,
    text_classification: ChatDotRound,
    language_model: ChatDotRound,
    speech_recognition: Headset
  }
  return iconMap[type] || Cpu
}

const handleSearch = () => {
  pagination.currentPage = 1
}

const handleFilter = () => {
  pagination.currentPage = 1
}

const handleSort = () => {
  pagination.currentPage = 1
}

const resetFilters = () => {
  filters.search = ''
  filters.status = ''
  filters.modelType = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
}

const handleTableSort = ({ prop, order }: any) => {
  if (order) {
    filters.sortBy = prop
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
}

const refreshTrainings = async () => {
  try {
    // 这里应该调用实际的API
    // const response = await trainingApi.getTrainings()
    // trainings.value = response.data
    
    // 模拟数据
    trainings.value = [
      {
        id: '1',
        name: 'ResNet50图像分类训练',
        description: '使用CIFAR-10数据集训练ResNet50模型进行图像分类',
        model_type: 'image_classification',
        status: 'running',
        progress: 65,
        dataset_name: 'CIFAR-10',
        gpu_count: 2,
        duration: 3600,
        metrics: {
          loss: 0.3245,
          accuracy: 0.8567
        },
        created_at: '2024-01-20T10:30:00Z',
        started_at: '2024-01-20T10:35:00Z'
      },
      {
        id: '2',
        name: 'BERT文本分类微调',
        description: '基于预训练BERT模型进行中文情感分析任务微调',
        model_type: 'text_classification',
        status: 'completed',
        progress: 100,
        dataset_name: '中文情感分析语料库',
        gpu_count: 1,
        duration: 7200,
        metrics: {
          loss: 0.1234,
          accuracy: 0.9234
        },
        created_at: '2024-01-18T14:20:00Z',
        started_at: '2024-01-18T14:25:00Z',
        completed_at: '2024-01-18T16:25:00Z'
      },
      {
        id: '3',
        name: 'YOLO目标检测训练',
        description: '训练YOLOv8模型进行自定义目标检测',
        model_type: 'object_detection',
        status: 'failed',
        progress: 23,
        dataset_name: '自定义检测数据集',
        gpu_count: 4,
        duration: 1800,
        metrics: {
          loss: 2.5678,
          accuracy: 0.2345
        },
        created_at: '2024-01-19T09:15:00Z',
        started_at: '2024-01-19T09:20:00Z'
      },
      {
        id: '4',
        name: 'Whisper语音识别训练',
        description: '基于Whisper模型进行中文语音识别训练',
        model_type: 'speech_recognition',
        status: 'pending',
        progress: 0,
        dataset_name: '语音识别数据集',
        gpu_count: 2,
        duration: 0,
        metrics: null,
        created_at: '2024-01-21T08:45:00Z'
      },
      {
        id: '5',
        name: 'GPT-2语言模型训练',
        description: '训练小型GPT-2模型用于文本生成',
        model_type: 'language_model',
        status: 'running',
        progress: 12,
        dataset_name: '中文文本语料',
        gpu_count: 8,
        duration: 14400,
        metrics: {
          loss: 3.2456,
          perplexity: 25.67
        },
        created_at: '2024-01-17T16:30:00Z',
        started_at: '2024-01-17T16:35:00Z'
      }
    ]
    
    // 更新统计数据
    updateStats()
    
    ElMessage.success('训练任务列表已刷新')
  } catch (error) {
    console.error('刷新训练任务列表失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  }
}

const updateStats = () => {
  stats.total = trainings.value.length
  stats.running = trainings.value.filter(t => t.status === 'running').length
  stats.completed = trainings.value.filter(t => t.status === 'completed').length
  stats.gpuUsage = Math.floor(Math.random() * 100) // 模拟GPU使用率
}

const createTraining = () => {
  router.push('/training/create')
}

const viewTraining = (training: any) => {
  router.push(`/training/${training.id}`)
}

const stopTraining = async (training: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要停止训练任务 "${training.name}" 吗？`,
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    // await trainingApi.stopTraining(training.id)
    
    training.status = 'stopped'
    updateStats()
    
    ElMessage.success('训练任务已停止')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('停止训练任务失败:', error)
      ElMessage.error('停止失败，请稍后重试')
    }
  }
}

const deployModel = (training: any) => {
  router.push(`/deployments/create?trainingId=${training.id}`)
}

const viewLogs = (training: any) => {
  router.push(`/training/${training.id}/logs`)
}

const viewMetrics = (training: any) => {
  router.push(`/training/${training.id}/metrics`)
}

const cloneTraining = async (training: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要克隆训练任务 "${training.name}" 吗？`,
      '确认克隆',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    // 这里应该调用实际的API
    // await trainingApi.cloneTraining(training.id)
    
    ElMessage.success('训练任务克隆成功')
    refreshTrainings()
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('克隆训练任务失败:', error)
      ElMessage.error('克隆失败，请稍后重试')
    }
  }
}

const downloadModel = async (training: any) => {
  try {
    // 这里应该调用实际的API获取下载链接
    // const response = await trainingApi.getModelDownloadUrl(training.id)
    // window.open(response.data.url)
    
    ElMessage.info('正在准备模型下载链接...')
  } catch (error) {
    console.error('获取模型下载链接失败:', error)
    ElMessage.error('下载失败，请稍后重试')
  }
}

const deleteTraining = async (training: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除训练任务 "${training.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    // await trainingApi.deleteTraining(training.id)
    
    const index = trainings.value.findIndex(t => t.id === training.id)
    if (index > -1) {
      trainings.value.splice(index, 1)
      updateStats()
    }
    
    ElMessage.success('训练任务删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除训练任务失败:', error)
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

// 自动刷新运行中的训练任务
const startAutoRefresh = () => {
  refreshTimer = setInterval(() => {
    const runningTrainings = trainings.value.filter(t => t.status === 'running')
    if (runningTrainings.length > 0) {
      // 这里应该只更新运行中的训练任务状态
      // updateRunningTrainings(runningTrainings.map(t => t.id))
      
      // 模拟进度更新
      runningTrainings.forEach(training => {
        if (training.progress < 100) {
          training.progress = Math.min(100, training.progress + Math.floor(Math.random() * 5))
          training.duration += 30
          
          if (training.metrics) {
            training.metrics.loss = Math.max(0.01, training.metrics.loss - Math.random() * 0.01)
            if (training.metrics.accuracy) {
              training.metrics.accuracy = Math.min(1, training.metrics.accuracy + Math.random() * 0.001)
            }
          }
          
          if (training.progress >= 100) {
            training.status = 'completed'
            training.completed_at = new Date().toISOString()
            updateStats()
          }
        }
      })
    }
  }, 30000) // 每30秒更新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

onMounted(() => {
  refreshTrainings()
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<style lang="scss" scoped>
.training-page {
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
        
        &.running {
          background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
          
          .el-icon {
            animation: spin 2s linear infinite;
          }
        }
        
        &.completed {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.gpu {
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
  
  .training-list {
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
      .training-card {
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
        
        .training-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 12px;
          
          .training-type {
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
          
          .training-status {
            .status-running {
              animation: pulse 1.5s infinite;
            }
          }
        }
        
        .training-content {
          flex: 1;
          
          .training-name {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin: 0 0 8px 0;
            line-height: 1.4;
          }
          
          .training-description {
            font-size: 14px;
            color: var(--el-text-color-regular);
            line-height: 1.5;
            margin: 0 0 12px 0;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
          }
          
          .training-meta {
            margin-bottom: 16px;
            
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
          
          .training-progress {
            margin-bottom: 16px;
            
            .progress-header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 8px;
              
              .progress-label {
                font-size: 12px;
                color: var(--el-text-color-secondary);
              }
              
              .progress-value {
                font-size: 12px;
                font-weight: 600;
                color: var(--el-text-color-primary);
              }
            }
          }
          
          .training-metrics {
            margin-bottom: 16px;
            
            .metrics-header {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 8px;
            }
            
            .metrics-grid {
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 8px;
              
              .metric-item {
                background: var(--el-fill-color-light);
                padding: 8px;
                border-radius: 4px;
                text-align: center;
                
                .metric-label {
                  font-size: 10px;
                  color: var(--el-text-color-secondary);
                  margin-bottom: 2px;
                }
                
                .metric-value {
                  font-size: 12px;
                  font-weight: 600;
                  color: var(--el-text-color-primary);
                }
              }
            }
          }
          
          .dataset-info {
            margin-bottom: 16px;
            
            .info-label {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 4px;
            }
            
            .info-value {
              font-size: 14px;
              color: var(--el-text-color-primary);
              font-weight: 500;
            }
          }
        }
        
        .training-actions {
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
      .training-name-cell {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .training-type-icon {
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
        
        .training-info {
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
      
      .progress-text {
        margin-left: 8px;
        font-size: 12px;
        color: var(--el-text-color-secondary);
      }
    }
    
    .pagination-wrapper {
      display: flex;
      justify-content: center;
      margin-top: 20px;
    }
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
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
  .training-page {
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
    
    .training-list {
      .grid-view {
        .training-card {
          .training-actions {
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
  .training-page {
    .stats-cards {
      .stat-card {
        background: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
      }
    }
    
    .training-list {
      .grid-view {
        .training-card {
          background: var(--el-bg-color-page);
          border-color: var(--el-border-color);
        }
      }
    }
  }
}
</style>