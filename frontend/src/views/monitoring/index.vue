<template>
  <div class="monitoring-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Monitor /></el-icon>
            系统监控
          </h1>
          <p class="page-description">实时监控系统运行状态和性能指标</p>
        </div>
        <div class="header-right">
          <el-button-group>
            <el-button
              :type="timeRange === '1h' ? 'primary' : 'default'"
              @click="setTimeRange('1h')"
            >
              1小时
            </el-button>
            <el-button
              :type="timeRange === '6h' ? 'primary' : 'default'"
              @click="setTimeRange('6h')"
            >
              6小时
            </el-button>
            <el-button
              :type="timeRange === '24h' ? 'primary' : 'default'"
              @click="setTimeRange('24h')"
            >
              24小时
            </el-button>
            <el-button
              :type="timeRange === '7d' ? 'primary' : 'default'"
              @click="setTimeRange('7d')"
            >
              7天
            </el-button>
          </el-button-group>
          <el-button @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
          <el-switch
            v-model="autoRefresh"
            active-text="自动刷新"
            @change="toggleAutoRefresh"
          />
        </div>
      </div>
    </div>
    
    <!-- 系统状态概览 -->
    <div class="system-overview">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="status-card">
            <div class="status-content">
              <div class="status-icon healthy">
                <el-icon><CircleCheckFilled /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">系统状态</div>
                <div class="status-value healthy">正常</div>
                <div class="status-detail">运行时间: {{ systemUptime }}</div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="status-card">
            <div class="status-content">
              <div class="status-icon">
                <el-icon><Cpu /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">CPU使用率</div>
                <div class="status-value">{{ systemMetrics.cpu }}%</div>
                <div class="status-detail">
                  <el-progress
                    :percentage="systemMetrics.cpu"
                    :color="getProgressColor(systemMetrics.cpu)"
                    :show-text="false"
                    :stroke-width="4"
                  />
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="status-card">
            <div class="status-content">
              <div class="status-icon">
                <el-icon><Monitor /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">内存使用率</div>
                <div class="status-value">{{ systemMetrics.memory }}%</div>
                <div class="status-detail">
                  <el-progress
                    :percentage="systemMetrics.memory"
                    :color="getProgressColor(systemMetrics.memory)"
                    :show-text="false"
                    :stroke-width="4"
                  />
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <el-card shadow="hover" class="status-card">
            <div class="status-content">
              <div class="status-icon">
                <el-icon><Files /></el-icon>
              </div>
              <div class="status-info">
                <div class="status-title">磁盘使用率</div>
                <div class="status-value">{{ systemMetrics.disk }}%</div>
                <div class="status-detail">
                  <el-progress
                    :percentage="systemMetrics.disk"
                    :color="getProgressColor(systemMetrics.disk)"
                    :show-text="false"
                    :stroke-width="4"
                  />
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- GPU监控 -->
    <div class="gpu-monitoring">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <h3>
              <el-icon><VideoCamera /></el-icon>
              GPU监控
            </h3>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col
            v-for="(gpu, index) in gpuMetrics"
            :key="index"
            :xs="24" :sm="12" :md="8" :lg="6"
          >
            <div class="gpu-card">
              <div class="gpu-header">
                <div class="gpu-name">{{ gpu.name }}</div>
                <div class="gpu-status" :class="gpu.status">
                  {{ getGpuStatusText(gpu.status) }}
                </div>
              </div>
              
              <div class="gpu-metrics">
                <div class="metric-item">
                  <div class="metric-label">GPU使用率</div>
                  <div class="metric-value">{{ gpu.utilization }}%</div>
                  <el-progress
                    :percentage="gpu.utilization"
                    :color="getProgressColor(gpu.utilization)"
                    :show-text="false"
                    :stroke-width="4"
                  />
                </div>
                
                <div class="metric-item">
                  <div class="metric-label">显存使用</div>
                  <div class="metric-value">{{ gpu.memory_used }}GB / {{ gpu.memory_total }}GB</div>
                  <el-progress
                    :percentage="(gpu.memory_used / gpu.memory_total) * 100"
                    :color="getProgressColor((gpu.memory_used / gpu.memory_total) * 100)"
                    :show-text="false"
                    :stroke-width="4"
                  />
                </div>
                
                <div class="metric-item">
                  <div class="metric-label">温度</div>
                  <div class="metric-value">{{ gpu.temperature }}°C</div>
                  <el-progress
                    :percentage="(gpu.temperature / 90) * 100"
                    :color="getTemperatureColor(gpu.temperature)"
                    :show-text="false"
                    :stroke-width="4"
                  />
                </div>
                
                <div class="metric-item">
                  <div class="metric-label">功耗</div>
                  <div class="metric-value">{{ gpu.power }}W / {{ gpu.power_limit }}W</div>
                  <el-progress
                    :percentage="(gpu.power / gpu.power_limit) * 100"
                    :color="getProgressColor((gpu.power / gpu.power_limit) * 100)"
                    :show-text="false"
                    :stroke-width="4"
                  />
                </div>
              </div>
              
              <div v-if="gpu.processes.length > 0" class="gpu-processes">
                <div class="processes-title">运行进程</div>
                <div
                  v-for="process in gpu.processes"
                  :key="process.pid"
                  class="process-item"
                >
                  <div class="process-name">{{ process.name }}</div>
                  <div class="process-memory">{{ process.memory }}MB</div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
    
    <!-- 性能图表 -->
    <div class="performance-charts">
      <el-row :gutter="20">
        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>
                  <el-icon><TrendCharts /></el-icon>
                  CPU & 内存使用趋势
                </h3>
              </div>
            </template>
            <div ref="cpuMemoryChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>
                  <el-icon><Connection /></el-icon>
                  网络流量
                </h3>
              </div>
            </template>
            <div ref="networkChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>
                  <el-icon><VideoCamera /></el-icon>
                  GPU使用率趋势
                </h3>
              </div>
            </template>
            <div ref="gpuChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
        
        <el-col :xs="24" :lg="12">
          <el-card shadow="never">
            <template #header>
              <div class="card-header">
                <h3>
                  <el-icon><DataAnalysis /></el-icon>
                  API请求统计
                </h3>
              </div>
            </template>
            <div ref="apiChartRef" class="chart-container"></div>
          </el-card>
        </el-col>
      </el-row>
    </div>
    
    <!-- 服务状态 -->
    <div class="service-status">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <h3>
              <el-icon><Service /></el-icon>
              服务状态
            </h3>
          </div>
        </template>
        
        <el-row :gutter="20">
          <el-col
            v-for="service in services"
            :key="service.name"
            :xs="24" :sm="12" :md="8" :lg="6"
          >
            <div class="service-card">
              <div class="service-header">
                <div class="service-name">{{ service.name }}</div>
                <div class="service-status" :class="service.status">
                  <el-icon v-if="service.status === 'running'">
                    <CircleCheckFilled />
                  </el-icon>
                  <el-icon v-else-if="service.status === 'stopped'">
                    <CircleCloseFilled />
                  </el-icon>
                  <el-icon v-else>
                    <WarningFilled />
                  </el-icon>
                  {{ getServiceStatusText(service.status) }}
                </div>
              </div>
              
              <div class="service-info">
                <div class="info-item">
                  <span class="label">端口:</span>
                  <span class="value">{{ service.port }}</span>
                </div>
                <div class="info-item">
                  <span class="label">CPU:</span>
                  <span class="value">{{ service.cpu }}%</span>
                </div>
                <div class="info-item">
                  <span class="label">内存:</span>
                  <span class="value">{{ service.memory }}MB</span>
                </div>
                <div class="info-item">
                  <span class="label">运行时间:</span>
                  <span class="value">{{ service.uptime }}</span>
                </div>
              </div>
              
              <div class="service-actions">
                <el-button
                  v-if="service.status === 'stopped'"
                  size="small"
                  type="primary"
                  @click="startService(service.name)"
                >
                  启动
                </el-button>
                <el-button
                  v-else-if="service.status === 'running'"
                  size="small"
                  type="danger"
                  @click="stopService(service.name)"
                >
                  停止
                </el-button>
                <el-button
                  size="small"
                  @click="restartService(service.name)"
                >
                  重启
                </el-button>
                <el-button
                  size="small"
                  @click="viewServiceLogs(service.name)"
                >
                  日志
                </el-button>
              </div>
            </div>
          </el-col>
        </el-row>
      </el-card>
    </div>
    
    <!-- 告警信息 -->
    <div class="alerts-section">
      <el-card shadow="never">
        <template #header>
          <div class="card-header">
            <h3>
              <el-icon><Bell /></el-icon>
              系统告警
            </h3>
            <el-button size="small" @click="clearAllAlerts">
              清除所有
            </el-button>
          </div>
        </template>
        
        <div v-if="alerts.length === 0" class="no-alerts">
          <el-empty description="暂无告警信息" />
        </div>
        
        <div v-else class="alerts-list">
          <div
            v-for="alert in alerts"
            :key="alert.id"
            :class="['alert-item', alert.level]"
          >
            <div class="alert-icon">
              <el-icon v-if="alert.level === 'critical'">
                <CircleCloseFilled />
              </el-icon>
              <el-icon v-else-if="alert.level === 'warning'">
                <WarningFilled />
              </el-icon>
              <el-icon v-else>
                <InfoFilled />
              </el-icon>
            </div>
            
            <div class="alert-content">
              <div class="alert-title">{{ alert.title }}</div>
              <div class="alert-message">{{ alert.message }}</div>
              <div class="alert-time">{{ formatDate(alert.timestamp) }}</div>
            </div>
            
            <div class="alert-actions">
              <el-button
                size="small"
                @click="dismissAlert(alert.id)"
              >
                忽略
              </el-button>
              <el-button
                size="small"
                type="primary"
                @click="handleAlert(alert)"
              >
                处理
              </el-button>
            </div>
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Monitor,
  Refresh,
  CircleCheckFilled,
  CircleCloseFilled,
  WarningFilled,
  InfoFilled,
  Cpu,
  Files,
  VideoCamera,
  TrendCharts,
  Connection,
  DataAnalysis,
  Service,
  Bell
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'

