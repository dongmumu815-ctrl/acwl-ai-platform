<template>
  <div class="deployments-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Monitor /></el-icon>
            部署管理
          </h1>
          <p class="page-description">管理和监控您的模型部署</p>
        </div>
        <div class="header-right">
          <el-button type="primary" @click="createDeployment">
            <el-icon><Plus /></el-icon>
            创建部署
          </el-button>
          <el-button @click="refreshDeployments">
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
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_count }}</div>
              <div class="stat-label">总部署数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon running">
              <el-icon><VideoPlay /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.running_count }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon stopped">
              <el-icon><VideoPause /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.stopped_count }}</div>
              <div class="stat-label">已停止</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon requests">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.totalRequests) }}</div>
              <div class="stat-label">总请求数</div>
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
              v-model="filters.keyword"
              placeholder="搜索部署名称"
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
              <el-option label="运行中" value="running" />
              <el-option label="已停止" value="stopped" />
              <el-option label="部署中" value="deploying" />
              <el-option label="失败" value="failed" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="环境">
            <el-select
              v-model="filters.env_id"
              placeholder="全部环境"
              clearable
              style="width: 180px"
              @change="handleFilter"
            >
              <el-option
                v-for="env in environments"
                :key="env.id"
                :label="env.name"
                :value="env.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="排序">
            <el-select
              v-model="filters.sortBy"
              style="width: 150px"
              @change="handleSort"
            >
              <el-option label="创建时间" value="created_at" />
              <el-option label="请求数" value="request_count" />
              <el-option label="CPU使用率" value="cpu_usage" />
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
    
    <!-- 部署列表 -->
    <div class="deployments-list">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>部署列表</span>
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
              v-for="deployment in paginatedDeployments"
              :key="deployment.id"
              :xs="24"
              :sm="12"
              :md="8"
              :lg="6"
            >
              <div class="deployment-card">
                <div class="deployment-header">
                  <div class="deployment-info">
                    <h3 class="deployment-name">{{ deployment.name }}</h3>
                    <p class="deployment-model">{{ deployment.model_name }}</p>
                  </div>
                  <div class="deployment-status">
                    <el-tag
                      :type="getStatusType(deployment.status)"
                      size="small"
                      :class="{ 'status-blinking': deployment.status === 'deploying' }"
                    >
                      {{ getStatusText(deployment.status) }}
                    </el-tag>
                  </div>
                </div>
                
                <div class="deployment-content">
                  <div class="deployment-meta">
                    <div class="meta-item">
                      <el-icon><Calendar /></el-icon>
                      <span>{{ formatDate(deployment.created_at) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Location /></el-icon>
                      <span>{{ getEnvironmentNameById(deployment.env_id) }}</span>
                    </div>
                    <div class="meta-item">
                      <el-icon><Connection /></el-icon>
                      <span>{{ deployment.request_count }} 请求</span>
                    </div>
                  </div>
                  
                  <!-- 资源使用情况 -->
                  <div class="resource-usage">
                    <div class="usage-item">
                      <div class="usage-label">
                        <el-icon><Cpu /></el-icon>
                        <span>CPU</span>
                      </div>
                      <div class="usage-bar">
                        <el-progress
                          :percentage="deployment.cpu_usage"
                          :stroke-width="6"
                          :show-text="false"
                          :color="getUsageColor(deployment.cpu_usage)"
                        />
                        <span class="usage-text">{{ deployment.cpu_usage }}%</span>
                      </div>
                    </div>
                    
                    <div class="usage-item">
                      <div class="usage-label">
                        <el-icon><Monitor /></el-icon>
                        <span>内存</span>
                      </div>
                      <div class="usage-bar">
                        <el-progress
                          :percentage="deployment.memory_usage"
                          :stroke-width="6"
                          :show-text="false"
                          :color="getUsageColor(deployment.memory_usage)"
                        />
                        <span class="usage-text">{{ deployment.memory_usage }}%</span>
                      </div>
                    </div>
                    
                    <div class="usage-item" v-if="deployment.gpu_usage !== undefined">
                      <div class="usage-label">
                        <el-icon><VideoCamera /></el-icon>
                        <span>GPU</span>
                      </div>
                      <div class="usage-bar">
                        <el-progress
                          :percentage="deployment.gpu_usage"
                          :stroke-width="6"
                          :show-text="false"
                          :color="getUsageColor(deployment.gpu_usage)"
                        />
                        <span class="usage-text">{{ deployment.gpu_usage }}%</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- API端点 -->
                  <div class="api-endpoint">
                    <div class="endpoint-label">API端点:</div>
                    <div class="endpoint-url">
                      <el-input
                        :model-value="deployment.endpoint"
                        readonly
                        size="small"
                      >
                        <template #append>
                          <el-button
                            size="small"
                            @click="copyEndpoint(deployment.endpoint)"
                          >
                            <el-icon><CopyDocument /></el-icon>
                          </el-button>
                        </template>
                      </el-input>
                    </div>
                  </div>
                </div>
                
                <div class="deployment-actions">
                  <el-button
                    size="small"
                    @click="viewDeployment(deployment)"
                  >
                    查看
                  </el-button>
                  <el-button
                    v-if="deployment.status === 'stopped'"
                    type="success"
                    size="small"
                    @click="startDeployment(deployment)"
                  >
                    启动
                  </el-button>
                  <el-button
                    v-else-if="deployment.status === 'running'"
                    type="warning"
                    size="small"
                    @click="stopDeployment(deployment)"
                  >
                    停止
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button size="small" text>
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="editDeployment(deployment)">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item @click="viewLogs(deployment)">
                          <el-icon><Document /></el-icon>
                          查看日志
                        </el-dropdown-item>
                        <el-dropdown-item @click="viewMetrics(deployment)">
                          <el-icon><TrendCharts /></el-icon>
                          监控指标
                        </el-dropdown-item>
                        <el-dropdown-item @click="scaleDeployment(deployment)">
                          <el-icon><ScaleToOriginal /></el-icon>
                          扩缩容
                        </el-dropdown-item>
                        <el-dropdown-item
                          divided
                          @click="deleteDeployment(deployment)"
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
            :data="paginatedDeployments"
            style="width: 100%"
            @sort-change="handleTableSort"
          >
            <el-table-column prop="name" label="部署名称" sortable>
              <template #default="{ row }">
                <div class="deployment-name-cell">
                  <div class="deployment-info">
                    <div class="name">{{ row.name }}</div>
                    <div class="model">{{ row.model_name }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="status" label="状态" width="120">
              <template #default="{ row }">
                <el-tag
                  :type="getStatusType(row.status)"
                  size="small"
                  :class="{ 'status-blinking': row.status === 'deploying' }"
                >
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="env_id" label="环境" width="100">
              <template #default="{ row }">
                <el-tag size="small">{{ getEnvironmentNameById(row.env_id) }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column label="资源使用" width="200">
              <template #default="{ row }">
                <div class="resource-usage-table">
                  <div class="usage-row">
                    <span class="usage-label">CPU:</span>
                    <el-progress
                      :percentage="row.cpu_usage"
                      :stroke-width="4"
                      :show-text="false"
                      :color="getUsageColor(row.cpu_usage)"
                    />
                    <span class="usage-value">{{ row.cpu_usage }}%</span>
                  </div>
                  <div class="usage-row">
                    <span class="usage-label">内存:</span>
                    <el-progress
                      :percentage="row.memory_usage"
                      :stroke-width="4"
                      :show-text="false"
                      :color="getUsageColor(row.memory_usage)"
                    />
                    <span class="usage-value">{{ row.memory_usage }}%</span>
                  </div>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="request_count" label="请求数" width="120" sortable>
              <template #default="{ row }">
                {{ formatNumber(row.request_count) }}
              </template>
            </el-table-column>
            
            <el-table-column prop="created_at" label="创建时间" width="180" sortable>
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click="viewDeployment(row)">
                  查看
                </el-button>
                <el-button
                  v-if="row.status === 'stopped'"
                  type="success"
                  size="small"
                  @click="startDeployment(row)"
                >
                  启动
                </el-button>
                <el-button
                  v-else-if="row.status === 'running'"
                  type="warning"
                  size="small"
                  @click="stopDeployment(row)"
                >
                  停止
                </el-button>
                <el-dropdown trigger="click">
                  <el-button size="small" text>
                    <el-icon><MoreFilled /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="editDeployment(row)">
                        <el-icon><Edit /></el-icon>
                        编辑
                      </el-dropdown-item>
                      <el-dropdown-item @click="viewLogs(row)">
                        <el-icon><Document /></el-icon>
                        查看日志
                      </el-dropdown-item>
                      <el-dropdown-item @click="viewMetrics(row)">
                        <el-icon><TrendCharts /></el-icon>
                        监控指标
                      </el-dropdown-item>
                      <el-dropdown-item @click="scaleDeployment(row)">
                        <el-icon><ScaleToOriginal /></el-icon>
                        扩缩容
                      </el-dropdown-item>
                      <el-dropdown-item
                        divided
                        @click="deleteDeployment(row)"
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
            :total="totalCount"
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
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  Plus,
  Refresh,
  RefreshLeft,
  Search,
  Grid,
  List,
  VideoPlay,
  VideoPause,
  Connection,
  Calendar,
  Location,
  Cpu,
  VideoCamera,
  CopyDocument,
  MoreFilled,
  Edit,
  Document,
  TrendCharts,
  ScaleToOriginal,
  Delete
} from '@element-plus/icons-vue'
import { deploymentApi, type DeploymentStats } from '@/api/deployments'
import { environmentApi } from '@/api/environments'

const router = useRouter()

// 响应式数据
const viewMode = ref('grid')

// 统计数据
const stats = reactive({
  total_count: 0,
  running_count: 0,
  stopped_count: 0,
  failed_count: 0,
  deploying_count: 0,
  total_requests: 0,
  type_stats: {} as Record<string, number>,
  status_distribution: {
    running: 0,
    stopped: 0,
    failed: 0,
    deploying: 0
  },
  totalRequests: 0 // 保留用于显示，从部署列表计算
})

// 筛选条件
const filters = reactive({
  keyword: '',
  status: '',
  env_id: '',
  sortBy: 'created_at'
})

// 分页
const pagination = reactive({
  currentPage: 1,
  pageSize: 20
})

// 响应式数据
const deployments = ref<any[]>([])
const totalCount = ref(0)
const environments = ref<any[]>([])

// 计算属性 - 现在直接使用API返回的数据，不需要本地过滤
const filteredDeployments = computed(() => {
  return deployments.value
})

const paginatedDeployments = computed(() => {
  // 由于API已经处理了分页，直接返回所有数据
  return deployments.value
})

// 方法
const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const getStatusType = (status: string) => {
  const statusMap: Record<string, string> = {
    running: 'success',
    stopped: 'info',
    deploying: 'warning',
    error: 'danger'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status: string) => {
  const statusMap: Record<string, string> = {
    running: '运行中',
    stopped: '已停止',
    deploying: '部署中',
    error: '错误'
  }
  return statusMap[status] || '未知'
}

const getEnvironmentText = (environment: string) => {
  const envMap: Record<string, string> = {
    development: '开发',
    testing: '测试',
    production: '生产'
  }
  return envMap[environment] || environment
}

const getEnvironmentNameById = (id: string | number) => {
  const env = environments.value.find((e: any) => e.id === id)
  return env ? env.name : String(id || '')
}

const getUsageColor = (usage: number) => {
  if (usage >= 80) return '#f56c6c'
  if (usage >= 60) return '#e6a23c'
  return '#67c23a'
}

const handleSearch = () => {
  pagination.currentPage = 1
  refreshDeployments()
}

const handleFilter = () => {
  pagination.currentPage = 1
  refreshDeployments()
}

const handleSort = () => {
  pagination.currentPage = 1
  refreshDeployments()
}

const resetFilters = () => {
  filters.keyword = ''
  filters.status = ''
  filters.env_id = ''
  filters.sortBy = 'created_at'
  pagination.currentPage = 1
  refreshDeployments()
}

const handleTableSort = ({ prop, order }: any) => {
  if (order) {
    filters.sortBy = prop
    refreshDeployments()
  }
}

const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  refreshDeployments()
}

const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  refreshDeployments()
}

const refreshDeployments = async () => {
  try {
    const queryParams = {
      page: pagination.currentPage,
      size: pagination.pageSize,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
      env_id: filters.env_id || undefined,
      sort_by: filters.sortBy || 'created_at',
      sort_order: 'desc'
    }
    
    const response = await deploymentApi.getDeployments(queryParams)
    
    deployments.value = (response.items || []).map((deployment: any) => ({
      id: deployment.id?.toString?.() ?? String(deployment.id),
      name: deployment.deployment_name || deployment.name,
      model_name: deployment.model?.name || deployment.model_name || 'Unknown Model',
      status: deployment.status,
      env_id: deployment.env_id,
      cpu_usage: deployment.latest_metrics?.cpu_utilization || 0,
      memory_usage: parseFloat(deployment.latest_metrics?.memory_used?.replace(/[^\d.]/g, '') || '0'),
      gpu_usage: deployment.latest_metrics?.gpu_utilization ? 
        Object.values(deployment.latest_metrics.gpu_utilization)[0] || 0 : 0,
      request_count: deployment.latest_metrics?.request_count || 0,
      endpoint: deployment.endpoint_url || '',
      created_at: deployment.created_at,
      updated_at: deployment.updated_at,
      _original: deployment
    }))
    
    totalCount.value = response.total || deployments.value.length
    
    updateStats()
    
    ElMessage.success('部署列表已刷新')
  } catch (error) {
    console.error('刷新部署列表失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    const statsData = await deploymentApi.getDeploymentStats()
    Object.assign(stats, statsData)
    
    // 使用API返回的总请求数
    stats.totalRequests = statsData.total_requests || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
    ElMessage.error('获取统计数据失败')
  }
}

const updateStats = () => {
  stats.total_count = deployments.value.length
  stats.running_count = deployments.value.filter(d => d.status === 'running').length
  stats.stopped_count = deployments.value.filter(d => d.status === 'stopped').length
  stats.failed_count = deployments.value.filter(d => d.status === 'failed').length
  stats.deploying_count = deployments.value.filter(d => d.status === 'deploying').length
  stats.totalRequests = deployments.value.reduce((sum, d) => sum + (d.request_count || 0), 0)
  
  // 更新状态分布
  stats.status_distribution = {
    running: stats.running_count,
    stopped: stats.stopped_count,
    failed: stats.failed_count,
    deploying: stats.deploying_count
  }
}

const createDeployment = async () => {
  try {
    const res = await environmentApi.getEnvironments({ page: 1, size: 100 })
    const items = (res as any).items || []
    sessionStorage.setItem('cachedEnvironments', JSON.stringify(items))
  } catch (e) {
    console.error('查询环境失败:', e)
    // 不中断跳转，保障创建流程
  } finally {
    router.push('/deployments/create')
  }
}

const viewDeployment = (deployment: any) => {
  router.push(`/deployments/${deployment.id}`)
}

const editDeployment = (deployment: any) => {
  router.push(`/deployments/${deployment.id}/edit`)
}

const startDeployment = async (deployment: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要启动部署 "${deployment.name}" 吗？`,
      '确认启动',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )
    
    // 这里应该调用实际的API
    // await deploymentApi.startDeployment(deployment.id)
    
    deployment.status = 'deploying'
    ElMessage.success('部署启动中...')
    
    // 模拟状态变化
    setTimeout(() => {
      deployment.status = 'running'
      ElMessage.success('部署启动成功')
    }, 3000)
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('启动部署失败:', error)
      ElMessage.error('启动失败，请稍后重试')
    }
  }
}

const stopDeployment = async (deployment: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要停止部署 "${deployment.name}" 吗？`,
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    // await deploymentApi.stopDeployment(deployment.id)
    
    deployment.status = 'stopped'
    deployment.cpu_usage = 0
    deployment.memory_usage = 0
    if (deployment.gpu_usage !== undefined) {
      deployment.gpu_usage = 0
    }
    
    ElMessage.success('部署已停止')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('停止部署失败:', error)
      ElMessage.error('停止失败，请稍后重试')
    }
  }
}

const deleteDeployment = async (deployment: any) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除部署 "${deployment.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里应该调用实际的API
    // await deploymentApi.deleteDeployment(deployment.id)
    
    const index = deployments.value.findIndex(d => d.id === deployment.id)
    if (index > -1) {
      deployments.value.splice(index, 1)
      updateStats()
    }
    
    ElMessage.success('部署删除成功')
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除部署失败:', error)
      ElMessage.error('删除失败，请稍后重试')
    }
  }
}

