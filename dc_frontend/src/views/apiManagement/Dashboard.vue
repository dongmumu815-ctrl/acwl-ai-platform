<template>
  <div class="api-dashboard">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">
            <el-icon><Monitor /></el-icon>
            API仪表板
          </h1>
          <p class="page-description">API接口管理系统数据统计和监控</p>
        </div>
        <div class="header-right">
          <el-button @click="refreshData">
            <el-icon><Refresh /></el-icon>
            刷新数据
          </el-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <el-row :gutter="20">
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon customers">
              <el-icon><UserFilled /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalCustomers }}</div>
              <div class="stat-label">总平台数</div>
              <div class="stat-change positive">+{{ stats.activeCustomers }} 活跃</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon apis">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalApis }}</div>
              <div class="stat-label">API接口数</div>
              <div class="stat-change positive">+12 本月新增</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon batches">
              <el-icon><DataBoard /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ stats.totalBatches }}</div>
              <div class="stat-label">总批次数</div>
              <div class="stat-change">{{ stats.pendingBatches }} 待处理</div>
            </div>
          </div>
        </el-col>
        
        <el-col :xs="12" :sm="6">
          <div class="stat-card">
            <div class="stat-icon calls">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stat-content">
              <div class="stat-value">{{ formatNumber(stats.totalApiCalls) }}</div>
              <div class="stat-label">总调用次数</div>
              <div class="stat-change positive">+15.2% 较上月</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 图表区域 -->
    <el-row :gutter="20">
      <!-- API调用趋势 -->
      <el-col :span="12">
        <div class="page-card">
          <div class="card-header">
            <h3>API调用趋势</h3>
            <el-select v-model="callsTimeRange" size="small" @change="loadApiCallStats">
              <el-option label="最近7天" value="7d" />
              <el-option label="最近30天" value="30d" />
              <el-option label="最近90天" value="90d" />
            </el-select>
          </div>
          <div class="chart-container">
            <div ref="callsChartRef" class="chart"></div>
          </div>
        </div>
      </el-col>

      <!-- 批次状态分布 -->
      <el-col :span="12">
        <div class="page-card">
          <div class="card-header">
            <h3>批次状态分布</h3>
          </div>
          <div class="chart-container">
            <div ref="batchChartRef" class="chart"></div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px">
      <!-- 客户活跃度 -->
      <el-col :span="12">
        <div class="page-card">
          <div class="card-header">
            <h3>客户活跃度排行</h3>
          </div>
          <div class="activity-list">
            <div 
              v-for="(customer, index) in customerActivity" 
              :key="customer.customer_name"
              class="activity-item"
            >
              <div class="rank">{{ index + 1 }}</div>
              <div class="customer-info">
                <div class="customer-name">{{ customer.customer_name }}</div>
                <div class="last-call">最后调用: {{ formatDate(customer.last_call_date) }}</div>
              </div>
              <div class="call-count">{{ customer.api_calls }} 次</div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 系统状态 -->
      <el-col :span="12">
        <div class="page-card">
          <div class="card-header">
            <h3>系统状态</h3>
          </div>
          <div class="system-status">
            <div class="status-item">
              <div class="status-label">系统运行时间</div>
              <div class="status-value">15天 8小时 32分钟</div>
            </div>
            <div class="status-item">
              <div class="status-label">平均响应时间</div>
              <div class="status-value">125ms</div>
            </div>
            <div class="status-item">
              <div class="status-label">成功率</div>
              <div class="status-value success">99.8%</div>
            </div>
            <div class="status-item">
              <div class="status-label">错误率</div>
              <div class="status-value danger">0.2%</div>
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <div class="page-card" style="margin-top: 20px">
      <div class="card-header">
        <h3>最近活动</h3>
        <el-button size="small" @click="loadRecentActivity">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      <div class="recent-activity">
        <el-timeline>
          <el-timeline-item
            v-for="activity in recentActivity"
            :key="activity.id"
            :timestamp="formatDate(activity.timestamp)"
            :type="getActivityType(activity.type)"
          >
            <div class="activity-content">
              <div class="activity-title">{{ activity.title }}</div>
              <div class="activity-description">{{ activity.description }}</div>
            </div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { formatDate } from '@/utils/date'
import {
  getSystemStats,
  getBatchStatusStats,
  getApiCallStats,
  getCustomerActivityStats
} from '@/api/apiManagement'
import type { SystemStats, ApiCallStats, CustomerActivityStats } from '@/types/apiManagement'
import * as echarts from 'echarts'

/**
 * 响应式数据
 */