// 响应式数据
const timeRange = ref('1h')
const autoRefresh = ref(true)
const refreshTimer = ref(null)

// 图表引用
const cpuMemoryChartRef = ref(null)
const networkChartRef = ref(null)
const gpuChartRef = ref(null)
const apiChartRef = ref(null)

// 图表实例
let cpuMemoryChart = null
let networkChart = null
let gpuChart = null
let apiChart = null

// 系统运行时间
const systemUptime = ref('15天 8小时 32分钟')

// 系统指标
const systemMetrics = reactive({
  cpu: 45,
  memory: 68,
  disk: 32
})

// GPU指标
const gpuMetrics = ref([
  {
    name: 'NVIDIA RTX 4090',
    status: 'running',
    utilization: 85,
    memory_used: 18.5,
    memory_total: 24,
    temperature: 72,
    power: 380,
    power_limit: 450,
    processes: [
      { pid: 1234, name: 'python', memory: 8192 },
      { pid: 5678, name: 'training_job', memory: 10240 }
    ]
  },
  {
    name: 'NVIDIA RTX 4080',
    status: 'running',
    utilization: 32,
    memory_used: 6.2,
    memory_total: 16,
    temperature: 58,
    power: 180,
    power_limit: 320,
    processes: [
      { pid: 9012, name: 'inference_server', memory: 4096 }
    ]
  },
  {
    name: 'NVIDIA RTX 3090',
    status: 'idle',
    utilization: 0,
    memory_used: 0.5,
    memory_total: 24,
    temperature: 35,
    power: 45,
    power_limit: 350,
    processes: []
  },
  {
    name: 'NVIDIA RTX 3080',
    status: 'error',
    utilization: 0,
    memory_used: 0,
    memory_total: 10,
    temperature: 0,
    power: 0,
    power_limit: 320,
    processes: []
  }
])