const viewLogs = (deployment: any) => {
  router.push(`/deployments/${deployment.id}/logs`)
}

const viewMetrics = (deployment: any) => {
  router.push(`/deployments/${deployment.id}/metrics`)
}

const scaleDeployment = (deployment: any) => {
  router.push(`/deployments/${deployment.id}/scale`)
}

const copyEndpoint = async (endpoint: string) => {
  try {
    await navigator.clipboard.writeText(endpoint)
    ElMessage.success('API端点已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请手动复制')
  }
}

onMounted(async () => {
  const cached = sessionStorage.getItem('cachedEnvironments')
  if (cached) {
    try {
      environments.value = JSON.parse(cached) || []
    } catch {}
  }
  if (!environments.value || environments.value.length === 0) {
    try {
      const res = await environmentApi.getEnvironments({ page: 1, size: 100 })
      environments.value = (res as any).items || []
    } catch (e) {
      console.error('加载环境列表失败:', e)
      ElMessage.error('加载环境列表失败')
    }
  }
  await refreshDeployments()
})
</script>

<style lang="scss" scoped>
.deployments-page {
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
        }
        
        &.stopped {
          background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }
        
        &.requests {
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
  
  .deployments-list {
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
      .deployment-card {
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
        
        .deployment-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
          
          .deployment-info {
            .deployment-name {
              font-size: 16px;
              font-weight: 600;
              color: var(--el-text-color-primary);
              margin: 0 0 4px 0;
              line-height: 1.4;
            }
            
            .deployment-model {
              font-size: 14px;
              color: var(--el-text-color-secondary);
              margin: 0;
            }
          }
          
          .deployment-status {
            .status-blinking {
              animation: blink 1.5s infinite;
            }
          }
        }
        
        .deployment-content {
          flex: 1;
          
          .deployment-meta {
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
          
          .resource-usage {
            margin-bottom: 16px;
            
            .usage-item {
              display: flex;
              align-items: center;
              gap: 8px;
              margin-bottom: 8px;
              
              &:last-child {
                margin-bottom: 0;
              }
              
              .usage-label {
                display: flex;
                align-items: center;
                gap: 4px;
                font-size: 12px;
                color: var(--el-text-color-secondary);
                width: 50px;
                flex-shrink: 0;
                
                .el-icon {
                  font-size: 14px;
                }
              }
              
              .usage-bar {
                flex: 1;
                display: flex;
                align-items: center;
                gap: 8px;
                
                .usage-text {
                  font-size: 12px;
                  color: var(--el-text-color-secondary);
                  width: 35px;
                  text-align: right;
                }
              }
            }
          }
          
          .api-endpoint {
            margin-bottom: 16px;
            
            .endpoint-label {
              font-size: 12px;
              color: var(--el-text-color-secondary);
              margin-bottom: 4px;
            }
            
            .endpoint-url {
              :deep(.el-input) {
                .el-input__inner {
                  font-size: 12px;
                  font-family: 'Courier New', monospace;
                }
              }
            }
          }
        }
        
        .deployment-actions {
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
      .deployment-name-cell {
        .deployment-info {
          .name {
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 2px;
          }
          
          .model {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
      
      .resource-usage-table {
        .usage-row {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 4px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .usage-label {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            width: 35px;
            flex-shrink: 0;
          }
          
          .usage-value {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            width: 35px;
            text-align: right;
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

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0.5;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .deployments-page {
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
    
    .deployments-list {
      .grid-view {
        .deployment-card {
          .deployment-actions {
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
  .deployments-page {
    .stats-cards {
      .stat-card {
        background: var(--el-bg-color-page);
        border: 1px solid var(--el-border-color);
      }
    }
    
    .deployments-list {
      .grid-view {
        .deployment-card {
          background: var(--el-bg-color-page);
          border-color: var(--el-border-color);
        }
      }
    }
  }
}
</style>