const loading = ref(false)
const callsChartRef = ref<HTMLElement>()
const batchChartRef = ref<HTMLElement>()
const callsTimeRange = ref('7d')

// 统计数据
const stats = reactive<SystemStats>({
  totalCustomers: 0,
  totalApis: 0,
  totalBatches: 0,
  totalUploads: 0,
  totalApiCalls: 0,
  activeCustomers: 0,
  pendingBatches: 0,
  processingBatches: 0,
  completedBatches: 0,
  failedBatches: 0
})

// 客户活跃度数据
const customerActivity = ref<CustomerActivityStats[]>([])

// 最近活动数据
const recentActivity = ref<Array<{
  id: string
  type: string
  title: string
  description: string
  timestamp: string
}>>([])

// 图表实例
let callsChart: echarts.ECharts | null = null
let batchChart: echarts.ECharts | null = null

/**
 * 生命周期钩子
 */
onMounted(() => {
  loadDashboardData()
  initCharts()
})

/**
 * 方法定义
 */

/**
 * 加载仪表板数据
 */
const loadDashboardData = async () => {
  try {
    loading.value = true
    
    // 并行加载所有数据
    const [
      systemStatsRes,
      batchStatsRes,
      apiCallStatsRes,
      customerActivityRes
    ] = await Promise.all([
      getSystemStats(),
      getBatchStatusStats(),
      getApiCallStats({ start_date: getDateBefore(7) }),
      getCustomerActivityStats({ limit: 10 })
    ])

    // 更新统计数据
    if (systemStatsRes.success) {
      Object.assign(stats, systemStatsRes.data)
    }

    // 更新客户活跃度
    if (customerActivityRes.success) {
      customerActivity.value = customerActivityRes.data
    }

    // 更新图表数据
    if (apiCallStatsRes.success) {
      updateCallsChart(apiCallStatsRes.data)
    }

    if (batchStatsRes.success) {
      updateBatchChart(batchStatsRes.data)
    }

    // 加载最近活动
    loadRecentActivity()

  } catch (error) {
    console.error('加载仪表板数据失败:', error)
    ElMessage.error('加载仪表板数据失败')
  } finally {
    loading.value = false
  }
}

/**
 * 初始化图表
 */
const initCharts = async () => {
  await nextTick()
  
  if (callsChartRef.value) {
    callsChart = echarts.init(callsChartRef.value)
  }
  
  if (batchChartRef.value) {
    batchChart = echarts.init(batchChartRef.value)
  }

  // 监听窗口大小变化
  window.addEventListener('resize', () => {
    callsChart?.resize()
    batchChart?.resize()
  })
}

/**
 * 更新API调用趋势图表
 */
const updateCallsChart = (data: ApiCallStats[]) => {
  if (!callsChart) return

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: ['总调用', '成功调用', '失败调用']
    },
    xAxis: {
      type: 'category',
      data: data.map(item => item.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总调用',
        type: 'line',
        data: data.map(item => item.calls),
        smooth: true,
        itemStyle: { color: '#409EFF' }
      },
      {
        name: '成功调用',
        type: 'line',
        data: data.map(item => item.success_calls),
        smooth: true,
        itemStyle: { color: '#67C23A' }
      },
      {
        name: '失败调用',
        type: 'line',
        data: data.map(item => item.failed_calls),
        smooth: true,
        itemStyle: { color: '#F56C6C' }
      }
    ]
  }

  callsChart.setOption(option)
}

/**
 * 更新批次状态分布图表
 */