// 服务状态
const services = ref([
  {
    name: 'API服务',
    status: 'running',
    port: 8000,
    cpu: 12.5,
    memory: 256,
    uptime: '5天 12小时'
  },
  {
    name: '训练服务',
    status: 'running',
    port: 8001,
    cpu: 45.2,
    memory: 1024,
    uptime: '2天 8小时'
  },
  {
    name: '推理服务',
    status: 'running',
    port: 8002,
    cpu: 8.7,
    memory: 512,
    uptime: '1天 15小时'
  },
  {
    name: '数据库',
    status: 'running',
    port: 5432,
    cpu: 3.2,
    memory: 128,
    uptime: '15天 8小时'
  },
  {
    name: 'Redis',
    status: 'running',
    port: 6379,
    cpu: 1.5,
    memory: 64,
    uptime: '15天 8小时'
  },
  {
    name: '监控服务',
    status: 'stopped',
    port: 9090,
    cpu: 0,
    memory: 0,
    uptime: '-'
  },
  {
    name: '日志服务',
    status: 'running',
    port: 5601,
    cpu: 2.1,
    memory: 96,
    uptime: '10天 3小时'
  },
  {
    name: '文件服务',
    status: 'error',
    port: 9000,
    cpu: 0,
    memory: 0,
    uptime: '-'
  }
])

