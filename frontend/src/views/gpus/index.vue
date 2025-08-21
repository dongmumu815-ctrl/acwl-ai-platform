<template>
  <div class="gpus-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Cpu /></el-icon>
            GPU资源池
          </h1>
          <p class="page-description">管理和监控GPU资源使用情况</p>
        </div>
        <div class="header-right">
          <el-button @click="scanAllGpus" :loading="scanning">
            <el-icon><Refresh /></el-icon>
            扫描GPU
          </el-button>
          <el-button @click="refreshGpus">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon total">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">GPU总数</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon available">
              <el-icon><CircleCheckFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.available }}</div>
              <div class="stat-label">可用</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon busy">
              <el-icon><Loading /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.busy }}</div>
              <div class="stat-label">使用中</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon error">
              <el-icon><CircleCloseFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.error }}</div>
              <div class="stat-label">异常</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 搜索和筛选 -->
    <div class="search-section">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="8">
          <el-input
            v-model="searchQuery"
            placeholder="搜索GPU型号、服务器..."
            @input="handleSearch"
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select
            v-model="filterStatus"
            placeholder="状态"
            @change="handleFilter"
            clearable
          >
            <el-option label="可用" value="available" />
            <el-option label="使用中" value="busy" />
            <el-option label="异常" value="error" />
          </el-select>
        </el-col>
        <el-col :xs="12" :sm="4">
          <el-select
            v-model="filterServer"
            placeholder="服务器"
            @change="handleFilter"
            clearable
          >
            <el-option
              v-for="server in servers"
              :key="server.id"
              :label="server.name"
              :value="server.id"
            />
          </el-select>
        </el-col>
      </el-row>
    </div>

    <!-- GPU列表 -->
    <div class="gpus-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <span>GPU列表</span>
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
          <div class="gpus-grid">
            <div
              v-for="gpu in filteredGpus"
              :key="gpu.id"
              class="gpu-card"
              :class="gpu.status"
            >
              <div class="gpu-header">
                <div class="gpu-info">
                  <div class="gpu-name">{{ gpu.name }}</div>
                  <div class="gpu-server">{{ gpu.server_name }}</div>
                </div>
                <div class="gpu-status" :class="gpu.status">
                  <el-icon v-if="gpu.status === 'available'">
                    <CircleCheckFilled />
                  </el-icon>
                  <el-icon v-else-if="gpu.status === 'busy'">
                    <Loading />
                  </el-icon>
                  <el-icon v-else>
                    <CircleCloseFilled />
                  </el-icon>
                  {{ getStatusText(gpu.status) }}
                </div>
              </div>
              
              <div class="gpu-details">
                <div class="detail-item">
                  <span class="label">型号:</span>
                  <span class="value">{{ gpu.model || '未知' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">显存:</span>
                  <span class="value">{{ gpu.memory_total || '未知' }}</span>
                </div>
                <div class="detail-item">
                  <span class="label">使用率:</span>
                  <span class="value">{{ gpu.utilization || 0 }}%</span>
                </div>
                <div class="detail-item">
                  <span class="label">温度:</span>
                  <span class="value">{{ gpu.temperature || 0 }}°C</span>
                </div>
                <div class="detail-item">
                  <span class="label">功耗:</span>
                  <span class="value">{{ gpu.power_usage || 0 }}W</span>
                </div>
                <div class="detail-item">
                  <span class="label">部署:</span>
                  <span class="value">{{ gpu.deployment_name || '无' }}</span>
                </div>
              </div>
              
              <!-- 使用率进度条 -->
              <div class="gpu-progress">
                <div class="progress-label">GPU使用率</div>
                <el-progress
                  :percentage="gpu.utilization || 0"
                  :color="getProgressColor(gpu.utilization)"
                  :stroke-width="6"
                />
              </div>
              
              <div class="gpu-actions">
                <el-button
                  size="small"
                  @click="viewGpuDetail(gpu)"
                >
                  详情
                </el-button>
                <el-button
                  v-if="gpu.status === 'busy'"
                  size="small"
                  type="warning"
                  @click="releaseGpu(gpu)"
                >
                  释放
                </el-button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 列表视图 -->
        <div v-else class="list-view">
          <el-table
            :data="filteredGpus"
            style="width: 100%"
            @row-click="viewGpuDetail"
          >
            <el-table-column prop="name" label="GPU名称" min-width="120" />
            <el-table-column prop="server_name" label="所属服务器" min-width="120" />
            <el-table-column prop="model" label="型号" min-width="150" />
            <el-table-column prop="memory_total" label="显存" min-width="100" />
            <el-table-column label="状态" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusTagType(row.status)">
                  {{ getStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="使用率" min-width="120">
              <template #default="{ row }">
                <el-progress
                  :percentage="row.utilization || 0"
                  :color="getProgressColor(row.utilization)"
                  :stroke-width="6"
                />
              </template>
            </el-table-column>
            <el-table-column prop="temperature" label="温度(°C)" min-width="80" />
            <el-table-column prop="power_usage" label="功耗(W)" min-width="80" />
            <el-table-column prop="deployment_name" label="当前部署" min-width="120" />
            <el-table-column label="操作" min-width="120" fixed="right">
              <template #default="{ row }">
                <el-button size="small" @click.stop="viewGpuDetail(row)">
                  详情
                </el-button>
                <el-button
                  v-if="row.status === 'busy'"
                  size="small"
                  type="warning"
                  @click.stop="releaseGpu(row)"
                >
                  释放
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-card>
    </div>

    <!-- GPU详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="GPU详情"
      width="600px"
    >
      <div v-if="selectedGpu" class="gpu-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="GPU名称">
            {{ selectedGpu.name }}
          </el-descriptions-item>
          <el-descriptions-item label="所属服务器">
            {{ selectedGpu.server_name }}
          </el-descriptions-item>
          <el-descriptions-item label="GPU型号">
            {{ selectedGpu.model || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusTagType(selectedGpu.status)">
              {{ getStatusText(selectedGpu.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="显存总量">
            {{ selectedGpu.memory_total || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="已用显存">
            {{ selectedGpu.memory_used || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="GPU使用率">
            {{ selectedGpu.utilization || 0 }}%
          </el-descriptions-item>
          <el-descriptions-item label="温度">
            {{ selectedGpu.temperature || 0 }}°C
          </el-descriptions-item>
          <el-descriptions-item label="功耗">
            {{ selectedGpu.power_usage || 0 }}W
          </el-descriptions-item>
          <el-descriptions-item label="当前部署">
            {{ selectedGpu.deployment_name || '无' }}
          </el-descriptions-item>
          <el-descriptions-item label="驱动版本" span="2">
            {{ selectedGpu.driver_version || '未知' }}
          </el-descriptions-item>
          <el-descriptions-item label="最后更新" span="2">
            {{ formatTime(selectedGpu.updated_at) }}
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Cpu,
  CircleCheckFilled,
  CircleCloseFilled,
  Loading,
  Refresh,
  Search,
  Grid,
  List
} from '@element-plus/icons-vue'

// 响应式数据
const loading = ref(false)
const scanning = ref(false)
const searchQuery = ref('')
const filterStatus = ref('')
const filterServer = ref('')
const viewMode = ref('grid')
const detailDialogVisible = ref(false)
const selectedGpu = ref(null)

// 统计数据
const stats = reactive({
  total: 0,
  available: 0,
  busy: 0,
  error: 0
})

// GPU列表和服务器列表
const gpus = ref([])
const servers = ref([])

/**
 * 计算过滤后的GPU列表
 */
const filteredGpus = computed(() => {
  let result = gpus.value
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(gpu => 
      gpu.name.toLowerCase().includes(query) ||
      gpu.model?.toLowerCase().includes(query) ||
      gpu.server_name.toLowerCase().includes(query)
    )
  }
  
  // 状态过滤
  if (filterStatus.value) {
    result = result.filter(gpu => gpu.status === filterStatus.value)
  }
  
  // 服务器过滤
  if (filterServer.value) {
    result = result.filter(gpu => gpu.server_id === filterServer.value)
  }
  
  return result
})

/**
 * 获取状态文本
 */
function getStatusText(status: string): string {
  const statusMap = {
    available: '可用',
    busy: '使用中',
    error: '异常',
    offline: '离线'
  }
  return statusMap[status] || '未知'
}

/**
 * 获取状态标签类型
 */
function getStatusTagType(status: string): string {
  const typeMap = {
    available: 'success',
    busy: 'warning',
    error: 'danger',
    offline: 'info'
  }
  return typeMap[status] || 'info'
}

/**
 * 获取进度条颜色
 */
function getProgressColor(percentage: number): string {
  if (percentage < 30) return '#67c23a'
  if (percentage < 70) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 格式化时间
 */
function formatTime(time: string): string {
  if (!time) return '未知'
  return new Date(time).toLocaleString()
}

/**
 * 加载GPU列表
 */
async function loadGpus() {
  try {
    loading.value = true
    // TODO: 调用API获取GPU列表
    // const response = await gpuApi.getGpus()
    
    // 模拟数据
    gpus.value = [
      {
        id: 1,
        name: 'GPU-0',
        server_id: 1,
        server_name: 'GPU-Server-01',
        model: 'NVIDIA RTX 4090',
        memory_total: '24GB',
        memory_used: '8GB',
        utilization: 65,
        temperature: 72,
        power_usage: 320,
        status: 'busy',
        deployment_name: 'ChatGLM-6B',
        driver_version: '535.86.10',
        updated_at: new Date().toISOString()
      },
      {
        id: 2,
        name: 'GPU-1',
        server_id: 1,
        server_name: 'GPU-Server-01',
        model: 'NVIDIA RTX 4090',
        memory_total: '24GB',
        memory_used: '0GB',
        utilization: 0,
        temperature: 45,
        power_usage: 50,
        status: 'available',
        deployment_name: null,
        driver_version: '535.86.10',
        updated_at: new Date().toISOString()
      },
      {
        id: 3,
        name: 'GPU-0',
        server_id: 2,
        server_name: 'GPU-Server-02',
        model: 'NVIDIA RTX 3090',
        memory_total: '24GB',
        memory_used: '12GB',
        utilization: 85,
        temperature: 78,
        power_usage: 350,
        status: 'busy',
        deployment_name: 'Llama2-7B',
        driver_version: '535.86.10',
        updated_at: new Date().toISOString()
      }
    ]
    
    updateStats()
  } catch (error) {
    console.error('加载GPU列表失败:', error)
    ElMessage.error('加载GPU列表失败')
  } finally {
    loading.value = false
  }
}

/**
 * 加载服务器列表
 */
async function loadServers() {
  try {
    // TODO: 调用API获取服务器列表
    // const response = await serverApi.getServers()
    
    // 模拟数据
    servers.value = [
      { id: 1, name: 'GPU-Server-01' },
      { id: 2, name: 'GPU-Server-02' },
      { id: 3, name: 'GPU-Server-03' }
    ]
  } catch (error) {
    console.error('加载服务器列表失败:', error)
  }
}

/**
 * 更新统计数据
 */
function updateStats() {
  stats.total = gpus.value.length
  stats.available = gpus.value.filter(gpu => gpu.status === 'available').length
  stats.busy = gpus.value.filter(gpu => gpu.status === 'busy').length
  stats.error = gpus.value.filter(gpu => gpu.status === 'error').length
}

/**
 * 扫描所有GPU
 */
async function scanAllGpus() {
  try {
    scanning.value = true
    // TODO: 调用API扫描GPU
    // await gpuApi.scanAllGpus()
    
    ElMessage.success('GPU扫描完成')
    await loadGpus()
  } catch (error) {
    console.error('扫描GPU失败:', error)
    ElMessage.error('扫描GPU失败')
  } finally {
    scanning.value = false
  }
}

/**
 * 刷新GPU列表
 */
function refreshGpus() {
  loadGpus()
}

/**
 * 处理搜索
 */
function handleSearch() {
  // 搜索逻辑在computed中处理
}

/**
 * 处理筛选
 */
function handleFilter() {
  // 筛选逻辑在computed中处理
}

/**
 * 查看GPU详情
 */
function viewGpuDetail(gpu: any) {
  selectedGpu.value = gpu
  detailDialogVisible.value = true
}

/**
 * 释放GPU
 */
async function releaseGpu(gpu: any) {
  try {
    await ElMessageBox.confirm(
      `确定要释放GPU "${gpu.name}" 吗？这将停止当前部署。`,
      '确认释放',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // TODO: 调用API释放GPU
    // await gpuApi.releaseGpu(gpu.id)
    
    ElMessage.success('GPU释放成功')
    await loadGpus()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('释放GPU失败:', error)
      ElMessage.error('释放GPU失败')
    }
  }
}

// 组件挂载时加载数据
onMounted(() => {
  loadGpus()
  loadServers()
})
</script>

<style lang="scss" scoped>
.gpus-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  margin-bottom: 20px;
  
  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-left {
      .page-title {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 0 0 8px 0;
        font-size: 24px;
        font-weight: 600;
        color: #303133;
      }
      
      .page-description {
        margin: 0;
        color: #909399;
        font-size: 14px;
      }
    }
    
    .header-right {
      display: flex;
      gap: 12px;
    }
  }
}

.stats-section {
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
      
      &.available {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
      }
      
      &.busy {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
      }
      
      &.error {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
      }
    }
    
    .stat-content {
      .stat-value {
        font-size: 28px;
        font-weight: 600;
        color: #303133;
        line-height: 1;
        margin-bottom: 4px;
      }
      
      .stat-label {
        font-size: 14px;
        color: #909399;
      }
    }
  }
}

.search-section {
  margin-bottom: 20px;
}

.gpus-section {
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    .header-actions {
      display: flex;
      gap: 12px;
    }
  }
  
  .grid-view {
    .gpus-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
      gap: 20px;
      
      .gpu-card {
        background: white;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
        
        &:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
        }
        
        &.available {
          border-left: 4px solid #67c23a;
        }
        
        &.busy {
          border-left: 4px solid #e6a23c;
        }
        
        &.error {
          border-left: 4px solid #f56c6c;
        }
        
        .gpu-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 16px;
          
          .gpu-info {
            .gpu-name {
              font-size: 18px;
              font-weight: 600;
              color: #303133;
              margin-bottom: 4px;
            }
            
            .gpu-server {
              font-size: 14px;
              color: #909399;
            }
          }
          
          .gpu-status {
            display: flex;
            align-items: center;
            gap: 4px;
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 4px;
            
            &.available {
              background: #f0f9ff;
              color: #67c23a;
            }
            
            &.busy {
              background: #fdf6ec;
              color: #e6a23c;
            }
            
            &.error {
              background: #fef0f0;
              color: #f56c6c;
            }
          }
        }
        
        .gpu-details {
          margin-bottom: 16px;
          
          .detail-item {
            display: flex;
            justify-content: space-between;
            margin-bottom: 8px;
            
            .label {
              font-size: 14px;
              color: #909399;
            }
            
            .value {
              font-size: 14px;
              color: #303133;
              font-weight: 500;
            }
          }
        }
        
        .gpu-progress {
          margin-bottom: 16px;
          
          .progress-label {
            font-size: 12px;
            color: #909399;
            margin-bottom: 8px;
          }
        }
        
        .gpu-actions {
          display: flex;
          gap: 8px;
        }
      }
    }
  }
  
  .list-view {
    .el-table {
      .el-table__row {
        cursor: pointer;
        
        &:hover {
          background-color: #f5f7fa;
        }
      }
    }
  }
}

.gpu-detail {
  .el-descriptions {
    margin-top: 20px;
  }
}

// 响应式设计
@media (max-width: 768px) {
  .gpus-page {
    padding: 16px;
  }
  
  .page-header {
    .header-content {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }
  }
  
  .stats-section {
    .stat-card {
      padding: 16px;
      
      .stat-icon {
        width: 40px;
        height: 40px;
        margin-right: 12px;
        
        .el-icon {
          font-size: 20px;
        }
      }
      
      .stat-content {
        .stat-value {
          font-size: 24px;
        }
      }
    }
  }
  
  .gpus-section {
    .grid-view {
      .gpus-grid {
        grid-template-columns: 1fr;
      }
    }
  }
}
</style>