const updateBatchChart = (data: any) => {
  if (!batchChart) return

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left'
    },
    series: [
      {
        name: '批次状态',
        type: 'pie',
        radius: '50%',
        data: [
          { value: data.pending, name: '待处理', itemStyle: { color: '#909399' } },
          { value: data.processing, name: '处理中', itemStyle: { color: '#E6A23C' } },
          { value: data.completed, name: '已完成', itemStyle: { color: '#67C23A' } },
          { value: data.failed, name: '失败', itemStyle: { color: '#F56C6C' } }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  batchChart.setOption(option)
}

/**
 * 加载API调用统计
 */
const loadApiCallStats = async () => {
  try {
    const days = parseInt(callsTimeRange.value.replace('d', ''))
    const response = await getApiCallStats({ 
      start_date: getDateBefore(days) 
    })
    
    if (response.success) {
      updateCallsChart(response.data)
    }
  } catch (error) {
    console.error('加载API调用统计失败:', error)
  }
}

/**
 * 加载最近活动
 */
const loadRecentActivity = () => {
  // 模拟最近活动数据
  recentActivity.value = [
    {
      id: '1',
      type: 'api_created',
      title: '新建API接口',
      description: '客户"测试公司"创建了API接口"用户查询"',
      timestamp: new Date(Date.now() - 300000).toISOString()
    },
    {
      id: '2',
      type: 'batch_completed',
      title: '批次处理完成',
      description: '批次"数据导入_20241009"处理完成，成功处理1000条记录',
      timestamp: new Date(Date.now() - 600000).toISOString()
    },
    {
      id: '3',
      type: 'customer_registered',
      title: '新客户注册',
      description: '新客户"科技有限公司"完成注册',
      timestamp: new Date(Date.now() - 900000).toISOString()
    },
    {
      id: '4',
      type: 'api_called',
      title: 'API调用异常',
      description: 'API"数据查询"调用失败，错误码500',
      timestamp: new Date(Date.now() - 1200000).toISOString()
    }
  ]
}

/**
 * 获取指定天数前的日期
 */
const getDateBefore = (days: number) => {
  const date = new Date()
  date.setDate(date.getDate() - days)
  return date.toISOString().split('T')[0]
}

/**
 * 格式化数字
 */
const formatNumber = (num: number) => {
  if (num >= 1000000) {
    return (num / 1000000).toFixed(1) + 'M'
  } else if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K'
  }
  return num.toString()
}

/**
 * 获取活动类型
 */
const getActivityType = (type: string) => {
  const types: Record<string, string> = {
    api_created: 'success',
    batch_completed: 'primary',
    customer_registered: 'info',
    api_called: 'warning'
  }
  return types[type] || 'primary'
}

/**
 * 刷新数据
 */
const refreshData = () => {
  loadDashboardData()
}
</script>

<style scoped lang="scss">
.api-dashboard {
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
          color: var(--el-text-color-primary);
        }
        
        .page-description {
          margin: 0;
          color: var(--el-text-color-regular);
        }
      }
    }
  }
  
  .stats-section {
    margin-bottom: 20px;
    
    .stat-card {
      display: flex;
      align-items: center;
      padding: 24px;
      background: white;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      
      .stat-icon {
        width: 56px;
        height: 56px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 20px;
        font-size: 28px;
        
        &.customers {
          background: #e3f2fd;
          color: #1976d2;
        }
        
        &.apis {
          background: #f3e5f5;
          color: #7b1fa2;
        }
        
        &.batches {
          background: #fff3e0;
          color: #f57c00;
        }
        
        &.calls {
          background: #e8f5e8;
          color: #388e3c;
        }
      }
      
      .stat-content {
        flex: 1;
        
        .stat-value {
          font-size: 28px;
          font-weight: 600;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 14px;
          color: var(--el-text-color-regular);
          margin-bottom: 4px;
        }
        
        .stat-change {
          font-size: 12px;
          color: var(--el-text-color-secondary);
          
          &.positive {
            color: var(--el-color-success);
          }
        }
      }
    }
  }
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 20px 0 20px;
    
    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 600;
    }
  }
  
  .chart-container {
    padding: 20px;
    
    .chart {
      width: 100%;
      height: 300px;
    }
  }
  
  .activity-list {
    padding: 20px;
    
    .activity-item {
      display: flex;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .rank {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: var(--el-color-primary);
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 600;
        margin-right: 16px;
      }
      
      .customer-info {
        flex: 1;
        
        .customer-name {
          font-weight: 500;
          color: var(--el-text-color-primary);
          margin-bottom: 4px;
        }
        
        .last-call {
          font-size: 12px;
          color: var(--el-text-color-secondary);
        }
      }
      
      .call-count {
        font-weight: 600;
        color: var(--el-color-primary);
      }
    }
  }
  
  .system-status {
    padding: 20px;
    
    .status-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 0;
      border-bottom: 1px solid var(--el-border-color-lighter);
      
      &:last-child {
        border-bottom: none;
      }
      
      .status-label {
        color: var(--el-text-color-regular);
      }
      
      .status-value {
        font-weight: 600;
        color: var(--el-text-color-primary);
        
        &.success {
          color: var(--el-color-success);
        }
        
        &.danger {
          color: var(--el-color-danger);
        }
      }
    }
  }
  
  .recent-activity {
    padding: 20px;
    
    .activity-content {
      .activity-title {
        font-weight: 500;
        color: var(--el-text-color-primary);
        margin-bottom: 4px;
      }
      
      .activity-description {
        font-size: 14px;
        color: var(--el-text-color-regular);
      }
    }
  }
}
</style>