// 告警信息
const alerts = ref([
  {
    id: '1',
    level: 'critical',
    title: 'GPU温度过高',
    message: 'NVIDIA RTX 4090 温度达到 85°C，超过安全阈值',
    timestamp: '2024-01-21T10:30:00Z'
  },
  {
    id: '2',
    level: 'warning',
    title: '内存使用率较高',
    message: '系统内存使用率达到 85%，建议释放部分内存',
    timestamp: '2024-01-21T10:25:00Z'
  },
  {
    id: '3',
    level: 'info',
    title: '训练任务完成',
    message: '模型训练任务 "ResNet-50" 已成功完成',
    timestamp: '2024-01-21T10:20:00Z'
  }
])

// 方法
const getProgressColor = (percentage: number) => {
  if (percentage < 50) return '#67c23a'
  if (percentage < 80) return '#e6a23c'
  return '#f56c6c'
}

const getTemperatureColor = (temperature: number) => {
  if (temperature < 60) return '#67c23a'
  if (temperature < 80) return '#e6a23c'
  return '#f56c6c'
}

const getGpuStatusText = (status: string) => {
  const statusMap = {
    running: '运行中',
    idle: '空闲',
    error: '错误'
  }
  return statusMap[status] || status
}

const getServiceStatusText = (status: string) => {
  const statusMap = {
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return statusMap[status] || status
}

const formatDate = (date: string) => {
  return new Date(date).toLocaleString('zh-CN')
}

const setTimeRange = (range: string) => {
  timeRange.value = range
  updateCharts()
}

const refreshData = async () => {
  try {
    // 模拟数据刷新
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 更新系统指标
    systemMetrics.cpu = Math.floor(Math.random() * 100)
    systemMetrics.memory = Math.floor(Math.random() * 100)
    systemMetrics.disk = Math.floor(Math.random() * 100)
    
    // 更新GPU指标
    gpuMetrics.value.forEach(gpu => {
      if (gpu.status === 'running') {
        gpu.utilization = Math.floor(Math.random() * 100)
        gpu.temperature = 40 + Math.floor(Math.random() * 40)
        gpu.power = Math.floor(Math.random() * gpu.power_limit)
      }
    })
    
    updateCharts()
    ElMessage.success('数据刷新成功')
  } catch (error) {
    console.error('刷新数据失败:', error)
    ElMessage.error('刷新失败，请稍后重试')
  }
}

const toggleAutoRefresh = () => {
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

const startAutoRefresh = () => {
  refreshTimer.value = setInterval(() => {
    refreshData()
  }, 30000) // 每30秒刷新一次
}

const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

const startService = async (serviceName: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要启动服务 "${serviceName}" 吗？`,
      '确认启动',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 模拟启动服务
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const service = services.value.find(s => s.name === serviceName)
    if (service) {
      service.status = 'running'
      service.cpu = Math.floor(Math.random() * 20)
      service.memory = Math.floor(Math.random() * 500) + 50
      service.uptime = '刚刚启动'
    }
    
    ElMessage.success(`服务 "${serviceName}" 启动成功`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('启动服务失败:', error)
      ElMessage.error('启动失败，请稍后重试')
    }
  }
}

const stopService = async (serviceName: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要停止服务 "${serviceName}" 吗？`,
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 模拟停止服务
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    const service = services.value.find(s => s.name === serviceName)
    if (service) {
      service.status = 'stopped'
      service.cpu = 0
      service.memory = 0
      service.uptime = '-'
    }
    
    ElMessage.success(`服务 "${serviceName}" 停止成功`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停止服务失败:', error)
      ElMessage.error('停止失败，请稍后重试')
    }
  }
}

const restartService = async (serviceName: string) => {
  try {
    await ElMessageBox.confirm(
      `确定要重启服务 "${serviceName}" 吗？`,
      '确认重启',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 模拟重启服务
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    const service = services.value.find(s => s.name === serviceName)
    if (service) {
      service.status = 'running'
      service.cpu = Math.floor(Math.random() * 20)
      service.memory = Math.floor(Math.random() * 500) + 50
      service.uptime = '刚刚重启'
    }
    
    ElMessage.success(`服务 "${serviceName}" 重启成功`)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重启服务失败:', error)
      ElMessage.error('重启失败，请稍后重试')
    }
  }
}

const viewServiceLogs = (serviceName: string) => {
  // 这里应该跳转到日志页面或打开日志对话框
  ElMessage.info(`查看服务 "${serviceName}" 的日志`)
}

const dismissAlert = (alertId: string) => {
  const index = alerts.value.findIndex(alert => alert.id === alertId)
  if (index > -1) {
    alerts.value.splice(index, 1)
    ElMessage.success('告警已忽略')
  }
}

const handleAlert = (alert: any) => {
  ElMessage.info(`处理告警: ${alert.title}`)
  // 这里应该实现具体的告警处理逻辑
}

const clearAllAlerts = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要清除所有告警吗？',
      '确认清除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    alerts.value = []
    ElMessage.success('所有告警已清除')
  } catch (error) {
    // 用户取消
  }
}

// 图表相关方法
const initCharts = () => {
  nextTick(() => {
    initCpuMemoryChart()
    initNetworkChart()
    initGpuChart()
    initApiChart()
  })
}

const initCpuMemoryChart = () => {
  if (!cpuMemoryChartRef.value) return
  
  cpuMemoryChart = echarts.init(cpuMemoryChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['CPU使用率', '内存使用率']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: generateTimeLabels()
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'CPU使用率',
        type: 'line',
        smooth: true,
        data: generateRandomData(24, 20, 80),
        itemStyle: {
          color: '#5470c6'
        }
      },
      {
        name: '内存使用率',
        type: 'line',
        smooth: true,
        data: generateRandomData(24, 30, 90),
        itemStyle: {
          color: '#91cc75'
        }
      }
    ]
  }
  
  cpuMemoryChart.setOption(option)
}

const initNetworkChart = () => {
  if (!networkChartRef.value) return
  
  networkChart = echarts.init(networkChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['入站流量', '出站流量']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: generateTimeLabels()
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} MB/s'
      }
    },
    series: [
      {
        name: '入站流量',
        type: 'line',
        smooth: true,
        data: generateRandomData(24, 10, 100),
        itemStyle: {
          color: '#fac858'
        },
        areaStyle: {
          opacity: 0.3
        }
      },
      {
        name: '出站流量',
        type: 'line',
        smooth: true,
        data: generateRandomData(24, 5, 80),
        itemStyle: {
          color: '#ee6666'
        },
        areaStyle: {
          opacity: 0.3
        }
      }
    ]
  }
  
  networkChart.setOption(option)
}

const initGpuChart = () => {
  if (!gpuChartRef.value) return
  
  gpuChart = echarts.init(gpuChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['GPU 0', 'GPU 1', 'GPU 2', 'GPU 3']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: generateTimeLabels()
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'GPU 0',
        type: 'line',
        smooth: true,
        data: generateRandomData(24, 60, 95),
        itemStyle: {
          color: '#5470c6'
        }
      },
      {
        name: 'GPU 1',
        type: 'line',
        smooth: true,
        data: generateRandomData(24, 20, 60),
        itemStyle: {
          color: '#91cc75'
        }
      },
      {
        name: 'GPU 2',
        type: 'line',
        smooth: true,
        data: generateRandomData(24, 0, 10),
        itemStyle: {
          color: '#fac858'
        }
      },
      {
        name: 'GPU 3',
        type: 'line',
        smooth: true,
        data: new Array(24).fill(0),
        itemStyle: {
          color: '#ee6666'
        }
      }
    ]
  }
  
  gpuChart.setOption(option)
}

const initApiChart = () => {
  if (!apiChartRef.value) return
  
  apiChart = echarts.init(apiChartRef.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['成功请求', '失败请求']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: generateTimeLabels()
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value} 次/分钟'
      }
    },
    series: [
      {
        name: '成功请求',
        type: 'bar',
        data: generateRandomData(24, 50, 200),
        itemStyle: {
          color: '#67c23a'
        }
      },
      {
        name: '失败请求',
        type: 'bar',
        data: generateRandomData(24, 0, 20),
        itemStyle: {
          color: '#f56c6c'
        }
      }
    ]
  }
  
  apiChart.setOption(option)
}

const updateCharts = () => {
  // 更新图表数据
  if (cpuMemoryChart) {
    cpuMemoryChart.setOption({
      xAxis: {
        data: generateTimeLabels()
      },
      series: [
        {
          data: generateRandomData(24, 20, 80)
        },
        {
          data: generateRandomData(24, 30, 90)
        }
      ]
    })
  }
  
  if (networkChart) {
    networkChart.setOption({
      xAxis: {
        data: generateTimeLabels()
      },
      series: [
        {
          data: generateRandomData(24, 10, 100)
        },
        {
          data: generateRandomData(24, 5, 80)
        }
      ]
    })
  }
  
  if (gpuChart) {
    gpuChart.setOption({
      xAxis: {
        data: generateTimeLabels()
      },
      series: [
        {
          data: generateRandomData(24, 60, 95)
        },
        {
          data: generateRandomData(24, 20, 60)
        },
        {
          data: generateRandomData(24, 0, 10)
        },
        {
          data: new Array(24).fill(0)
        }
      ]
    })
  }
  
  if (apiChart) {
    apiChart.setOption({
      xAxis: {
        data: generateTimeLabels()
      },
      series: [
        {
          data: generateRandomData(24, 50, 200)
        },
        {
          data: generateRandomData(24, 0, 20)
        }
      ]
    })
  }
}

const generateTimeLabels = () => {
  const labels = []
  const now = new Date()
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60 * 60 * 1000)
    labels.push(time.getHours().toString().padStart(2, '0') + ':00')
  }
  
  return labels
}

const generateRandomData = (count: number, min: number, max: number) => {
  return Array.from({ length: count }, () => 
    Math.floor(Math.random() * (max - min + 1)) + min
  )
}

const resizeCharts = () => {
  cpuMemoryChart?.resize()
  networkChart?.resize()
  gpuChart?.resize()
  apiChart?.resize()
}

onMounted(() => {
  initCharts()
  if (autoRefresh.value) {
    startAutoRefresh()
  }
  
  // 监听窗口大小变化
  window.addEventListener('resize', resizeCharts)
})

onUnmounted(() => {
  stopAutoRefresh()
  
  // 销毁图表实例
  cpuMemoryChart?.dispose()
  networkChart?.dispose()
  gpuChart?.dispose()
  apiChart?.dispose()
  
  // 移除事件监听
  window.removeEventListener('resize', resizeCharts)
})
</script>

<style lang="scss" scoped>
.monitoring-page {
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
        align-items: center;
        gap: 12px;
      }
    }
  }
  
  .system-overview {
    margin-bottom: 20px;
    
    .status-card {
      .status-content {
        display: flex;
        align-items: center;
        gap: 16px;
        
        .status-icon {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--el-color-primary);
          
          .el-icon {
            font-size: 24px;
            color: white;
          }
          
          &.healthy {
            background: var(--el-color-success);
          }
        }
        
        .status-info {
          flex: 1;
          
          .status-title {
            font-size: 14px;
            color: var(--el-text-color-secondary);
            margin-bottom: 4px;
          }
          
          .status-value {
            font-size: 20px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
            
            &.healthy {
              color: var(--el-color-success);
            }
          }
          
          .status-detail {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
  
  .gpu-monitoring {
    margin-bottom: 20px;
    
    .gpu-card {
      border: 1px solid var(--el-border-color);
      border-radius: 8px;
      padding: 16px;
      background: var(--el-bg-color);
      
      .gpu-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        
        .gpu-name {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        .gpu-status {
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          
          &.running {
            background: rgba(103, 194, 58, 0.1);
            color: var(--el-color-success);
          }
          
          &.idle {
            background: rgba(144, 202, 249, 0.1);
            color: var(--el-color-info);
          }
          
          &.error {
            background: rgba(245, 108, 108, 0.1);
            color: var(--el-color-danger);
          }
        }
      }
      
      .gpu-metrics {
        .metric-item {
          margin-bottom: 12px;
          
          &:last-child {
            margin-bottom: 0;
          }
          
          .metric-label {
            font-size: 12px;
            color: var(--el-text-color-secondary);
            margin-bottom: 4px;
          }
          
          .metric-value {
            font-size: 14px;
            font-weight: 500;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }
        }
      }
      
      .gpu-processes {
        margin-top: 16px;
        padding-top: 16px;
        border-top: 1px solid var(--el-border-color-lighter);
        
        .processes-title {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          margin-bottom: 8px;
        }
        
        .process-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 4px 0;
          font-size: 12px;
          
          .process-name {
            color: var(--el-text-color-primary);
          }
          
          .process-memory {
            color: var(--el-text-color-secondary);
          }
        }
      }
    }
  }
  
  .performance-charts {
    margin-bottom: 20px;
    
    .chart-container {
      height: 300px;
      width: 100%;
    }
  }
  
  .service-status {
    margin-bottom: 20px;
    
    .service-card {
      border: 1px solid var(--el-border-color);
      border-radius: 8px;
      padding: 16px;
      background: var(--el-bg-color);
      
      .service-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .service-name {
          font-size: 16px;
          font-weight: 600;
          color: var(--el-text-color-primary);
        }
        
        .service-status {
          display: flex;
          align-items: center;
          gap: 4px;
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 12px;
          font-weight: 500;
          
          &.running {
            background: rgba(103, 194, 58, 0.1);
            color: var(--el-color-success);
          }
          
          &.stopped {
            background: rgba(144, 202, 249, 0.1);
            color: var(--el-color-info);
          }
          
          &.error {
            background: rgba(245, 108, 108, 0.1);
            color: var(--el-color-danger);
          }
        }
      }
      
      .service-info {
        margin-bottom: 16px;
        
        .info-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 4px 0;
          font-size: 14px;
          
          .label {
            color: var(--el-text-color-secondary);
          }
          
          .value {
            color: var(--el-text-color-primary);
            font-weight: 500;
          }
        }
      }
      
      .service-actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        
        .el-button {
          flex: 1;
          min-width: 60px;
        }
      }
    }
  }
  
  .alerts-section {
    .no-alerts {
      text-align: center;
      padding: 40px 0;
    }
    
    .alerts-list {
      .alert-item {
        display: flex;
        align-items: flex-start;
        gap: 12px;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 12px;
        
        &:last-child {
          margin-bottom: 0;
        }
        
        &.critical {
          background: rgba(245, 108, 108, 0.05);
          border-left: 4px solid var(--el-color-danger);
        }
        
        &.warning {
          background: rgba(230, 162, 60, 0.05);
          border-left: 4px solid var(--el-color-warning);
        }
        
        &.info {
          background: rgba(144, 202, 249, 0.05);
          border-left: 4px solid var(--el-color-info);
        }
        
        .alert-icon {
          .el-icon {
            font-size: 20px;
          }
        }
        
        .alert-content {
          flex: 1;
          
          .alert-title {
            font-size: 16px;
            font-weight: 600;
            color: var(--el-text-color-primary);
            margin-bottom: 4px;
          }
          
          .alert-message {
            font-size: 14px;
            color: var(--el-text-color-regular);
            margin-bottom: 8px;
          }
          
          .alert-time {
            font-size: 12px;
            color: var(--el-text-color-secondary);
          }
        }
        
        .alert-actions {
          display: flex;
          gap: 8px;
        }
      }
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h3 {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 18px;
      font-weight: 600;
      color: var(--el-text-color-primary);
      margin: 0;
    }
  }
}

// 响应式设计
@media (max-width: 768px) {
  .monitoring-page {
    padding: 16px;
    
    .page-header {
      .header-content {
        flex-direction: column;
        gap: 16px;
        
        .header-right {
          align-self: stretch;
          flex-wrap: wrap;
          
          .el-button-group {
            flex: 1;
            
            .el-button {
              flex: 1;
            }
          }
        }
      }
    }
    
    .performance-charts {
      .chart-container {
        height: 250px;
      }
    }
    
    .service-status {
      .service-card {
        .service-actions {
          .el-button {
            min-width: 50px;
            font-size: 12px;
          }
        }
      }
    }
    
    .alerts-section {
      .alerts-list {
        .alert-item {
          flex-direction: column;
          gap: 8px;
          
          .alert-actions {
            align-self: stretch;
            
            .el-button {
              flex: 1;
            }
          }
        }
      }
    }
  }
}

// 暗色主题
.dark {
  .monitoring-page {
    .gpu-monitoring {
      .gpu-card {
        background: var(--el-bg-color-page);
        border-color: var(--el-border-color-darker);
      }
    }
    
    .service-status {
      .service-card {
        background: var(--el-bg-color-page);
        border-color: var(--el-border-color-darker);
      }
    }
  }
}
</style>